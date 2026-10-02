"""检查居中阅读布局和目录；使用可选依赖 Playwright 与本机 Chrome。"""
from pathlib import Path
import functools, http.server, json, threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/_book/'
    errors, results = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True, args=['--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width':1440,'height':1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        for width in [1280, 1440, 1920, 2560]:
            page.set_viewport_size({'width':width,'height':1000})
            page.goto(base+'index.html', wait_until='domcontentloaded')
            page.wait_for_selector('.lab-plot.js-plotly-plot')
            page.wait_for_timeout(800)
            main = page.locator('main').bounding_box()
            sidebar = page.locator('#quarto-sidebar').bounding_box()
            aside = page.locator('#quarto-margin-sidebar').bounding_box()
            assert abs(main['x']+main['width']/2-width/2)<2, (width,main)
            assert sidebar['x']+sidebar['width']<main['x'], (width,sidebar,main)
            assert aside['x']>main['x']+main['width'], (width,aside,main)
            assert page.evaluate('document.documentElement.scrollWidth')<=width+1
            plot = page.locator('.lab-plot').first.bounding_box()
            assert plot['width']<=main['width'] and plot['width']>600
            assert page.locator('.sidebar-item-section').count()==0
            page.screenshot(path=str(ROOT/f'reports/layout-{width}.png'))
            results.append({'viewport':width,'body':main,'plot_width':plot['width']})
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(base+'chapters/03-duality-smo.html',wait_until='domcontentloaded')
        page.wait_for_selector('[data-experiment=smo] .js-plotly-plot')
        assert page.locator('#TOC h2').inner_text()=='本章目录'
        target = page.locator('#TOC a').nth(2)
        target.click()
        page.wait_for_timeout(800)
        assert page.evaluate('location.hash')
        assert page.locator('#TOC .nav-link.active').count()>0
        sidebar = page.locator('#quarto-sidebar').bounding_box()
        assert sidebar['y']>=50 and sidebar['y']<80
        page.screenshot(path=str(ROOT/'reports/layout-chapter.png'))
        page.goto(base+'index.html',wait_until='domcontentloaded')
        page.wait_for_selector('.lab-plot.js-plotly-plot')
        page.set_viewport_size({'width':1920,'height':1000})
        page.wait_for_timeout(800)
        plot = page.locator('.lab-plot').first
        assert abs(plot.evaluate('el=>el._fullLayout.width')-plot.bounding_box()['width'])<2
        page.locator('input[name=angle]').fill('90')
        page.locator('input[name=angle]').dispatch_event('input')
        page.locator('.lab-controls button').first.click()
        assert page.locator('input[name=angle]').input_value()=='45'
        browser.close()
    server.shutdown()
    assert not errors, errors
    report={'layouts':results,'checks':['centered body','separate sidebars','no horizontal overflow','flat chapter list','TOC anchor and active state','sticky sidebar','Plotly window resize and reset'],'page_errors':errors}
    (ROOT/'reports/layout-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
