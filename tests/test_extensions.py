import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import experiments as exp
import svm_lab as lab

def test_smo_history_is_feasible_and_improves_dual():
    X=np.array([[-2,-1],[-1,-2],[-1,0],[1,0],[1,2],[2,1]],float)
    y=np.array([-1,-1,-1,1,1,1])
    m=lab.LinearSMO(C=2,record_history=True).fit(X,y)
    assert len(m.history_)>2
    dual=[]
    for state in m.history_:
        a=np.array(state['alpha']);w=np.array(state['w'])
        assert np.all(a>=-1e-9) and np.all(a<=m.C+1e-9)
        assert abs(a@y)<1e-8
        assert np.allclose(w,(a*y)@X)
        dual.append(state['dual'])
    assert np.all(np.diff(dual)>=-1e-8)
    assert m.history_[-1]['gap']<1e-3

def test_extension_protocols_preserve_test_isolation():
    payload=exp.build_experiments()
    for name in ['scaling','imbalance','calibration']:
        data=payload[name]
        assert not set(data['train_ids']) & set(data['test_ids'])
        assert len(data['train_ids'])+len(data['test_ids'])==data['n']
    repeated=payload['repeated']
    assert len(repeated['rows'])==24
    for seed in range(8):
        rows=[r for r in repeated['rows'] if r['seed']==seed]
        assert len({r['split_hash'] for r in rows})==1
        assert all(r['inner_folds']==3 for r in rows)
    assert all(np.isfinite(m['brier']) for m in payload['calibration']['states'])


def test_experiment_boundary_contour_uses_one_fixed_color():
    state=exp.scaling(False)['states'][0]
    boundary=state['figure']['data'][1]
    assert boundary['colorscale']==[[0,'#17324d'],[1,'#17324d']]
