"""数值验收及双语言结果比较。实际调用 R，不用已有截图代替执行。"""
from pathlib import Path
import sys,os,json,subprocess,hashlib,platform,importlib.metadata
import numpy as np
import svm_lab as lab
ROOT=Path(__file__).resolve().parents[1]


def main():
    os.chdir(ROOT);(ROOT/'reports').mkdir(exist_ok=True)
    rpath=os.environ.get('QUARTO_R')
    if not rpath:
        candidates=sorted(Path('C:/Program Files/R').glob('*/bin/Rscript.exe'))
        rpath=str(candidates[-1]) if candidates else 'Rscript'
    subprocess.run([rpath,'scripts/validate-r.R'],check=True)
    rresults=json.loads((ROOT/'reports/r-results.json').read_text(encoding='utf-8'))
    rows=[]
    for name,r in zip(['iris','heart','khan'],rresults):
        _,_,_,p=lab.fit_case(name)
        match=np.array_equal(p['confusion'],r['confusion'])
        assert p['train_n']==r['train_n'] and p['test_n']==r['test_n']
        assert match, f'{name} Python/R confusion mismatch'
        assert abs(p['macro_f1']-r['macro_f1'])<1e-8
        assert abs(p['cv_macro_f1']-r['cv_macro_f1'])<1e-8
        assert p['parameters']['svm__C']==r['parameters']['C']
        if name!='khan':assert p['parameters']['svm__gamma']==r['parameters']['gamma']
        rows.append({'case':name,'python':p,'r':r,'confusion_match':bool(match)})
        print(name,'Python/R match:',match,'test accuracy=',round(p['accuracy'],4))
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data').glob('*.csv'))}
    (ROOT/'data/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    report={'date':'2026-10-02','python':sys.version,'platform':platform.platform(),
      'versions':{p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','scikit-learn','plotly']},
      'cross_language':rows,'data_sha256':manifest,
      'limitations':['固定数据划分上的实现核对，不是总体性能检验','教学SMO不含完整退化分支','模型网格为预计算，不是浏览器重训练']}
    (ROOT/'reports/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Validation report written.')


if __name__=='__main__':main()
