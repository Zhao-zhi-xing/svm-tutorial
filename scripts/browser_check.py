"""浏览器验收（可选开发依赖 playwright）；使用本机 Chrome，无需模型服务。"""
from pathlib import Path
import json,threading,http.server,functools,urllib.parse
from html.parser import HTMLParser
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/'_book'


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for k in ['href','src']:
            if k in a:self.links.append(a[k])


def link_check():
    pages={p:Links() for p in BOOK.rglob('*.html') if 'site_libs' not in p.parts and 'assets' not in p.parts}
    for p,parser in pages.items():parser.feed(p.read_text(encoding='utf-8'))
    broken=[]
    for p,parser in pages.items():
      for url in parser.links:
        u=urllib.parse.urlsplit(url)
        if u.scheme or u.netloc or url.startswith('data:'):continue
        target=(BOOK/u.path.lstrip('/')) if u.path.startswith('/') else (p.parent/urllib.parse.unquote(u.path))
        target=target.resolve() if u.path else p
        if not target.exists():broken.append([str(p.relative_to(BOOK)),url])
        elif u.fragment and target in pages and urllib.parse.unquote(u.fragment) not in pages[target].ids:
            broken.append([str(p.relative_to(BOOK)),url])
    assert not broken,broken[:20]
    return len(pages)


def main():
    page_count=link_check()
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    handler=functools.partial(QuietHandler,directory=str(ROOT))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    # 故意用子路径，检验GitHub Pages仓库目录形式。
    base=f'http://127.0.0.1:{server.server_port}/_book/'
    errors=[];requests=[];results=[]
    with sync_playwright() as p:
      browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--enable-unsafe-swiftshader'])
      context=browser.new_context(viewport={'width':1440,'height':1000})
      page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
      page.on('response',lambda r:requests.append(r.url) if r.status>=400 and r.url.startswith(base) else None)
      def visit(path):
        page.goto(base+path,wait_until='domcontentloaded')
        page.wait_for_function("typeof Plotly !== 'undefined'")
        page.wait_for_timeout(600)
      visit('index.html')
      page.wait_for_selector('[data-svm-lab="geometry"] .js-plotly-plot')
      angle=page.locator('input[name=angle]')
      for value in ['0','90','180']:
        angle.fill(value);angle.dispatch_event('input')
      assert page.locator('.stat-label').get_by_text('‖w‖',exact=True).locator('..').locator('.stat-value').inner_text()=='1.00'
      for value in ['-2','2']:
        page.locator('input[name=bias]').fill(value);page.locator('input[name=bias]').dispatch_event('input')
      point=page.locator('select[name=point]');point.select_option(index=point.locator('option').count()-1)
      point.dispatch_event('input')
      page.locator('.lab-controls button').click()
      assert angle.input_value()=='45'
      page.screenshot(path=str(ROOT/'reports/home-desktop.png'),full_page=True)
      assert page.locator('.lab-plot').evaluate('(el)=>el._fullLayout.xaxis._length')>600
      assert page.locator('.stat-card').count()>=4
      results.append('geometry metric cards, desktop plot width, angle/bias endpoints and reset')
      models=json.loads((ROOT/'assets/models.json').read_text(encoding='utf-8'))
      for kind,path in [('linear','chapters/02-soft-margin.html'),('rbf','chapters/04-kernels.html')]:
        visit(path);lab=page.locator(f'[data-svm-lab={kind}]');lab.wait_for()
        for m in models[kind]['models']:
            lab.locator('select[name=C]').select_option(str(m['C']))
            if kind=='rbf':lab.locator('select[name=gamma]').select_option(str(m['gamma']))
            assert lab.get_attribute('data-current-sv')==str(len(m['sv']))
            assert float(lab.get_attribute("data-current-c"))==m["C"]
            assert lab.locator('.lab-plot').evaluate('(el)=>el.data[0].z')==m['decision']
        lines=lab.locator('.lab-plot').evaluate('(el)=>el.data.filter(t=>t.type==="scatter" && t.mode==="lines").map(t=>({name:t.name,color:t.line.color,dash:t.line.dash}))')
        assert len(lines)==3 and len({t['color'] for t in lines})==3
        assert sum(t.get('dash')=='dash' for t in lines)==2
        lab.locator('button').click()
        best=models[kind]['models'][models[kind]['best_index']]
        assert float(lab.get_attribute('data-current-c'))==best['C']
        for name in ['Python','R','Python']:
            page.get_by_role('tab',name=name,exact=True).first.click()
            page.wait_for_timeout(200)
        assert page.locator('.tab-pane.active .js-plotly-plot').first.bounding_box()['width']>700
        results.append(f'{kind}: all precomputed states, reset, Python/R plot resize')
      mapping=page.locator('[data-svm-lab=mapping]')
      assert mapping.locator('canvas').count()>0
      scene=mapping.locator('.lab-plot');scene.scroll_into_view_if_needed()
      page.wait_for_timeout(200)
      before=scene.evaluate('(el)=>el._fullLayout.scene._scene.getCamera().eye')
      box=scene.bounding_box();x=box['x']+box['width']*.5;y=box['y']+box['height']*.5
      page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+80,y+40,steps=8);page.mouse.up();page.wait_for_timeout(300)
      after=scene.evaluate('(el)=>el._fullLayout.scene._scene.getCamera().eye')
      assert sum(abs(after[k]-before[k]) for k in before)>.05
      mapping.locator('button').click();page.wait_for_timeout(200)
      reset_camera=scene.evaluate('(el)=>el._fullLayout.scene._scene.getCamera().eye')
      assert all(abs(reset_camera[k]-before[k])<1e-6 for k in before)
      results.append('WebGL 3D rotation and reset')
      visit('chapters/05-multiclass.html')
      lab=page.locator('[data-svm-lab=multiclass]')
      for mode in ['OvR 符号判定','OvR argmax','OvO 投票']:
        lab.locator('select[name=strategy]').select_option(mode)
        for coord in [-2.8,2.8]:
          for name in ['x1','x2']:
            lab.locator(f'input[name={name}]').fill(str(coord));lab.locator(f'input[name={name}]').dispatch_event('input')
        assert lab.get_attribute('data-current-strategy')==mode
      lab.locator('select[name=step]').select_option('2');lab.locator('button').click()
      assert lab.get_attribute('data-current-strategy')=='OvR 符号判定'
      lab.scroll_into_view_if_needed();page.screenshot(path=str(ROOT/'reports/multiclass-desktop.png'))
      results.append('multiclass rules, coordinate endpoints, step, reset')
      for path in ['chapters/06-workflow.html','chapters/07-cases.html']:
        visit(path)
        for name in ['R','Python']:
            page.get_by_role('tab',name=name,exact=True).first.click();page.wait_for_timeout(200)
        assert page.locator('.js-plotly-plot').count()>0
      results.append('ROC/PR and all case charts present')
      additions=json.loads((ROOT/'assets/experiments.json').read_text(encoding='utf-8'))
      for kind,path in [('scaling','chapters/06-workflow.html'),('imbalance','chapters/06-workflow.html'),('calibration','chapters/06-workflow.html'),('repeated','chapters/07-cases.html')]:
        visit(path);lab=page.locator(f'[data-experiment={kind}]')
        for index,state in enumerate(additions[kind]['states']):
          lab.locator('select[name=experiment]').select_option(str(index))
          assert lab.get_attribute('data-current-state')==str(index)
          page.wait_for_timeout(100)
          trace_index=min(1,len(state['figure']['data'])-1)
          assert lab.locator('.lab-plot').evaluate('(el,i)=>el.data[i].y',trace_index)==state['figure']['data'][trace_index]['y']
          assert lab.locator('.stat-card').count()==len(state['cards'])
          for card_index,(_,expected) in enumerate(state['cards']):
            actual=lab.locator('.stat-value').nth(card_index).inner_text()
            if isinstance(expected,(int,float)):assert abs(float(actual)-expected)<5.1e-5
            else:assert actual==expected
          assert lab.locator('.lab-plot').bounding_box()['width']>700
        lab.locator('button').click();assert lab.get_attribute('data-current-state')=='0'
      results.append('scaling, class weights, calibration and repeated evaluation: every state, metrics and reset')
      visit('chapters/03-duality-smo.html');lab=page.locator('[data-experiment=smo]')
      for index,state in enumerate(additions['smo']['states']):
        lab.locator('input[name=smo-step]').fill(str(index));lab.locator('input[name=smo-step]').dispatch_event('input')
        assert lab.get_attribute('data-current-step')==str(index)
        for point in range(len(additions['smo']['points'])):
          lab.locator('select[name=smo-point]').select_option(str(point))
          assert lab.get_attribute('data-current-point')==str(point)
          alpha=float(lab.locator('.stat-card').filter(has=page.locator('.stat-label').get_by_text('所选 α',exact=True)).locator('.stat-value').inner_text())
          assert abs(alpha-state['alpha'][point])<5.1e-5
        assert lab.locator('.lab-table tr').count()==9
      lab.locator('button').click()
      assert lab.get_attribute('data-current-step')==str(len(additions['smo']['states'])-1)
      lab.locator('select[name=smo-point]').select_option('7')
      lab.locator('.lab-plot .scatterlayer .trace').first.locator('.point').first.click(force=True)
      assert lab.get_attribute('data-current-point')=='0'
      lab.screenshot(path=str(ROOT/'reports/smo-extension.png'))
      results.append('SMO: every real update, every sample, alpha agreement, direct point click and reset')
      visit('chapters/00-python-start.html')
      assert page.locator('a[href$="python-svm-start.ipynb"]').count()>0
      assert (BOOK/'notebooks/python-svm-start.ipynb').exists()
      results.append('standalone Python notebook download and introductory chapter')
      # 图例切换确实改变曲线的显示状态。
      visit('chapters/06-workflow.html')
      graph=page.locator('#heart-ranking-python')
      graph.locator('.legend .traces').nth(1).click();page.wait_for_timeout(400)
      assert graph.evaluate('(el)=>el.data[1].visible') is True
      results.append('Plotly PR legend toggle')
      for path in ['chapters/01-geometry.html','chapters/03-duality-smo.html','chapters/08-modern.html','chapters/09-authoring.html','references.html']:
        visit(path);assert '未找到引用' not in page.locator('main').inner_text()
      for path in ['chapters/01-geometry.html','chapters/02-soft-margin.html','chapters/03-duality-smo.html','chapters/04-kernels.html','chapters/05-multiclass.html','chapters/06-workflow.html']:
        visit(path)
        page.wait_for_function('!!window.MathJax && !!document.querySelector("mjx-container")')
        assert page.locator('mjx-merror').count()==0, path
      results.append('expanded derivations: MathJax renders without formula errors')
      results.append('desktop-first layout; narrow-screen acceptance retired by user request')
      visit('index.html')
      if not page.locator('#quarto-search input:visible').count():
        page.locator('#quarto-search').click()
      search=page.locator('input.aa-Input:visible').first
      search.fill('软间隔');page.wait_for_timeout(600)
      assert page.locator('.aa-Item').count()>0
      results.append('book search')
      browser.close()
    server.shutdown()
    assert not errors,errors
    assert not requests,requests
    report={'pages':page_count,'passed':results,'page_errors':errors,'local_http_errors':requests,'deployment_test':'served under /_book/ prefix'}
    (ROOT/'reports/browser-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
