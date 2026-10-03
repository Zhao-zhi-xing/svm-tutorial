import sys,json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

def test_projection_scaling_and_foot():
 from teaching import projection
 for s in [.5,1,2,5]:
  result=projection(s)
  np.testing.assert_allclose(result['foot'],[.76,.68])
  assert abs(result['distance']-.4)<1e-12
  assert abs(result['score']-2*s)<1e-12

def test_hard_separability_and_dual_certificate():
 from teaching import points,labels,build_teaching
 d=build_teaching()
 for i,state in enumerate(d['scenarios']):
  X=np.array(state['points']); y=labels
  feasible=linprog(np.zeros(3),A_ub=-y[:,None]*np.c_[X,np.ones(6)],b_ub=-np.ones(6),bounds=[(None,None)]*3,method='highs').success
  assert feasible==(i<2)
  if i<2:
   m=y*(X@state['w']+state['b'])
   assert min(m)>=1-1e-10
 a=np.array([0,0,.5,.5,0,0]);S=(a*labels)@points
 assert abs(a@labels)<1e-10
 np.testing.assert_allclose(S,[1,0])
 assert abs(a.sum()-.5*S@S-.5)<1e-10

def test_soft_precomputed_models_constraints_kkt_gap():
 from teaching import build_teaching,labels
 d=build_teaching()
 for state in d['scenarios']:
  X=np.array(state['points'])
  for m in state['soft']:
   a=np.array(m['alpha']);w=np.array(m['w']);margin=np.array(m['margins']);xi=np.array(m['slack']);C=m['C']
   assert min(a)>=-1e-8 and max(a)<=C+1e-8
   assert abs(a@labels)<1e-7
   np.testing.assert_allclose((a*labels)@X,w,atol=1e-7)
   assert min(margin+xi)>=1-1e-8
   assert abs(m['primal']-m['dual'])<1e-5
   assert max(abs(a*(1-xi-margin)))<1e-5

def test_smo_hand_step_and_ranking_example():
 from teaching import hand_step
 a,w,b=hand_step()
 np.testing.assert_allclose(a,[.5,.5]);np.testing.assert_allclose(w,[1,0]);assert abs(b)<1e-12
 from sklearn.metrics import roc_auc_score,average_precision_score
 assert roc_auc_score([1,0,1,0],[3,2,1,0])==.75
 assert abs(average_precision_score([1,0,1,0],[3,2,1,0])-5/6)<1e-12
