"""更新现有gh-pages。默认只列出差异；--publish 才发布。认证交给gh。"""
from pathlib import Path
import subprocess,json,hashlib,base64,sys
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
REPO='repos/Zhao-zhi-xing/svm-tutorial'
def run(args,data=None):
 p=subprocess.run(args,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT)
 if p.returncode:raise RuntimeError(p.stderr.decode('utf-8',errors='replace'))
 return p.stdout

def api(endpoint,method='GET',data=None):
 args=['gh','api',f'{REPO}/{endpoint}','--method',method]
 if data is not None:args+=['--input','-']
 return json.loads(run(args,json.dumps(data,ensure_ascii=False).encode('utf-8') if data is not None else None))

def main():
 if not (ROOT/'reports/content-validation.json').is_file():raise RuntimeError('Run content_check.py before publication')
 report=json.loads((ROOT/'reports/content-validation.json').read_text(encoding='utf-8'))
 if report['page_errors'] or report['failed_local_requests']:raise RuntimeError('Browser validation contains errors')
 parent=api('git/ref/heads/gh-pages')['object']['sha'];base=api(f'git/commits/{parent}')['tree']['sha']
 old={i['path']:i['sha'] for i in api(f'git/trees/{base}?recursive=1')['tree'] if i['type']=='blob'}
 changes=[];current=set()
 for file in sorted((ROOT/'_book').rglob('*')):
  if not file.is_file():continue
  path=file.relative_to(ROOT/'_book').as_posix();current.add(path);data=file.read_bytes()
  if file.suffix in ['.html','.css','.js','.json','.md','.txt','.csv','.ipynb']:data=data.replace(b'\r\n',b'\n')
  sha=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
  if old.get(path)!=sha:changes.append((path,data,sha))
 retired=[p for p in old if p not in current and (p in ['chapters/09-authoring.html','MIGRATION.md','使用VSCode制作与维护QuartoBook.md'] or p.startswith(('docs/','chapters/09-authoring_files/')))]
 print('Changed site files:',len(changes),'Retired author resources:',len(retired),flush=True)
 if '--publish' not in sys.argv:
  print('\n'.join('UPDATE '+p for p,_,_ in changes));print('\n'.join('REMOVE '+p for p in retired));return
 def blob(item):
  path,data,sha=item;r=api('git/blobs','POST',{'content':base64.b64encode(data).decode(),'encoding':'base64'})
  assert r['sha']==sha;return {'path':path,'mode':'100644','type':'blob','sha':sha}
 with ThreadPoolExecutor(max_workers=4) as pool:tree=list(pool.map(blob,changes))
 tree.extend({'path':p,'mode':'100644','type':'blob','sha':None} for p in retired)
 if not tree:print('Site already matches.');return
 # Protect against another publisher advancing this branch during blob upload.
 if api('git/ref/heads/gh-pages')['object']['sha']!=parent:raise RuntimeError('gh-pages advanced; rerun instead of overwriting')
 newtree=api('git/trees','POST',{'base_tree':base,'tree':tree})['sha']
 source=run(['git','rev-parse','--short','HEAD']).decode().strip()
 commit=api('git/commits','POST',{'message':f'Publish sequential self-study SVM tutorial (source {source})','tree':newtree,'parents':[parent]})['sha']
 api('git/refs/heads/gh-pages','PATCH',{'sha':commit,'force':False})
 print('Published gh-pages commit:',commit,flush=True)
if __name__=='__main__':main()
