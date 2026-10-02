"""生成共享数据、固定划分、预计算模型。运行：python scripts/prepare.py"""
from pathlib import Path
import sys, json, base64, hashlib, re, argparse
import numpy as np
import pandas as pd
from sklearn.datasets import make_moons, make_blobs, make_circles, load_iris
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_curve, precision_recall_curve, roc_auc_score, average_precision_score
from plotly.offline import get_plotlyjs
ROOT=Path(__file__).resolve().parents[1]


def save_split(name, X, y, names):
    frame=pd.DataFrame(X,columns=names)
    frame.insert(0,'id',np.arange(len(frame)))
    frame['target']=y
    train,test=train_test_split(np.arange(len(frame)),test_size=.3,stratify=y,random_state=42)
    frame['split']='train'; frame.loc[test,'split']='test'
    # CV 折按同一算法保存，使两种语言在完全相同折上选择超参数。
    frame['fold']=-1
    for fold,(_,validation) in enumerate(StratifiedKFold(5,shuffle=True,random_state=42).split(X[train] if isinstance(X,np.ndarray) else np.asarray(X)[train],np.asarray(y)[train])):
        frame.loc[train[validation],'fold']=fold
    frame.to_csv(ROOT/'data'/f'{name}.csv',index=False)
    return frame


def model_grid(df, kernel, costs, gammas):
    tr=df[df.split=='train']; te=df[df.split=='test']
    X=tr[['x1','x2']].to_numpy(); y=tr.target.to_numpy()
    axis=np.linspace(-3,3,61); xx,yy=np.meshgrid(axis,axis); xy=np.c_[xx.ravel(),yy.ravel()]
    result={'axis':axis.tolist(),'points':df[['x1','x2']].values.tolist(),'labels':df.target.tolist(),'split':df.split.tolist(),'models':[]}
    cv=[(np.flatnonzero(tr.fold.values!=f),np.flatnonzero(tr.fold.values==f)) for f in range(5)]
    for C in costs:
      for gamma in gammas:
        m=make_pipeline(StandardScaler(),SVC(C=C,gamma=gamma,kernel=kernel)).fit(X,y)
        svc=m.named_steps['svc']
        scores=[]
        for a,b in cv:
            foldmodel=make_pipeline(StandardScaler(),SVC(C=C,gamma=gamma,kernel=kernel)).fit(X[a],y[a])
            scores.append(f1_score(y[b],foldmodel.predict(X[b]),average='macro'))
        pred=m.predict(te[['x1','x2']].to_numpy())
        scaler=m.named_steps['standardscaler']
        raw_w=svc.coef_[0]/scaler.scale_ if kernel=='linear' else None
        result['models'].append({'input_margin_width':float(2/np.linalg.norm(raw_w)) if raw_w is not None else None,'C':C,'gamma':gamma,'decision':m.decision_function(xy).reshape(xx.shape).round(5).tolist(),
           'sv':X[svc.support_].tolist(),'train_errors':int(np.sum(m.predict(X)!=y)),
           'test_accuracy':float(accuracy_score(te.target,pred)),'cv_macro_f1':float(np.mean(scores))})
    result['best_index']=int(np.argmax([m['cv_macro_f1'] for m in result['models']]))
    return result


def multiclass_payload():
    X,y=make_blobs(n_samples=90,centers=[[-1.3,-.7],[1.3,-.7],[0,1.3]],cluster_std=.65,random_state=12)
    df=save_split('multiclass',X,y,['x1','x2'])
    tr=df[df.split=='train']; X=tr[['x1','x2']].values; y=tr.target.values
    ovr=OneVsRestClassifier(SVC(kernel='linear',C=1)).fit(X,y)
    pairs=[]
    for i,j in [(0,1),(0,2),(1,2)]:
        take=(y==i)|(y==j); m=SVC(kernel='linear',C=1).fit(X[take],y[take])
        # SVC 的二分类正分数指向 classes_[1]，这里是 j。
        pairs.append({'i':i,'j':j,'w':m.coef_[0].tolist(),'b':float(m.intercept_[0])})
    return {'points':df[['x1','x2']].values.tolist(),'labels':df.target.tolist(),
       'ovr':[{'w':m.coef_[0].tolist(),'b':float(m.intercept_[0])} for m in ovr.estimators_],'pairs':pairs}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--heart-source',type=Path,default=ROOT/'sources/Heart.csv')
    parser.add_argument('--extract-notebook',type=Path,default=None,help='可选：从原notebook重新提取附件')
    args=parser.parse_args()
    # 所有输入在写入任何产物前验证，缺失时不覆盖已有模型。
    heart_source=pd.read_csv(args.heart_source)
    nbpath=args.extract_notebook
    nb=json.loads(nbpath.read_text(encoding='utf-8')) if nbpath else None
    for d in ['data','assets','docs/original-attachments','reports']:(ROOT/d).mkdir(parents=True,exist_ok=True)
    X,y=make_moons(n_samples=180,noise=.22,random_state=42)
    moons=save_split('moons',X,y,['x1','x2'])
    X,y=make_blobs(n_samples=80,centers=[[-.8,-.8],[.8,.8]],cluster_std=.85,random_state=19)
    linear=save_split('linear',X,y,['x1','x2'])
    iris=load_iris(); save_split('iris',iris.data,iris.target,iris.feature_names)
    heart=heart_source.drop(columns=['Unnamed: 0'])
    y=(heart.pop('AHD')=='Yes').astype(int).values
    save_split('heart',heart.values,y,list(heart.columns))
    payload={'linear':model_grid(linear,'linear',[.03,.1,1,10,100],[1]),'rbf':model_grid(moons,'rbf',[.1,1,10,100],[.03,.1,1,10]),'multiclass':multiclass_payload()}
    X,y=make_circles(n_samples=80,noise=.035,factor=.4,random_state=42)
    payload['mapping']={'points':X.tolist(),'labels':y.tolist(),'z':np.sum(X*X,axis=1).tolist()}
    encoded=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    (ROOT/'assets/models.json').write_text(encoded,encoding='utf-8')
    (ROOT/'assets/models.js').write_text('window.SVM_MODELS='+encoded+';',encoding='utf-8')
    (ROOT/'assets/plotly.min.js').write_text(get_plotlyjs(),encoding='utf-8')
    attachments=[]
    for i,c in enumerate(nb['cells'] if nb else []):
      for name,formats in c.get('attachments',{}).items():
        mime,data=next(iter(formats.items())); path=ROOT/'docs/original-attachments'/f'cell-{i:03d}-{name}'
        path.write_bytes(base64.b64decode(data)); attachments.append({'cell':i,'file':path.name,'mime':mime})
    if nb:
        (ROOT/'docs/attachments.json').write_text(json.dumps(attachments,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/'docs/original-inventory.json').write_text(json.dumps({'source_sha256':hashlib.sha256(nbpath.read_bytes()).hexdigest(),'cells':len(nb['cells']),'attachments':len(attachments),'kernel':nb['metadata']['kernelspec'],'headings':[l for c in nb['cells'] if c['cell_type']=='markdown' for l in ''.join(c['source']).splitlines() if l.startswith('#')]},ensure_ascii=False,indent=2),encoding='utf-8')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data').glob('*.csv'))}
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    from experiments import main as prepare_experiments
    prepare_experiments()
    print('Prepared shared datasets, 21 model states, multiclass and 3D mapping.',f'Extracted {len(attachments)} attachments.' if nb else 'Original migration archive preserved.')


if __name__=='__main__':main()
