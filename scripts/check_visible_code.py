"""从头执行读者可见代码，Python章节互不共享变量，R各用新进程。"""
from pathlib import Path
import ast,contextlib,io,json,os,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 os.chdir(ROOT);rows=[];rresults={}
 for name in ['00-python-start','07-cases']:
  text=(ROOT/'chapters'/f'{name}.qmd').read_text(encoding='utf-8')
  ns={}
  with contextlib.redirect_stdout(io.StringIO()):
   for code in re.findall(r'```\{python\}\n(.*?)\n```',text,re.S):
    ast.parse(code);exec(compile(code,name,'exec'),ns)
  if name=='00-python-start':
   rows.append({'chapter':name,'case':'iris','result':ns['result']})
  else:
   from learner_experiments import train_case
   for case in ['iris','heart','khan']:
    _,_,_,saved=train_case(case);assert ns['result_'+case]==saved
    rows.append({'chapter':name,'case':case,'result':ns['result_'+case]})
  code='\n'.join(c for c in re.findall(r'```\{r\}\n(.*?)\n```',text,re.S) if '#| include: false' not in c)
  out=ROOT/'reports'/f'visible-r-{name}.json'
  expression='result_r' if name=='00-python-start' else 'list(iris=result_iris_r,heart=result_heart_r,khan=result_khan_r)'
  prefix="source('scripts/r-profile.R',encoding='UTF-8')\n.libPaths(c(normalizePath('.R-library'),.libPaths()))\nsink(file.path(tempdir(),'svm-r-output.txt'))\n"
  script=prefix+code+"\nsink()\njsonlite::write_json("+expression+", '"+out.as_posix()+"',auto_unbox=TRUE,digits=12)\n"
  rpath=os.getenv('QUARTO_R') or str(sorted(Path('C:/Program Files/R').glob('*/bin/Rscript.exe'))[-1])
  with tempfile.TemporaryDirectory(prefix='svm-visible-') as temp:
   file=Path(temp)/'check.R';file.write_text(script,encoding='utf-8')
   subprocess.run([rpath,str(file)],check=True,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  rresults[name]=json.loads(out.read_text(encoding='utf-8'))
 for row in rows:
  a=row['result'];b=rresults[row['chapter']]
  if row['chapter']=='07-cases':b=b[row['case']]
  assert a['confusion']==b['confusion']
  for metric in ['accuracy','macro_f1']:assert abs(a[metric]-b[metric])<1e-10
 report={'execution':'visible code only; independent Python namespaces and R processes','cross_language':[{'chapter':r['chapter'],'case':r['case'],'confusion':r['result']['confusion'],'accuracy':r['result']['accuracy'],'macro_f1':r['result']['macro_f1'],'match':True} for r in rows]}
 (ROOT/'reports/content-execution.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Visible Python/R code: 4 comparisons passed; no hidden setup or cross-chapter state.')
if __name__=='__main__':main()
