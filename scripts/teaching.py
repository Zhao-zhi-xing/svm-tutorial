"""连续六点教学数据：原坐标、真实离散C解；与评估数据完全分开。"""
from pathlib import Path
import json
import numpy as np
from sklearn.svm import SVC
ROOT=Path(__file__).resolve().parents[1]
points=np.array([[-2,-1],[-2,1],[-1,0],[1,0],[2,-1],[2,1]],float)
labels=np.array([-1,-1,-1,1,1,1])
def projection(scale=1):
 w=scale*np.array([3.,4.]);b=-5*scale;x=np.array([1.,1.]);score=float(w@x+b)
 return dict(w=w.tolist(),b=b,score=score,norm=float(np.linalg.norm(w)),foot=(x-score*w/(w@w)).tolist(),distance=abs(score)/np.linalg.norm(w))
def hand_step():
 X=points[[2,3]];y=labels[[2,3]];K=X@X.T;E=-y
 eta=K[0,0]+K[1,1]-2*K[0,1]
 aj=np.clip(y[1]*(E[0]-E[1])/eta,0,2);ai=aj
 w=(np.array([ai,aj])*y)@X;b=-E[0]-y[0]*ai*K[0,0]-y[1]*aj*K[0,1]
 return np.array([ai,aj]),w,float(b)
def soft_model(X, y, C):
 clf=SVC(C=C,kernel='linear',tol=1e-10).fit(X,y)
 alpha=np.zeros(len(y));alpha[clf.support_]=abs(clf.dual_coef_[0]);v=clf.coef_[0];bias=float(clf.intercept_[0]);m=y*(X@v+bias);xi=np.maximum(0,1-m)
 return dict(C=C,w=v.tolist(),b=bias,alpha=alpha.tolist(),margins=m.tolist(),slack=xi.tolist(),sv=clf.support_.tolist(),errors=int(np.sum(clf.predict(X)!=y)),primal=float(.5*v@v+C*xi.sum()),dual=float(alpha.sum()-.5*v@v))

def build_teaching():
 scenarios=[]
 for name,pos,w,b,feasible in [('原始：宽间隔',1,[1,0],0,True),('移动一点：窄间隔',-.5,[4,0],3,True),('进入凸包：不可分',-1.5,None,None,False)]:
  X=points.copy();X[3,0]=pos;states=[]
  for C in [.1,1.,10.,100.]:
   states.append(soft_model(X,labels,C))
  scenarios.append(dict(label=name,points=X.tolist(),feasible=feasible,w=w,b=b,soft=states))
 extra_points=np.vstack([points,[-1.5,1.5]]);extra_labels=np.r_[labels,1]
 effect=dict(points=extra_points.tolist(),labels=extra_labels.tolist(),models=[soft_model(extra_points,extra_labels,C) for C in [.1,.3,1.,3.,10.,100.]])
 return dict(points=points.tolist(),labels=labels.tolist(),scenarios=scenarios,projection=projection(),c_effect=effect)
def main():
 d=build_teaching();text=json.dumps(d,ensure_ascii=False,allow_nan=False)
 (ROOT/'assets/teaching.json').write_text(text,encoding='utf-8')
 (ROOT/'assets/teaching-data.js').write_text('window.SVM_TEACHING='+text+';',encoding='utf-8')
 (ROOT/'data/teaching-six-points.json').write_text(text,encoding='utf-8')
 print('Prepared 12 six-point models and 6 seven-point C-effect models.')
if __name__=='__main__':main()
