"""Give every page except the homepage the same header and "Retrouvez-nous" block as the homepage.

The header shows "Devis gratuit", the logo, "Appeler" and the same menu as the homepage.
The "Retrouvez-nous" block lists the same networks as the homepage footer.
Pages opened from a link always start at the top.

Run after any build script that regenerates pages:  python scripts/harmonize_site.py
The script is idempotent: running it twice gives the same result.
"""
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.claude', 'node_modules', 'scripts', 'content', 'assets'}
CSS = '<link rel="stylesheet" href="/assets/site-chrome.css">'
PHONE = 'tel:0648304965'

CHEVRON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M9 6l6 6-6 6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
PHONE_ICON = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.12 4.2 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.1 9.9a16 16 0 0 0 6 6l1.26-1.26a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
BURGER = ('<svg class="b" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke-linecap="round"/></svg>'
          '<svg class="x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" stroke-linecap="round"/></svg>')
MENU = [('/', 'Accueil'), ('/#services', 'Nos services'), ('/realisations/', 'Nos réalisations'),
        ('/conseils/', 'Actualité'), ('/conseils/', 'Conseils'), ('/#faq', 'FAQ'), ('/recrutement/', 'Recrutement')]

# Pages opened from a link start at the top; back/forward and #anchors keep the browser's behaviour.
SCRIPT = ('<script data-mu-chrome>(function(){try{var n=performance.getEntriesByType("navigation")[0];'
          'if(!location.hash&&(!n||n.type==="navigate"))window.scrollTo(0,0);}catch(e){}'
          'var m=document.querySelector(".mu-menu");if(!m)return;'
          'm.addEventListener("click",function(e){if(e.target.closest("a"))m.removeAttribute("open");});'
          'document.addEventListener("click",function(e){if(m.hasAttribute("open")&&!m.contains(e.target))m.removeAttribute("open");});'
          'document.addEventListener("keydown",function(e){if(e.key==="Escape")m.removeAttribute("open");});})();</script>')


def home_networks():
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    match = re.search(r'<div class="lks">(.*?)</div></div>', home, re.S)
    if not match:
        raise ValueError('Homepage "Retrouvez-nous" links not found')
    return match.group(1)


def header(path):
    devis = '/?source=' + quote(path, safe='') + '#devis'
    links = ''.join(f'<a href="{href}">{label}{CHEVRON}</a>' for href, label in MENU)
    return ('<header class="mu-header" data-mu-header><div class="mu-in">'
            f'<div class="mu-left"><a class="mu-btn mu-devis" href="{devis}">Devis gratuit</a></div>'
            '<a class="mu-brand" href="/" aria-label="MénageUp — accueil"><img src="/logo-v3.png" alt="MénageUp" width="549" height="160"></a>'
            f'<div class="mu-right"><a class="mu-btn mu-call" href="{PHONE}" aria-label="Appeler MénageUp">{PHONE_ICON}Appeler</a>'
            f'<details class="mu-menu"><summary class="mu-burger" aria-label="Ouvrir le menu">{BURGER}</summary>'
            f'<nav class="mu-panel" aria-label="Menu">{links}<a class="mu-panel-call" href="{PHONE}">{PHONE_ICON}Appeler</a></nav></details>'
            '</div></div></header>')


def social(networks):
    return ('<div class="mu-social" data-mu-social><a class="mu-lbl" href="/reseaux/">Retrouvez-nous</a>'
            f'<div class="mu-lks">{networks}</div></div>')


def footer(networks):
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    office = re.search(r'<p class="site-registered-office" data-registered-office>.*?</p>', home, re.S).group(0)
    legal = re.search(r'<div class="legal">(.*?)</div>', home, re.S).group(1).strip()
    return (f'<footer class="mu-footer" data-mu-footer>{social(networks)}{office}'
            f'<div class="mu-legal">{legal}</div></footer>')


def harmonize(html, path, networks):
    new_header = header(path)
    if 'data-mu-header' in html:
        html = re.sub(r'<header class="mu-header" data-mu-header>.*?</header>', lambda _: new_header, html, count=1, flags=re.S)
    elif re.search(r'<header class="topbar"', html):
        html = re.sub(r'<header class="topbar".*?</header>', lambda _: new_header, html, count=1, flags=re.S)
    else:
        html = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + '\n' + new_header, html, count=1)

    # Same footer as the homepage: networks, registered office, legal notice.
    new_footer = footer(networks)
    html, replaced = re.subn(r'<footer\b.*?</footer>', lambda _: new_footer, html, count=1, flags=re.S)
    if not replaced:
        html = html.replace('</body>', new_footer + '\n</body>', 1)

    if CSS not in html:
        html = html.replace('</head>', CSS + '\n</head>', 1)
    html = re.sub(r'<script data-mu-chrome>.*?</script>\n?', '', html, flags=re.S)
    html = html.replace('</body>', SCRIPT + '\n</body>', 1)
    return html


def main():
    networks = home_networks()
    changed = []
    for file in sorted(ROOT.rglob('*.html')):
        rel = file.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or rel.as_posix() == 'index.html':
            continue
        path = '/' + (rel.parent.as_posix() + '/' if rel.name == 'index.html' and rel.parent.as_posix() != '.' else rel.as_posix())
        html = file.read_text(encoding='utf-8')
        updated = harmonize(html, path, networks)
        if updated != html:
            file.write_text(updated, encoding='utf-8')
            changed.append(path)
    print(f'{len(changed)} pages harmonisées')


if __name__ == '__main__':
    main()
