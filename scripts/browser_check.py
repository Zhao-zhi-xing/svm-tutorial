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
    # Compatibility entrypoint: the self-study revision moved several labs.
    from content_check import main as check_content
    check_content()

if __name__=='__main__':main()
