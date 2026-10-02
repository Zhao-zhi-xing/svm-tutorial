import sys,json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


def test_shared_splits_have_no_overlap_and_cover_classes():
    for name in ['linear','moons','iris','heart','khan','multiclass']:
        data=pd.read_csv(ROOT/'data'/f'{name}.csv')
        assert data.id.is_unique
        tr=data[data.split=='train'];te=data[data.split=='test']
        assert set(tr.id).isdisjoint(te.id)
        assert set(tr.target)==set(te.target)
        assert set(tr.fold)==set(range(5))
        assert set(te.fold)=={-1}
        for f in range(5):
            assert set(tr[tr.fold==f].target)==set(tr.target)


def test_grid_extremes_match_fitted_model():
    payload=json.loads((ROOT/'assets/models.json').read_text(encoding='utf-8'))
    for name,kernel,data_name in [('linear','linear','linear'),('rbf','rbf','moons')]:
        d=payload[name];df=pd.read_csv(ROOT/'data'/f'{data_name}.csv');tr=df[df.split=='train']
        for item in [d['models'][0],d['models'][-1]]:
            X=tr[['x1','x2']].values;y=tr.target.values
            model=make_pipeline(StandardScaler(),SVC(C=item['C'],gamma=item['gamma'],kernel=kernel)).fit(X,y)
            point=np.array([[d['axis'][0],d['axis'][0]],[d['axis'][-1],d['axis'][-1]]])
            assert np.allclose(model.decision_function(point),[item['decision'][0][0],item['decision'][-1][-1]],atol=1e-4)
            assert np.allclose(X[model.named_steps['svc'].support_],item['sv'])
        assert d['best_index']==int(np.argmax([m['cv_macro_f1'] for m in d['models']]))


def test_heart_preprocessor_uses_training_data_only():
    import svm_lab as lab
    model,test,columns,result=lab.fit_case('heart')
    assert not set(['id','split','fold','target']) & set(columns)
    df=lab.load_data('heart');tr=df[df.split=='train']
    numcols=model.best_estimator_.named_steps['pre'].transformers_[0][2]
    fitted=model.best_estimator_.named_steps['pre'].named_transformers_['num'].named_steps['impute']
    assert np.allclose(fitted.statistics_,tr[numcols].median().values)
    assert sum(map(sum,result['confusion']))==len(test)
