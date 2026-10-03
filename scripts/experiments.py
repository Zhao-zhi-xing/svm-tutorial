"""新增教学实验：固定协议，训练折内预处理；生成无服务器交互数据。"""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.datasets import make_moons,make_classification
from sklearn.model_selection import train_test_split,StratifiedKFold,GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC,LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV,calibration_curve
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,brier_score_loss,log_loss
from svm_lab import LinearSMO
ROOT=Path(__file__).resolve().parents[1]

def serial(fig):return json.loads(fig.to_json())
def split(X,y,name,save):
    tr,te=train_test_split(np.arange(len(y)),test_size=.3,stratify=y,random_state=42)
    if save:
        df=pd.DataFrame(X,columns=[f'x{i+1}' for i in range(X.shape[1])]);df['id']=np.arange(len(y));df['target']=y;df['split']='train';df.loc[te,'split']='test'
        df.to_csv(ROOT/f'data/explore-{name}.csv',index=False)
    return tr,te,{'train_ids':tr.tolist(),'test_ids':te.tolist(),'n':len(y)}

def boundary_fig(X,y,tr,te,model,title):
    padding=(X.max(axis=0)-X.min(axis=0))*.07
    ax=[np.linspace(X[:,i].min()-padding[i],X[:,i].max()+padding[i],70) for i in range(2)]
    xx,yy=np.meshgrid(*ax);z=model.decision_function(np.c_[xx.ravel(),yy.ravel()]).reshape(xx.shape)
    fig=go.Figure(go.Contour(x=ax[0],y=ax[1],z=z,colorscale=[[0,'#dceaf8'],[.5,'#ffffff'],[1,'#f9e8d4']],contours=dict(coloring='heatmap',showlines=False),line=dict(width=0),showscale=False,hovertemplate='f=%{z:.3f}<extra></extra>'))
    fig.add_trace(go.Contour(x=ax[0],y=ax[1],z=z,contours=dict(start=0,end=0,size=1,coloring='lines'),colorscale=[[0,'#17324d'],[1,'#17324d']],line=dict(color='#17324d',width=3),showscale=False,hoverinfo='skip',name='决策边界'))
    for k,color in [(0,'#245e91'),(1,'#d17b26')]:
        for ids,symbol,label in [(tr,'circle','训练'),(te,'diamond-open','测试')]:
            ix=ids[y[ids]==k];fig.add_scatter(x=X[ix,0],y=X[ix,1],mode='markers',name=f'类别{k} · {label}',marker=dict(color=color,symbol=symbol,size=7))
    fig.update_layout(title=title,height=650,xaxis_title='原始特征 x₁',yaxis_title='原始特征 x₂',legend=dict(orientation='h',y=-.15),margin=dict(l=65,r=35,t=60,b=110))
    return serial(fig)

def scaling(save):
    X,y=make_moons(n_samples=300,noise=.23,random_state=14);X[:,0]*=1000
    tr,te,meta=split(X,y,'scaling',save);states=[]
    for scaled,label in [(False,'未标准化'),(True,'训练折标准化')]:
        m=Pipeline([('scale',StandardScaler() if scaled else 'passthrough'),('svm',SVC(C=1,gamma='scale'))]).fit(X[tr],y[tr])
        pred=m.predict(X[te]);clf=m.named_steps['svm']
        states.append({'label':label,'figure':boundary_fig(X,y,tr,te,m,label),'cards':[['测试 accuracy',accuracy_score(y[te],pred)],['测试 macro-F1',f1_score(y[te],pred,average='macro')],['支持向量',int(clf.n_support_.sum())],['实际 γ',float(clf._gamma)]]})
    return {**meta,'states':states,'note':'同一原始数据、同一划分、C=1，γ均采用scale规则。该规则依输入方差自动计算，因此实际γ不同；标准化只拟合训练集。横轴被人为放大1000倍，背景显示模型分数，菱形是测试样本。固定配置演示，不是调参后的模型排名。'}

def imbalance(save):
    X,y=make_classification(n_samples=600,n_features=2,n_redundant=0,n_clusters_per_class=2,weights=[.94,.06],class_sep=.7,flip_y=.04,random_state=42)
    tr,te,meta=split(X,y,'imbalance',save);states=[]
    for weight,label in [(None,'普通 SVM'),('balanced','类别加权 SVM')]:
        m=Pipeline([('scale',StandardScaler()),('svm',SVC(C=1,gamma='scale',class_weight=weight))]).fit(X[tr],y[tr]);pred=m.predict(X[te])
        states.append({'label':label,'figure':boundary_fig(X,y,tr,te,m,label),'cards':[['测试 accuracy',accuracy_score(y[te],pred)],['少数类 precision',precision_score(y[te],pred,zero_division=0)],['少数类 recall',recall_score(y[te],pred,zero_division=0)],['少数类 F1',f1_score(y[te],pred,zero_division=0)],['训练少数类',int(y[tr].sum())],['测试少数类',int(y[te].sum())]]})
    return {**meta,'states':states,'note':'类别1为少数类。balanced权重只按训练标签计算，相当于类别相关的C_i；两种配置使用同一划分和固定参数。注意召回率与精确率的权衡，加权不保证各指标同时改善。'}

def calibration(save):
    X,y=make_classification(n_samples=1000,n_features=8,n_informative=5,n_redundant=2,weights=[.8,.2],class_sep=.9,flip_y=.04,random_state=7)
    tr,te,meta=split(X,y,'calibration',save);states=[]
    for method,label in [('heuristic','直接sigmoid分数（未校准）'),('sigmoid','交叉验证 sigmoid 校准'),('isotonic','交叉验证 isotonic 校准')]:
        base=Pipeline([('scale',StandardScaler()),('svm',SVC(C=1,gamma='scale'))])
        if method=='heuristic':
            base.fit(X[tr],y[tr]);score=base.decision_function(X[te]);p=1/(1+np.exp(-score))
        else:
            cv=StratifiedKFold(5,shuffle=True,random_state=42)
            m=CalibratedClassifierCV(base,method=method,cv=cv);m.fit(X[tr],y[tr]);p=m.predict_proba(X[te])[:,1]
        fraction,means=calibration_curve(y[te],p,n_bins=8,strategy='uniform')
        bins=np.searchsorted(np.linspace(0,1,9)[1:-1],p);counts=np.bincount(bins,minlength=8);nonempty=np.flatnonzero(counts)
        fig=go.Figure(go.Scatter(x=[0,1],y=[0,1],mode='lines',name='理想校准',line=dict(color='#8b98a5',dash='dash')))
        fig.add_scatter(x=means,y=fraction,mode='lines+markers',name=label,customdata=counts[nonempty],hovertemplate='平均预测概率=%{x:.3f}<br>实际正类比例=%{y:.3f}<br>样本数=%{customdata}<extra></extra>')
        fig.update_layout(title=label,xaxis=dict(title='分箱平均预测概率',range=[0,1]),yaxis=dict(title='分箱实际正类比例',range=[0,1]),height=600,legend=dict(orientation='h',y=-.2),margin=dict(l=70,r=30,t=60,b=110))
        states.append({'label':label,'figure':serial(fig),'brier':float(brier_score_loss(y[te],p)),'cards':[['测试 Brier（越低越好）',brier_score_loss(y[te],p)],['测试 log loss（越低越好）',log_loss(y[te],p)],['测试样本',len(te)]],'bin_counts':counts.tolist()})
    return {**meta,'states':states,'note':'直接对SVM分数取sigmoid只是未经拟合的启发式基线，不能当成已校准概率。两种校准器均在训练集内5折拟合整个Pipeline，测试集仅作最后评估。分箱样本数较少时曲线有较大波动；isotonic不保证优于sigmoid。此处比较包含校准器的交叉验证集成差异。'}

def repeated(save):
    X,y=make_classification(n_samples=240,n_features=10,n_informative=6,n_redundant=2,class_sep=1,flip_y=.06,random_state=51)
    rows=[];splits=[]
    for seed in range(8):
        tr,te=train_test_split(np.arange(len(y)),test_size=.3,stratify=y,random_state=seed)
        cv=list(StratifiedKFold(3,shuffle=True,random_state=seed).split(X[tr],y[tr]))
        split_hash=hashlib.sha256(np.array(tr,dtype='<i8').tobytes()+np.array(te,dtype='<i8').tobytes()).hexdigest()
        splits.append({'seed':seed,'train_ids':tr.tolist(),'test_ids':te.tolist(),'inner_validation_ids':[tr[v].tolist() for _,v in cv]})
        for label,model,param in [('线性 SVM',LinearSVC(dual=False,max_iter=10000),{'model__C':[.1,1,10]}),('RBF SVM',SVC(),{'model__C':[.1,1,10],'model__gamma':[.03,.3]}),('逻辑回归',LogisticRegression(max_iter=2000),{'model__C':[.1,1,10]})]:
            search=GridSearchCV(Pipeline([('scale',StandardScaler()),('model',model)]),param,cv=cv,scoring='f1_macro',n_jobs=1).fit(X[tr],y[tr])
            rows.append({'seed':seed,'model':label,'macro_f1':float(f1_score(y[te],search.predict(X[te]),average='macro')),'inner_cv':float(search.best_score_),'parameters':search.best_params_,'split_hash':split_hash,'inner_folds':3})
    if save:
        pd.DataFrame(rows).to_csv(ROOT/'data/repeated-evaluation.csv',index=False)
        (ROOT/'data/repeated-splits.json').write_text(json.dumps(splits,ensure_ascii=False),encoding='utf-8')
    states=[];fig=go.Figure()
    for label in ['线性 SVM','RBF SVM','逻辑回归']:
        selected=[r for r in rows if r['model']==label];values=[r['macro_f1'] for r in selected]
        fig.add_trace(go.Box(y=values,name=label,boxpoints='all',jitter=.15,customdata=[r['seed'] for r in selected],hovertemplate='macro-F1=%{y:.3f}<br>划分种子=%{customdata}<extra>%{fullData.name}</extra>'))
    fig.update_layout(title='8次外层划分：每次在训练集内重新选参',yaxis_title='外层测试 macro-F1',height=600)
    cards=[[label+'：均值 ± 标准差',f"{np.mean([r['macro_f1'] for r in rows if r['model']==label]):.3f} ± {np.std([r['macro_f1'] for r in rows if r['model']==label],ddof=1):.3f}"] for label in ['线性 SVM','RBF SVM','逻辑回归']]
    states.append({'label':'分数分布','figure':serial(fig),'cards':cards})
    by={(r['seed'],r['model']):r['macro_f1'] for r in rows};delta=[by[(s,'RBF SVM')]-by[(s,'线性 SVM')] for s in range(8)]
    paired=go.Figure(go.Scatter(x=list(range(8)),y=delta,mode='lines+markers',name='RBF−线性'))
    paired.add_hline(y=0,line_dash='dash',line_color='#8b98a5');paired.update_layout(title='同一划分上的配对差值',xaxis_title='外层划分种子',yaxis_title='macro-F1差值（RBF−线性）',height=600)
    states.append({'label':'配对差值','figure':serial(paired),'cards':[['平均差值',float(np.mean(delta))],['RBF分数更高的划分',f'{sum(d>0 for d in delta)} / 8'],['每次内层折数','3']]})
    return {'rows':rows,'splits':splits,'states':states,'note':'同一模拟数据上的8次分层留出，三个模型共享每次外层划分和内层3折。测试集未参与该轮选参。RBF搜索6种配置，其余3种，预算并非完全相同。不同划分样本重叠，8个分数不是独立样本；标准差描述划分敏感性，不是置信区间，也不支持显著性宣称。所有划分与逐次选参结果已保存。'}

def smo():
    X=np.array([[-2,-1],[-2,1],[-1,0],[-1.5,0],[2,-1],[2,1]],float)
    y=np.array([-1,-1,-1,1,1,1]);model=LinearSMO(C=.7,tol=1e-5,record_history=True).fit(X,y)
    assert model.converged_,model.kkt_residual_
    return {'points':X.tolist(),'labels':y.tolist(),'C':model.C,'states':model.history_,'note':'真实教学SMO的预计算更新，包含初始状态。每次成功更新一对系数，未在浏览器实时训练。中间步骤通常未满足KKT；间隙与残差应在最终收敛状态解读。所选样本的KKT状态使用数值容差。'}

def build_experiments(save=False):
    return {'scaling':scaling(save),'imbalance':imbalance(save),'calibration':calibration(save),'repeated':repeated(save),'smo':smo()}

def main():
    payload=build_experiments(save=True)
    text=json.dumps(payload,ensure_ascii=False,allow_nan=False)
    (ROOT/'assets/experiments.json').write_text(text,encoding='utf-8')
    (ROOT/'assets/experiments.js').write_text('window.SVM_EXPERIMENTS='+text+';',encoding='utf-8')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data').glob('*.csv'))}
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Prepared teaching experiments and',len(payload['smo']['states']),'SMO states.')
if __name__=='__main__':main()
