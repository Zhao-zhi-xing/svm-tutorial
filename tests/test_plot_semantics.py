import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import svm_lab as lab

def test_zero_one_loss_has_jump_exactly_at_zero():
    trace=next(t for t in lab.loss_plot().data if t.name=='0–1')
    x=np.asarray(trace.x,dtype=float); y=np.asarray(trace.y,dtype=float)
    jump=np.flatnonzero(np.diff(y)!=0)
    assert len(jump)==1
    assert x[jump[0]]==0 and x[jump[0]+1]==0
    assert trace.line.shape=='hv'
    assert np.all(y[x<0]==1) and np.all(y[x>0]==0)

def test_binary_boundaries_are_named_separate_traces():
    fig=lab.binary_plot()
    boundary=next((t for t in fig.data if t.name=='决策边界 f(x)=0'),None)
    margins=[t for t in fig.data if t.name and '间隔线' in t.name]
    assert boundary is not None and len(margins)==2
    assert boundary.line.width>max(t.line.width for t in margins)
    assert len({boundary.line.color,*[t.line.color for t in margins]})==3
    assert all(t.line.dash=='dash' for t in margins)

    for trace in margins:
        x=np.asarray(trace.x,dtype=float)
        # Complete paths keep dash patterns continuous across grid cells.
        assert np.count_nonzero(np.isnan(x)) <= 3
