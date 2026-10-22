"""Add reviewed navigation after page builders; no fabricated city branches.

Only pages in the sitemap are touched. No public trackers or form requests.
Only the confirmed registered office describes the company; Google Business is untouched.
"""
from pathlib import Path
from datetime import date
import os
import xml.etree.ElementTree as ET
from seo_shared import with_sector_navigation

ROOT = Path(__file__).resolve().parents[1]
TODAY = date.fromisoformat(os.environ.get('MENAGEUP_CONTENT_DATE', date.today().isoformat())).isoformat()


def main():
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    ET.register_namespace('image', 'http://www.google.com/schemas/sitemap-image/1.1')
    tree = ET.parse(ROOT / 'sitemap.xml')
    changed = 0
    for node in tree.getroot():
        url = node.findtext('{' + ns + '}loc', '')
        if not url.startswith('https://menageup.fr/'):
            raise ValueError('Unexpected sitemap origin')
        path = '/' + url.removeprefix('https://menageup.fr/').strip('/')
        file = ROOT / path.strip('/') / 'index.html'
        original = file.read_text(encoding='utf-8')
        html = with_sector_navigation(original, path)
        if path == '':
            path = '/'
        if html != original:
            file.write_text(html, encoding='utf-8', newline='\n')
            lastmod = node.find('{' + ns + '}lastmod')
            if lastmod is None:
                lastmod = ET.SubElement(node, '{' + ns + '}lastmod')
            lastmod.text = TODAY
            changed += 1
    ET.indent(tree, space='  ')
    tree.write(ROOT / 'sitemap.xml', encoding='UTF-8', xml_declaration=True)
    print(f'Company identity and navigation enriched on {changed} pages. No Google account modified.')


if __name__ == '__main__':
    main()
