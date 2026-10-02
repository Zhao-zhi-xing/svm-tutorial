"""浏览器检查紧凑热图、双语言混淆矩阵与模型比较。"""
from pathlib import Path
import functools, http.server, json, threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/_book/'
    errors=[];results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'chapters/06-workflow.html',wait_until='domcontentloaded')
        plot=page.locator('[data-svm-lab=tuning] .lab-plot')
        page.wait_for_function('!!document.querySelector("[data-svm-lab=tuning] .lab-plot")._fullLayout')
        assert plot.bounding_box()['width']<=660 and plot.bounding_box()['height']==420
        assert len(plot.evaluate('el=>el.data[0].text'))==4
        plot.screenshot(path=str(ROOT/'reports/chart-tuning.png'))
        results.append('compact C-gamma grid with direct score labels')
        page.goto(base+'chapters/07-cases.html',wait_until='domcontentloaded')
        page.wait_for_function('!!document.getElementById("heart-python")._fullLayout')
        for name in ['heart','khan']:
            graph=page.locator('#'+name+'-python')
            graph.scroll_into_view_if_needed()
            assert graph.bounding_box()['width']<=600 and graph.bounding_box()['height']==490
            payload=graph.evaluate('el=>({z:el.data[0].z,shares:el.data[0].customdata,range:el._fullLayout.yaxis.range,x:el._fullLayout.xaxis._length,y:el._fullLayout.yaxis._length})')
            assert payload['range'][0]>payload['range'][1], payload
            assert '%{customdata' not in graph.inner_text()
            if name=='heart':assert '92%' in graph.inner_text()
            assert abs(payload['x']-payload['y'])<2
            for counts,shares in zip(payload['z'],payload['shares']):
                for count,share in zip(counts,shares):assert abs(share-count/max(sum(counts),1))<1e-7
            graph.screenshot(path=str(ROOT/f'reports/chart-{name}.png'))
            tabset=graph.locator('xpath=ancestor::div[contains(@class,"panel-tabset")][1]')
            tabset.get_by_role('tab',name='R',exact=True).click()
            rgraph=page.locator('#'+name+'-r')
            page.wait_for_timeout(500)
            assert rgraph.is_visible()
            assert '%{customdata' not in rgraph.inner_text()
            if name=='heart':assert '92%' in rgraph.inner_text()
            assert rgraph.bounding_box()['width']<=600 and rgraph.bounding_box()['height']==490
            assert rgraph.evaluate('el=>el.data[0].z')==payload['z']
            assert rgraph.evaluate('el=>el._fullLayout.yaxis.range[0]>el._fullLayout.yaxis.range[1]')
            tabset.get_by_role('tab',name='Python',exact=True).click()
        results.append('Python/R compact square confusion matrices; counts and row shares match')
        graph=page.locator('#model-comparison')
        graph.scroll_into_view_if_needed()
        assert graph.bounding_box()['height']==410 and graph.bounding_box()['width']<=880
        assert graph.evaluate('el=>el.data.length')==2
        assert graph.evaluate('el=>el.data.every(t=>t.orientation==="h")')
        assert graph.evaluate('el=>el.layout.xaxis.range[0]')==0
        assert graph.evaluate('el=>el.data[0].y')==graph.evaluate('el=>el.data[1].y')
        graph.screenshot(path=str(ROOT/'reports/chart-model-comparison.png'))
        results.append('horizontal CV/test grouped bars; direct labels and zero baseline')
        browser.close()
    server.shutdown()
    assert not errors,errors
    report={'passed':results,'page_errors':errors}
    (ROOT/'reports/chart-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
