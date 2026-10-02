import sys
from pathlib import Path
import numpy as np
from sklearn.svm import SVC
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


def test_smo_constraints_and_libsvm_agreement():
    from svm_lab import LinearSMO
    X = np.array([[-2,-1],[-1,-2],[-1,0],[1,0],[1,2],[2,1]], dtype=float)
    y = np.array([-1,-1,-1,1,1,1])
    model = LinearSMO(C=2, tol=1e-5).fit(X, y)
    assert np.min(model.alpha_) >= -1e-8
    assert np.max(model.alpha_) <= 2+1e-8
    assert abs(model.alpha_ @ y) < 1e-7
    assert model.kkt_residual_ < 1e-3
    reference = SVC(C=2, kernel='linear', tol=1e-7).fit(X,y)
    grid = np.array([[a,b] for a in np.linspace(-2,2,17) for b in np.linspace(-2,2,13)])
    away = abs(reference.decision_function(grid)) > 1e-3
    assert np.mean(model.predict(grid[away]) == reference.predict(grid[away])) > .99


def test_smo_nonseparable_and_invalid_labels():
    from svm_lab import LinearSMO
    import pytest
    rng = np.random.default_rng(17)
    X = rng.normal(size=(30,2))
    y = np.where(X[:,0]+.3*X[:,1]>0,1,-1)
    y[0] *= -1
    model = LinearSMO(C=.7, tol=1e-4).fit(X,y)
    assert model.kkt_residual_ < .01
    assert abs(model.alpha_ @ y) < 1e-7
    assert np.mean(model.predict(X)==SVC(C=.7,kernel='linear').fit(X,y).predict(X)) > .95
    with pytest.raises(ValueError):
        LinearSMO().fit(X, np.zeros(30))
