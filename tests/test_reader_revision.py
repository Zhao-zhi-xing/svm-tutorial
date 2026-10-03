import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))

def test_c_effect_has_visible_tradeoff_and_valid_certificates():
 from teaching import build_teaching
 d=build_teaching()['c_effect']; X=np.array(d['points']);y=np.array(d['labels'])
 states=d['models'];assert len(states)==6
 assert states[0]['errors']==1 and states[-1]['errors']==0
 assert np.linalg.norm(np.array(states[0]['w'])-states[-1]['w'])>1
 assert states[0]['slack'][-1]>1 and states[-1]['slack'][-1]<1e-6
 assert np.all(np.diff([sum(m['slack']) for m in states])<=1e-6)
 assert np.all(np.diff([np.linalg.norm(m['w']) for m in states])>=-1e-6)
 for m in states:
  a=np.array(m['alpha']);w=np.array(m['w']);xi=np.array(m['slack']);margin=np.array(m['margins'])
  assert abs(a@y)<1e-7 and np.all(a>=-1e-8) and np.all(a<=m['C']+1e-8)
  np.testing.assert_allclose((a*y)@X,w,atol=1e-7)
  assert abs(m['primal']-m['dual'])<1e-5
  assert np.max(abs(a*(1-xi-margin)))<1e-5

def test_fbeta_and_multiclass_hand_calculations():
 from sklearn.metrics import f1_score,fbeta_score
 truth=[1]*4+[0]*6;pred=[1]*3+[0]+[1]*2+[0]*4
 assert abs(f1_score(truth,pred)-2/3)<1e-12
 assert abs(fbeta_score(truth,pred,beta=.5)-.625)<1e-12
 assert abs(fbeta_score(truth,pred,beta=2)-5/7)<1e-12
 cm=np.array([[8,1,1],[2,3,0],[1,0,1]])
 t=[];p=[]
 for i in range(3):
  for j in range(3):t.extend([i]*cm[i,j]);p.extend([j]*cm[i,j])
 fs=np.array([16/21,2/3,1/2]);support=np.array([10,5,2])
 assert abs(f1_score(t,p,average='macro')-fs.mean())<1e-12
 assert abs(f1_score(t,p,average='weighted')-support@fs/17)<1e-12
 assert abs(f1_score(t,p,average='micro')-12/17)<1e-12


def test_scaling_comparison_keeps_same_rbf_configuration():
 from experiments import scaling
 result=scaling(False);a,b=[s['model'] for s in result['states']]
 assert a['kernel']==b['kernel']=='rbf' and a['C']==b['C']==1
 assert a['gamma_rule']==b['gamma_rule']=='scale'
 assert a['gamma']<1e-5 and abs(b['gamma']-.5)<1e-12
 assert result['training_original_std'][0]/result['training_original_std'][1]>1000
