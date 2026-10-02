"""可独立运行的 Python 实验。构建从项目根目录执行，无跨章节状态。"""
from pathlib import Path
import json
import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, roc_curve, precision_recall_curve, roc_auc_score, average_precision_score

ROOT = Path(__file__).resolve().parents[1]


class LinearSMO:
    """教学版线性 C-SVM：成对更新，完整扫描；不含缓存或 shrinking。"""
    def __init__(self, C=1.0, tol=1e-4, max_iter=3000, record_history=False):
        self.C, self.tol, self.max_iter = float(C), float(tol), int(max_iter)
        self.record_history = record_history

    def fit(self, X, y):
        X, y = np.asarray(X, float), np.asarray(y, float)
        if X.ndim != 2 or len(y) != len(X) or set(np.unique(y)) != {-1., 1.}:
            raise ValueError('X 必须为二维，y 必须包含 -1 和 +1 两类')
        if self.C <= 0 or not np.isfinite(X).all():
            raise ValueError('C 必须为正，X 必须有限')
        n = len(y)
        K = X @ X.T
        a, b = np.zeros(n), 0.0
        self.history_ = []
        def snapshot(pair=None, bounds=None):
            if not self.record_history:return
            w=(a*y)@X; margins=y*(X@w+b); slack=np.maximum(0,1-margins)
            residual=np.where(a<1e-8,np.maximum(0,1-margins),np.where(a>self.C-1e-8,np.maximum(0,margins-1),abs(margins-1)))
            primal=float(.5*w@w+self.C*slack.sum());dual=float(a.sum()-.5*w@w)
            self.history_.append({'alpha':a.tolist(),'w':w.tolist(),'b':float(b),'margins':margins.tolist(),'slack':slack.tolist(),'residuals':residual.tolist(),'primal':primal,'dual':dual,'gap':primal-dual,'kkt':float(residual.max()),'equality':float(abs(a@y)),'pair':pair,'bounds':bounds})
        snapshot()
        for iteration in range(self.max_iter):
            changed = 0
            for i in range(n):
                E = K @ (a*y) + b - y
                r = E[i]*y[i]
                if not ((r < -self.tol and a[i] < self.C-1e-9) or (r > self.tol and a[i] > 1e-9)):
                    continue
                # 最大误差差值优先；若该对受盒约束阻塞，尝试其他 j。
                for j in np.argsort(-abs(E[i]-E)):
                    if i == j:
                        continue
                    ai, aj = a[i], a[j]
                    if y[i] != y[j]:
                        L, H = max(0, aj-ai), min(self.C, self.C+aj-ai)
                    else:
                        L, H = max(0, ai+aj-self.C), min(self.C, ai+aj)
                    eta = K[i,i]+K[j,j]-2*K[i,j]
                    if H-L < 1e-12 or eta <= 1e-12:
                        continue
                    newj = np.clip(aj + y[j]*(E[i]-E[j])/eta, L, H)
                    if abs(newj-aj) < 1e-10:
                        continue
                    newi = ai + y[i]*y[j]*(aj-newj)
                    b1 = b-E[i]-y[i]*(newi-ai)*K[i,i]-y[j]*(newj-aj)*K[i,j]
                    b2 = b-E[j]-y[i]*(newi-ai)*K[i,j]-y[j]*(newj-aj)*K[j,j]
                    b = b1 if 1e-9 < newi < self.C-1e-9 else b2 if 1e-9 < newj < self.C-1e-9 else (b1+b2)/2
                    a[i], a[j] = newi, newj
                    snapshot([int(i),int(j)],{'L':float(L),'H':float(H),'eta':float(eta)})
                    changed += 1
                    break
            if changed == 0:
                break
        self.alpha_, self.coef_, self.intercept_ = a, (a*y) @ X, b
        self.n_iter_ = iteration+1
        margins = y*self.decision_function(X)
        residuals = np.where(a < 1e-8, np.maximum(0,1-margins),
                    np.where(a > self.C-1e-8,np.maximum(0,margins-1),abs(margins-1)))
        self.kkt_residual_ = float(residuals.max())
        self.converged_ = self.kkt_residual_ <= max(10*self.tol,1e-3)
        self.support_ = np.flatnonzero(a>1e-8)
        return self

    def decision_function(self, X):
        return np.asarray(X) @ self.coef_ + self.intercept_

    def predict(self, X):
        return np.where(self.decision_function(X)>=0,1,-1)


def load_data(name):
    return pd.read_csv(ROOT / 'data' / (name+'.csv'))


def fit_case(name='iris'):
    """训练折内预处理、分层 5 折选参，测试集仅用于最后评估。"""
    df = load_data(name)
    train, test = df[df.split=='train'], df[df.split=='test']
    columns = [c for c in df if c not in ['id','split','target','fold']]
    X, y = train[columns], train.target
    numeric = X.select_dtypes(include='number').columns.tolist()
    categorical = [c for c in columns if c not in numeric]
    pre = ColumnTransformer([
        ('num',Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),numeric),
        ('cat',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),categorical)])
    pipeline = Pipeline([('pre',pre),('svm',SVC())])
    cv = [(np.flatnonzero(train.fold.values!=f),np.flatnonzero(train.fold.values==f)) for f in range(5)]
    # Khan 为 p >> n，不使用 RBF 大网格。
    param = {'svm__C':[.1,1,10], 'svm__kernel':['linear']} if name=='khan' else {'svm__C':[.1,1,10],'svm__gamma':[.01,.1,1],'svm__kernel':['rbf']}
    search = GridSearchCV(pipeline,param,cv=cv,scoring='f1_macro',n_jobs=1).fit(X,y)
    pred = search.predict(test[columns])
    labels = sorted(df.target.unique().tolist())
    result = {'case':name,'language':'Python','train_n':len(train),'test_n':len(test),
        'parameters':search.best_params_,'cv_macro_f1':float(search.best_score_),
        'accuracy':float(accuracy_score(test.target,pred)), 'macro_f1':float(f1_score(test.target,pred,average='macro')),
        'labels':labels,'confusion':confusion_matrix(test.target,pred,labels=labels).tolist(),
        'support_vectors':int(search.best_estimator_.named_steps['svm'].n_support_.sum())}
    return search, test, columns, result


def case_plot(name='iris'):
    _,_,_,r = fit_case(name)
    fig = go.Figure(go.Heatmap(z=r['confusion'],x=[str(x) for x in r['labels']],y=[str(x) for x in r['labels']],colorscale='Blues',text=r['confusion'],texttemplate='%{text}',hovertemplate='真实=%{y}<br>预测=%{x}<br>数量=%{z}<extra></extra>'))
    fig.update_layout(title=f"{name} · Python 测试集：accuracy={r['accuracy']:.3f}, macro-F1={r['macro_f1']:.3f}",xaxis_title='预测类别',yaxis_title='真实类别',height=560)
    return fig, r


def figure_html(fig, identifier):
    """以本地共享 Plotly.js 渲染，避免每个图重复加载大型脚本。"""
    payload = fig.to_json().replace('</','<\\/')
    return f'<div class="plotly-output" id="{html.escape(identifier)}" data-plotly-source="{html.escape(identifier)}-json"></div><script type="application/json" id="{html.escape(identifier)}-json">{payload}</script>'


def loss_plot():
    z=np.linspace(-3,4,141)
    fig=go.Figure()
    for name,value in [('hinge',np.maximum(0,1-z)),('logistic',np.logaddexp(0,-z))]:
        fig.add_scatter(x=z,y=value,name=name,mode='lines',line=dict(width=3))
    # Explicit duplicated x=0 avoids a diagonal interpolation across the jump.
    fig.add_scatter(x=[-3,0,0,4],y=[1,1,0,0],name='0–1',mode='lines',line=dict(shape='hv',width=3,color='#ae3953'))
    fig.add_scatter(x=[0],y=[1],name='零分数按错误处理',mode='markers',marker=dict(color='#ae3953',size=9),showlegend=False)
    fig.add_scatter(x=[0],y=[0],name='右侧极限',mode='markers',marker=dict(color='#ae3953',size=9,symbol='circle-open'),showlegend=False)
    fig.update_layout(xaxis_title='带符号分数 y f(x)',yaxis_title='损失',title='损失函数比较：0–1 在零处分段跳变',height=560)
    return fig


def evaluation_plot(name='heart'):
    model,test,columns,result=fit_case(name)
    score=model.decision_function(test[columns])
    fpr,tpr,_=roc_curve(test.target,score)
    precision,recall,_=precision_recall_curve(test.target,score)
    auc=roc_auc_score(test.target,score); ap=average_precision_score(test.target,score)
    fig=go.Figure()
    fig.add_scatter(x=fpr,y=tpr,name=f'ROC · AUC={auc:.3f}',mode='lines',hovertemplate='FPR=%{x:.3f}<br>TPR=%{y:.3f}<extra></extra>')
    fig.add_scatter(x=recall,y=precision,name=f'PR · AP={ap:.3f}',mode='lines',visible='legendonly',hovertemplate='Recall=%{x:.3f}<br>Precision=%{y:.3f}<extra></extra>')
    fig.update_layout(title='Heart · Python：点击图例切换 ROC/PR',xaxis_title='FPR（ROC）/ Recall（PR）',yaxis_title='TPR（ROC）/ Precision（PR）',height=560,xaxis_range=[0,1],yaxis_range=[0,1.02])
    return fig,{'auc':float(auc),'average_precision':float(ap)}


def _contour_paths(axis,z,level):
    segments=[]
    for j in range(len(axis)-1):
        for i in range(len(axis)-1):
            points=np.array([[axis[i],axis[j]],[axis[i+1],axis[j]],[axis[i+1],axis[j+1]],[axis[i],axis[j+1]]])
            values=np.array([z[j,i],z[j,i+1],z[j+1,i+1],z[j+1,i]])
            cross=[]
            for e in range(4):
                k=(e+1)%4
                if (values[e]>level)!=(values[k]>level):
                    t=(level-values[e])/(values[k]-values[e]);cross.append(points[e]+t*(points[k]-points[e]))
            pairs=([(0,1),(2,3)] if (values.mean()>level)==(values[0]>level) else [(0,3),(1,2)]) if len(cross)==4 else [(0,1)] if len(cross)==2 else []
            for a,b in pairs:segments.append((cross[a],cross[b]))
    # Join neighboring cell segments so dash patterns do not restart every cell.
    adjacency={}
    key=lambda p:tuple(np.round(p,9))
    for index,(a,b) in enumerate(segments):
        adjacency.setdefault(key(a),[]).append(index)
        adjacency.setdefault(key(b),[]).append(index)
    unused=set(range(len(segments)));joined=[]
    while unused:
        index=unused.pop();a,b=segments[index];path=[a,b]
        for front in [False,True]:
            while True:
                endpoint=path[0] if front else path[-1]
                matches=[i for i in adjacency[key(endpoint)] if i in unused]
                if not matches:break
                i=matches[0];unused.remove(i);a,b=segments[i]
                other=b if key(a)==key(endpoint) else a
                if front:path.insert(0,other)
                else:path.append(other)
        joined.extend(path);joined.append([np.nan,np.nan])
    return [np.asarray(joined)] if joined else []


def binary_plot(name='linear',kernel='linear',C=1,gamma=1):
    df=load_data(name);tr=df[df.split=='train'];X=tr[['x1','x2']]
    model=Pipeline([('scale',StandardScaler()),('svm',SVC(kernel=kernel,C=C,gamma=gamma))]).fit(X,tr.target)
    axis=np.linspace(-3,3,61);xx,yy=np.meshgrid(axis,axis)
    query=pd.DataFrame(np.c_[xx.ravel(),yy.ravel()],columns=['x1','x2'])
    score=model.decision_function(query).reshape(xx.shape)
    fig=go.Figure(go.Contour(x=axis,y=axis,z=score,colorscale=[[0,'#dceaf8'],[.5,'#ffffff'],[1,'#f9e8d4']],showscale=False,contours={'coloring':'heatmap','showlines':False},line={'width':0},opacity=.55))
    for level,label,color,dash,width in [(0,'决策边界 f(x)=0','#17324d','solid',3.5), (1,'正侧间隔线 f(x)=+1','#137d80','dash',2), (-1,'负侧间隔线 f(x)=−1','#b96a15','dash',2)]:
        # Extract contour paths once with marching squares; use Scatter for dash support.
        for index,path in enumerate(_contour_paths(axis,score,level)):
            fig.add_scatter(x=path[:,0],y=path[:,1],name=label,legendgroup=label,showlegend=index==0,mode='lines',line=dict(color=color,dash=dash,width=width),hovertemplate=label+'<extra></extra>')
    for k in [0,1]:
        p=df[df.target==k]
        fig.add_scatter(x=p.x1,y=p.x2,mode='markers',name=f'类别 {k}',marker={'color':['#245e91','#d17b26'][k],'symbol':['circle' if s=='train' else 'diamond-open' for s in p.split]})
    support=X.iloc[model.named_steps['svm'].support_]
    fig.add_scatter(x=support.x1,y=support.x2,mode='markers',name='支持向量',marker={'symbol':'circle-open','size':13,'color':'#17324d'})
    fig.update_layout(title=f'Python · {kernel}, C={C}, γ={gamma}',height=860,xaxis_title='x₁',yaxis_title='x₂',yaxis_scaleanchor='x')
    return fig


def approximate_kernel_experiment():
    from sklearn.kernel_approximation import Nystroem
    from sklearn.svm import LinearSVC
    df=load_data('moons'); train=df[df.split=='train']; test=df[df.split=='test']
    X=train[['x1','x2']]; y=train.target
    rows=[]
    for m in [10,30,60,100]:
        model=Pipeline([('scale',StandardScaler()),('map',Nystroem(gamma=1,n_components=m,random_state=42)),('svm',LinearSVC(C=1,dual=False))]).fit(X,y)
        rows.append({'components':m,'accuracy':accuracy_score(test.target,model.predict(test[['x1','x2']]))})
    fig=go.Figure(go.Scatter(x=[r['components'] for r in rows],y=[r['accuracy'] for r in rows],mode='lines+markers'))
    fig.update_layout(title='Nyström + LinearSVC：固定配置的教学实验（非调参结论）',xaxis_title='近似特征数',yaxis_title='测试 accuracy',height=560)
    return fig


def compare_models():
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neural_network import MLPClassifier
    df=load_data('iris'); tr=df[df.split=='train']; te=df[df.split=='test']
    features=[c for c in df if c not in ['id','split','target','fold']]
    models={
      'RBF SVM':(SVC(),{'model__C':[.1,1,10],'model__gamma':[.01,.1,1]}),
      '逻辑回归':(LogisticRegression(max_iter=2000),{'model__C':[.1,1,10]}),
      '随机森林':(RandomForestClassifier(n_estimators=150,random_state=42),{'model__max_depth':[2,4,None]}),
      '小型 MLP':(MLPClassifier(random_state=42,max_iter=3000,solver='lbfgs'),{'model__hidden_layer_sizes':[(8,),(16,)],'model__alpha':[.01,1]})}
    rows=[]
    for name,(model,params) in models.items():
        pipeline=Pipeline([('scale',StandardScaler()),('model',model)])
        folds=[(np.flatnonzero(tr.fold.values!=f),np.flatnonzero(tr.fold.values==f)) for f in range(5)]
        fit=GridSearchCV(pipeline,params,scoring='f1_macro',cv=folds).fit(tr[features],tr.target)
        rows.append({'model':name,'cv_macro_f1':fit.best_score_,'test_macro_f1':f1_score(te.target,fit.predict(te[features]),average='macro'),'params':str(fit.best_params_)})
    fig=go.Figure(go.Bar(x=[r['model'] for r in rows],y=[r['test_macro_f1'] for r in rows],customdata=[r['params'] for r in rows],hovertemplate='%{x}<br>macro-F1=%{y:.3f}<br>%{customdata}<extra></extra>'))
    fig.update_layout(title='Iris：相同划分、相同 CV 折的有限网格比较',yaxis_title='测试 macro-F1',height=560)
    return fig,rows
