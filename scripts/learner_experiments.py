import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

def train_case(name='iris'):

    df = pd.read_csv('data/' + name + '.csv')
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

