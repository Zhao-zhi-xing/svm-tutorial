"""自学内容重构验收：链接、资源隔离、真实交互状态与实践输出。"""
from pathlib import Path
import json,functools,http.server,threading,os,re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from browser_check import link_check
ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/'_book'
def main():
 pages=link_check()
 assert pages==15,pages
 assert not (BOOK/'chapters/09-authoring.html').exists()
 for file in ['MIGRATION.md','使用VSCode制作与维护QuartoBook.md']:
  assert not (BOOK/file).exists(),file
 assert not (BOOK/'docs').exists()
 alltext='\n'.join(BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser').get_text() for p in BOOK.glob('chapters/*.html'))
 for phrase in ['这里恢复原笔记','新版直接','旧代码','方向错误已纠正']:
  assert phrase not in alltext,phrase
 for path in BOOK.glob('chapters/*.html'):
  visible=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser').select_one('main')
  for node in visible.select('pre,code,script,style'):node.decompose()
  assert not re.search(r'Figure\s*\(\s*\{',visible.get_text()),path.name
  assert not re.search(r'GridSearchCV\(cv=',visible.get_text()),path.name
  assert 'cdn.plot.ly' not in path.read_text(encoding='utf-8'),path.name
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 base=os.getenv('SVM_CHECK_URL',f'http://127.0.0.1:{server.server_port}/_book/')
 checks=[];errors=[];bad_requests=[]
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--enable-unsafe-swiftshader'])
  page=browser.new_page(viewport={'width':1440,'height':1000})
  page.context.grant_permissions(['clipboard-read','clipboard-write'])
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('response',lambda r:bad_requests.append(r.url) if r.status>=400 and r.url.startswith(base) else None)
  def visit(name):
   page.goto(base+name,wait_until='domcontentloaded');page.wait_for_timeout(800)
   page.wait_for_function("typeof Plotly !== 'undefined'")
   if page.locator('.math').count():
    page.wait_for_function("!!window.MathJax?.startup?.promise")
    page.evaluate('async()=>await MathJax.startup.promise')
  for path in sorted(BOOK.glob('chapters/*.html')):
   visit('chapters/'+path.name)
   expected=page.locator('[data-teaching], [data-svm-lab], [data-experiment], [data-plotly-source]').count()
   page.wait_for_function("()=>[...document.querySelectorAll('[data-teaching], [data-svm-lab], [data-experiment]')].every(e=>e.querySelector('.js-plotly-plot'))")
   assert not page.locator('mjx-merror, mjx-mtext[data-mjx-error]').count(), (path.name, page.locator('mjx-merror, mjx-mtext[data-mjx-error]').evaluate_all('(nodes)=>nodes.map(e=>e.outerHTML)'))
   assert page.locator('.chapter-intro').count()==1,path.name
   checks.append(path.name+' loaded; '+str(expected)+' figure containers')
  visit('index.html')
  assert not page.locator('[data-teaching], [data-svm-lab]').count()
  assert page.locator('.tutorial-start').get_attribute('href').endswith('01-geometry.html')
  assert not page.locator('h2 .header-section-number').count()
  assert page.locator('#quarto-sidebar .chapter-number').first.inner_text()=='1'
  assert page.locator('#quarto-sidebar .sidebar-link').nth(1).get_attribute('href').endswith('01-geometry.html')
  for name in ['chapters/01-geometry.html','chapters/03-duality-smo.html','chapters/07-cases.html']:
   visit(name)
   for width in [1280,1440,1920,2560]:
    page.set_viewport_size({'width':width,'height':1000})
    page.wait_for_function('document.documentElement.scrollWidth<=innerWidth+1',timeout=5000)
    measured=page.evaluate("()=>{const r=document.querySelector('main').getBoundingClientRect();return {center:r.x+r.width/2,overflow:document.documentElement.scrollWidth};}")
    assert abs(measured['center']-width/2)<2,measured
    assert measured['overflow']<=width+1,(name,width,measured)
    nav=page.locator('#quarto-sidebar').evaluate("e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,y:r.y,bottom:r.bottom,radius:s.borderRadius,shadow:s.boxShadow};}")
    assert abs(nav['x']-16)<1 and abs(nav['bottom']-984)<1,nav
    assert nav['radius']=='20px' and nav['shadow']!='none',nav
  checks.append('15 pages; author materials excluded; 4 desktop widths centered with no document overflow')
  page.set_viewport_size({'width':1440,'height':1000});visit('chapters/01-geometry.html')
  table=page.locator('main table').first
  style=table.evaluate("e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {width:r.width,top:s.borderTopWidth,bottom:s.borderBottomWidth,cell:getComputedStyle(e.querySelector('td')).textAlign};}")
  assert style['width']<=800 and style['top']=='2px' and style['bottom']=='2px' and style['cell']=='center',style
  page.screenshot(path=str(ROOT/'reports/reading-warm-table.png'))
  lab=page.locator('[data-teaching=geometry]');lab.wait_for();page.wait_for_selector('[data-teaching=geometry] .js-plotly-plot')
  assert lab.locator('.lab-plot').evaluate('e=>e._fullLayout.xaxis._length')>600
  for angle in ['-80','0','80']:
   lab.locator('input[name=angle]').fill(angle);lab.locator('input[name=angle]').dispatch_event('input')
  for bias in ['-2','0','2']:
   lab.locator('input[name=bias]').fill(bias);lab.locator('input[name=bias]').dispatch_event('input')
  lab.locator('button').click()
  for i,scale in enumerate([.5,1,2,5]):
   lab.locator('select[name=scale]').select_option(str(i))
   assert float(lab.get_attribute('data-scale'))==scale
   distance=lab.locator('.stat-card').filter(has=page.get_by_text('无符号距离',exact=True)).locator('.stat-value').inner_text()
   assert distance=='1.000',distance
  lab.locator('select[name=band]').select_option('1');lab.locator('button').click()
  assert lab.locator('input[name=angle]').input_value()=='0'
  checks.append('geometry endpoints, scaling invariance, reference-line stage, reset')
  visit('chapters/01-hard-margin.html')
  lab=page.locator('[data-teaching=hard]')
  for i in range(3):
   lab.locator('select[name=scenario]').select_option(str(i))
   assert lab.get_attribute('data-current-scenario')==str(i)
  assert '不存在' in lab.inner_text()
  projection=page.locator('[data-teaching=projection]')
  for i in range(4):
   projection.locator('select[name=scale]').select_option(str(i))
   factor=[.5,1,2,5][i]
   assert float(projection.get_attribute('data-current-scale'))==factor
   assert f'f(x)={2*factor:.3f}' in projection.locator('.lab-feedback').inner_text()
   assert f'‖w‖={5*factor:.3f}' in projection.locator('.lab-feedback').inner_text()
   assert '距离仍为0.400' in projection.locator('.lab-feedback').inner_text()
  projection.locator('button').click();assert projection.get_attribute('data-current-scale')=='1'
  annotations=projection.locator('.annotation-text').evaluate_all("nodes=>nodes.filter(n=>n.textContent.trim()).map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom};})")
  assert len(annotations)==4,annotations
  for i,a in enumerate(annotations):
   for b in annotations[i+1:]:assert a['right']<=b['x'] or b['right']<=a['x'] or a['bottom']<=b['y'] or b['bottom']<=a['y'],annotations
  projection.screenshot(path=str(ROOT/'reports/reading-projection-labels.png'))
  checks.append('hard separability states, projection scales and non-overlapping labels')
  visit('chapters/02-soft-margin.html');lab=page.locator('[data-teaching=soft]')
  data=json.loads((ROOT/'assets/teaching.json').read_text(encoding='utf-8'))
  effect=page.locator('[data-teaching=c-effect]')
  for i,model in enumerate(data['c_effect']['models']):
   effect.locator('select[name=C]').select_option(str(i))
   assert float(effect.get_attribute('data-current-c'))==model['C']
   assert effect.locator('.lab-table tr').count()==8
   shown=effect.locator('.lab-plot').evaluate('e=>e.data.find(t=>t.name==="决策边界 f=0")')
   for x,y in zip(shown['x'],shown['y']):assert abs(model['w'][0]*x+model['w'][1]*y+model['b'])<1e-6
  effect.locator('button').click();assert effect.get_attribute('data-current-c')=='0.1'
  effect.screenshot(path=str(ROOT/'reports/reading-c-effect.png'))
  checks.append('all 6 seven-point C states, fitted boundaries, point table and reset')
  for i,state in enumerate(data['scenarios']):
   lab.locator('select[name=scenario]').select_option(str(i))
   for j,model in enumerate(state['soft']):
    lab.locator('select[name=C]').select_option(str(j))
    assert float(lab.get_attribute('data-current-c'))==model['C']
    assert lab.locator('.lab-table tr').count()==7
  loss=page.locator('[data-teaching=loss]')
  for v in ['-3','0','1','4']:
   loss.locator('input[name=margin]').fill(v);loss.locator('input[name=margin]').dispatch_event('input')
  traces=loss.locator('.lab-plot').evaluate('e=>e.data.slice(0,2).map(t=>({x:t.x,y:t.y}))')
  assert traces==[{'x':[-3,0],'y':[1,1]},{'x':[0,4],'y':[0,0]}]
  checks.append('all 12 soft states and table; discontinuous 0–1 endpoints')
  visit('chapters/04-kernels.html');lab=page.locator('[data-teaching=mapping]')
  lab.locator('select[name=view]').select_option('1');page.wait_for_timeout(300)
  assert lab.locator('.lab-plot').evaluate('e=>e.data[0].type')=='scatter3d'
  lab.locator('.lab-plot').evaluate("e=>Plotly.relayout(e,{'scene.camera.eye':{x:2,y:0,z:1}})")
  lab.locator('button').click();assert lab.get_attribute('data-view')=='0'
  rbf=page.locator('[data-svm-lab=rbf]');models=json.loads((ROOT/'assets/models.json').read_text(encoding='utf-8'))['rbf']
  for m in models['models']:
   rbf.locator('select[name=C]').select_option(str(m['C']));rbf.locator('select[name=gamma]').select_option(str(m['gamma']))
   assert int(rbf.get_attribute('data-current-sv'))==len(m['sv'])
  checks.append('paired 2D/3D mapping, rotation/reset; all original RBF states')
  visit('chapters/03-smo.html');lab=page.locator('[data-experiment=smo]')
  assert lab.get_attribute('data-current-step')=='0'
  steps=json.loads((ROOT/'assets/experiments.json').read_text(encoding='utf-8'))['smo']['states']
  for i in range(len(steps)):
   lab.locator('input[name=smo-step]').fill(str(i));lab.locator('input[name=smo-step]').dispatch_event('input')
   assert lab.get_attribute('data-current-step')==str(i)
  lab.locator('button').click();assert lab.get_attribute('data-current-step')=='0'
  checks.append('every actual six-point SMO update and reset')
  visit('chapters/05-multiclass.html');lab=page.locator('[data-svm-lab=multiclass]')
  for option in lab.locator('select[name=strategy] option').all():
   lab.locator('select[name=strategy]').select_option(option.get_attribute('value'))
   assert lab.get_attribute('data-current-strategy')==option.inner_text()
  checks.append('multiclass strategy switching')
  visit('chapters/00-python-start.html')
  for lang in ['R','Python','R','Python']:
   page.get_by_role('tab',name=lang,exact=True).last.click();page.wait_for_timeout(150)
   active=page.locator('.tab-pane.active .js-plotly-plot')
   assert active.count()>=1 and active.first.bounding_box()['width']>450
  copy=page.locator('.code-copy-button:visible').first;copy.click();page.wait_for_timeout(150)
  assert page.evaluate('navigator.clipboard.readText()')
  checks.append('Python/R practice outputs, resize and code copy')
  visit('chapters/07-cases.html');details=page.locator('details.result-details');assert details.count()==4
  details.first.locator('summary').focus();page.keyboard.press('Enter');assert details.first.evaluate('e=>e.open')
  for name in ['iris','heart','khan']:
   assert page.locator('#'+name+'-python').count()==1
   assert page.locator('#'+name+'-r').count()==1
  assert page.locator('#model-comparison').evaluate('e=>e._fullLayout.height')==410
  checks.append('all three dual-language case outputs, folded records and compact comparison')
  for old,target in [('chapters/01-geometry.html#eq-hard-primal','01-hard-margin.html'),('chapters/03-duality-smo.html#eq-general-kkt','03-optimization.html'),('chapters/04-kernels.html#展开-rbf看到无限维映射','04-rkhs.html')]:
   visit(old);page.wait_for_url('**/'+target+'**');assert target in page.url
  checks.append('moved equation and section anchor compatibility')
  visit('chapters/06-workflow.html');scaling=page.locator('[data-experiment=scaling]')
  scale_data=json.loads((ROOT/'assets/experiments.json').read_text(encoding='utf-8'))['scaling']
  for i,state in enumerate(scale_data['states']):
   scaling.locator('select').select_option(str(i))
   assert state['model']['kernel']=='rbf' and state['model']['C']==1
   cards=scaling.locator('.stat-card').all_text_contents()
   assert any('核函数' in c and 'RBF' in c for c in cards)
   assert any('实际 γ' in c and ('e-6' in c if i==0 else '0.5000' in c) for c in cards),cards
  checks.append('same RBF/C standardization comparison; gamma displayed without rounding to zero')
  visit('chapters/01-geometry.html')
  next_link=page.locator('.nav-page-next .pagination-link');previous_link=page.locator('.nav-page-previous .pagination-link')
  assert '下一章' in next_link.inner_text() and '上一章' in previous_link.inner_text()
  assert next_link.bounding_box()['height']>=96
  next_link.focus();assert next_link.evaluate('e=>getComputedStyle(e).outlineWidth')=='3px'
  page.locator('.page-navigation').screenshot(path=str(ROOT/'reports/reading-pagination-cards.png'))
  next_link.click();page.wait_for_url('**/01-hard-margin.html')
  page.locator('.nav-page-previous .pagination-link').click();page.wait_for_url('**/01-geometry.html')
  checks.append('visible chapter cards, keyboard focus and real forward/back navigation')
  visit('references.html')
  assert '文献按正文首次引用顺序编号' not in page.locator('main').inner_text()
  numbers=page.locator('#refs .csl-left-margin').all_text_contents()
  assert len(numbers)>10 and all(str(i+1) in v for i,v in enumerate(numbers)),numbers
  assert '吴恩达' in page.locator('#refs').inner_text()
  page.screenshot(path=str(ROOT/'reports/reading-numbered-references.png'))
  checks.append('numeric references, explicit CS229 author, centered three-rule tables, floating sidebar')
  # Existing native search still finds a newly split chapter.
  visit('index.html');page.locator('#quarto-search button').first.click()
  search=page.locator('.aa-Input');search.fill('互补松弛');page.wait_for_timeout(650)
  assert page.locator('.aa-Item').count()>0
  page.keyboard.press('Escape');checks.append('native search finds rewritten material')
  for name in ['01-hard-margin','03-optimization','07-cases']:
   visit('chapters/'+name+'.html');page.screenshot(path=str(ROOT/'reports'/('content-'+name+'.png')))
  browser.close()
 server.shutdown()
 assert not errors,errors
 assert not bad_requests,bad_requests
 report={'pages':pages,'checks':checks,'page_errors':errors,'failed_local_requests':bad_requests}
 (ROOT/'reports/content-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
