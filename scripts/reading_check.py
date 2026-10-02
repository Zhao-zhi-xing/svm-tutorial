"""验收教程阅读排版、编号、语言标识与折叠结果。"""
from pathlib import Path
import functools, http.server, json, threading, os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

def main():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=os.environ.get('SVM_CHECK_URL',f'http://127.0.0.1:{server.server_port}/_book/')
    errors=[]; results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1920,'height':1080})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.context.grant_permissions(['clipboard-read','clipboard-write'])
        for name in ['index.html','chapters/03-duality-smo.html','chapters/07-cases.html']:
            page.goto(base+name,wait_until='domcontentloaded')
            page.wait_for_timeout(1600)
            for width in [1280,1440,1920,2560]:
                page.set_viewport_size({'width':width,'height':1080})
                page.wait_for_timeout(350)
                measure=page.evaluate('''()=>{
                  const main=document.querySelector('main'),r=main.getBoundingClientRect();
                  const prose=[...main.querySelectorAll('section.level2 > p')].find(p=>!p.querySelector('.math.display'));
                  const q=prose.getBoundingClientRect();
                  return {center:r.x+r.width/2,body:r.width,prose:q.width,proseCenter:q.x+q.width/2,overflow:document.documentElement.scrollWidth};
                }''')
                assert abs(measure['center']-width/2)<2,measure
                assert abs(measure['proseCenter']-width/2)<2,measure
                assert measure['prose']<=800.1,measure
                assert measure['overflow']<=width+1,measure
                results.append({'page':name,'viewport':width,**measure})
            active=page.locator('#quarto-sidebar .sidebar-link.active').first
            assert active.evaluate("e=>getComputedStyle(e).backgroundColor")=='rgb(234, 240, 255)'
            page.set_viewport_size({'width':1440,'height':1080})
            page.screenshot(path=str(ROOT/'reports'/('reading-'+Path(name).stem+'.png')))
            if name=='index.html':
                assert not page.locator('#title-block-header .chapter-number').count()
                assert active.inner_text()=='导读与学习路线'
                assert page.locator('#quarto-sidebar .sidebar-link').nth(1).locator('.chapter-number').inner_text()=='1'
                assert not page.locator('main h2 .header-section-number').count()
                assert page.locator('.start-learning').get_attribute('href').endswith('00-python-start.html')
                assert page.locator('.tutorial-meta').inner_text().startswith('赵知行')
                assert not page.locator('.quarto-title-meta:visible').count()
            else:
                assert page.locator('.chapter-intro').count()==1
                assert page.locator('.code-language').count()>0
                button=page.locator('.code-copy-button:visible').first
                button.click()
                page.wait_for_timeout(150)
                assert page.evaluate('navigator.clipboard.readText()')
                assert not page.locator('mjx-merror').count()
            if '07-cases' in name:
                details=page.locator('details.result-details')
                assert details.count()==5
                for i in range(details.count()): assert not details.nth(i).get_attribute('open')
                details.first.locator('summary').click()
                assert details.first.evaluate('e=>e.open')
                assert details.first.locator('pre').count()>0
                details.first.locator('summary').click()
                assert not details.first.evaluate('e=>e.open')
                # Native summary remains focusable and keyboard-operable.
                summary=details.first.locator('summary'); page.keyboard.press('Tab'); summary.focus()
                assert summary.evaluate('e=>getComputedStyle(e).outlineStyle')=='solid'
                page.keyboard.press('Enter')
                assert details.first.evaluate('e=>e.open')
        browser.close()
    server.shutdown()
    assert not errors, errors
    report={'measurements':results,'checks':['800px centered prose','1040px centered canvas','no document overflow at four desktop widths','unnumbered homepage','short active navigation','chapter introductions','code language labels','collapsed results and keyboard focus'],'page_errors':errors}
    (ROOT/'reports/reading-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
