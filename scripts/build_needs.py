"""Render reviewed need-based homepage links as static HTML; no client data or publication."""
import json
import os
import re
from datetime import date
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- MENAGEUP_NEEDS_START -->', '<!-- MENAGEUP_NEEDS_END -->'


def main():
    items = json.loads((ROOT / 'content/needs.json').read_text(encoding='utf-8'))
    if len({item['href'] for item in items}) != len(items):
        raise ValueError('Duplicate need destination')
    cards = []
    for i, item in enumerate(items, 1):
        path = item['href']
        if not re.fullmatch(r'/[a-z0-9-]+/', path) or not (ROOT / path.strip('/') / 'index.html').is_file():
            raise ValueError('Unknown need destination')
        featured = ' need-card-featured' if item.get('featured') else ''
        cards.append(f'<a class="need-card{featured}" href="{path}"><span class="need-number" aria-hidden="true">{i:02}</span><h3>{escape(item["title"])}</h3><p>{escape(item["text"])}</p><span class="need-link">{escape(item["label"])} <span aria-hidden="true">↗</span></span></a>')
    block = START + '\n<div class="needs-grid" aria-label="Choisir une prestation selon votre besoin">\n' + '\n'.join(cards) + '\n</div>\n' + END
    file = ROOT / 'index.html'
    original = file.read_text(encoding='utf-8')
    if START in original:
        html, count = re.subn(re.escape(START) + r'.*?' + re.escape(END), lambda _: block, original, flags=re.S)
    else:
        # Replace the former extra service cards; retain the four illustrated service families.
        html, removed = re.subn(r'<div class="service-focus">.*?</a>\s*</div>\s*</div>', '', original, count=1, flags=re.S)
        if removed != 1:
            raise ValueError('Expected previous service focus block')
        html, count = re.subn(r'(?=<div class="svc-rows">)', lambda _: block + '\n', html, count=1)
    if count != 1:
        raise ValueError('Expected one homepage need block')
    if html != original:
        file.write_text(html, encoding='utf-8', newline='\n')
        ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        ET.register_namespace('', ns)
        ET.register_namespace('image', 'http://www.google.com/schemas/sitemap-image/1.1')
        tree = ET.parse(ROOT / 'sitemap.xml')
        node = next(n for n in tree.getroot() if n.findtext('{' + ns + '}loc') == 'https://menageup.fr/')
        modified = node.find('{' + ns + '}lastmod')
        if modified is None:
            modified = ET.SubElement(node, '{' + ns + '}lastmod')
        modified.text = date.fromisoformat(os.environ.get('MENAGEUP_CONTENT_DATE', date.today().isoformat())).isoformat()
        ET.indent(tree, space='  ')
        tree.write(ROOT / 'sitemap.xml', encoding='UTF-8', xml_declaration=True)
    print(f'{len(items)} need-based homepage links built. No publication.')


if __name__ == '__main__':
    main()
