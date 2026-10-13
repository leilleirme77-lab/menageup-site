"""Build reviewed real-project pages and maintain their own sitemap entries. Does not deploy."""
from pathlib import Path
from urllib.parse import urlencode
from html import escape
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import date
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://menageup.fr'
HUB_PATH = '/realisations/'
DATA = ROOT / 'content/realisations.json'
CONTENT_DATE = date.fromisoformat(os.environ.get('MENAGEUP_CONTENT_DATE', date.today().isoformat())).isoformat()
PROJECT_DETAILS_CSS = '''
.project-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;border-top:1px solid var(--line);padding-top:20px;margin:24px 0 0}
.project-stats>div{display:flex;flex-direction:column;gap:7px}
.project-stats dt{font-size:13px;line-height:1.4;color:var(--muted)}
.project-stats dd{order:-1;margin:0;font-family:'Fraunces',Georgia,serif;font-size:31px;font-weight:600;line-height:1.1;color:var(--navy);white-space:nowrap}
.context-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:26px}
.context-grid article{border-top:1px solid var(--line);padding-top:22px}
.context-grid h3{font-size:19px;color:var(--navy)}
.context-grid p{font-size:16px;color:var(--muted);margin-top:12px}
.project-followup{background:#f7f8fa}
.project-followup .section-head{margin-bottom:22px}
@media(max-width:700px){.project-stats{gap:12px;padding-top:18px;margin-top:22px}.project-stats dd{font-size:29px}.project-stats dt{font-size:12px}.context-grid{grid-template-columns:1fr;gap:23px}.context-grid article{padding-top:18px}.context-grid p{font-size:15px}.project-followup .related-links{margin-top:18px}}
'''


def esc(value):
    return escape(str(value), quote=True)


def dimensions(file):
    path = ROOT / file
    if not path.is_file():
        raise ValueError('Missing real-project photograph: ' + file)
    with Image.open(path) as image:
        return image.size


def image_tag(file, alt, sizes, eager=False):
    """Prefer the 640px image; large originals remain available through explicit links."""
    original = ROOT / file
    width, height = dimensions(file)
    preview = original.with_name(original.stem + '-640.webp')
    src = file
    candidates = []
    if preview.is_file():
        src = preview.relative_to(ROOT).as_posix()
        preview_width, preview_height = dimensions(src)
        candidates.append(f'/{src} {preview_width}w')
        # The two exterior originals are large; open them only on the reader's request.
        if original.stat().st_size <= 350_000:
            candidates.append(f'/{file} {width}w')
        width, height = preview_width, preview_height
    attrs = f'src="/{esc(src)}" alt="{esc(alt)}" width="{width}" height="{height}" decoding="async"'
    if candidates:
        attrs += f' srcset="{esc(", ".join(candidates))}" sizes="{esc(sizes)}"'
    attrs += ' fetchpriority="high"' if eager else ' loading="lazy"'
    return '<img ' + attrs + '>'


def quote_link(path, service='', audience='', city=''):
    params = {}
    if service:
        params['service'] = service
    if audience:
        params['audience'] = audience
    if city:
        params['ville'] = city
    params['source'] = path
    return '/?' + urlencode(params) + '#devis'


def header(quote):
    links = '<a href="/#services">Nos prestations</a><a href="/realisations/" aria-current="location">Réalisations</a><a href="/conseils/">Conseils</a><a href="/qui-sommes-nous/">Qui sommes-nous</a>'
    return f'''<a class="skip" href="#contenu">Aller au contenu</a>
<header class="topbar"><div class="wrap topbar-inner">
<a class="brand" href="/" aria-label="MénageUp — accueil"><img src="/logo-v3.png" alt="MénageUp" width="549" height="160"></a>
<nav class="desktop-nav" aria-label="Navigation principale">{links}</nav>
<div class="nav-actions"><a class="btn small" href="{esc(quote)}"><span class="desktop-label">Demander un devis</span><span class="mobile-label">Devis gratuit</span></a>
<details class="mobile-menu"><summary aria-label="Menu de navigation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" stroke-linecap="round"/></svg></summary><nav class="mobile-links" aria-label="Navigation mobile">{links}<a href="tel:+33648304965">Appeler MénageUp</a></nav></details></div>
</div></header>'''


def footer():
    return '''<footer class="footer"><div class="wrap footer-grid"><div><a class="brand" href="/" aria-label="MénageUp — accueil"><img src="/logo-v3.png" alt="MénageUp" width="549" height="160" loading="lazy"></a><p>Vos espaces, notre exigence.<br>Seine-et-Marne (77) et Île-de-France.</p></div><nav class="footer-links" aria-label="Liens utiles"><a href="/realisations/">Réalisations</a><a href="/conseils/">Conseils</a><a href="/qui-sommes-nous/">Qui sommes-nous</a><a href="/mentions-legales/">Mentions légales</a><a href="tel:+33648304965">06 48 30 49 65</a></nav></div></footer>'''


def document(title, description, path, og_image, primary_image, crumbs, body, quote):
    og_width, og_height = dimensions(og_image)
    main_width, main_height = dimensions(primary_image)
    canonical = DOMAIN + path
    graph = {
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'WebPage', '@id': canonical + '#page', 'url': canonical,
             'name': title, 'description': description, 'inLanguage': 'fr-FR',
             'isPartOf': {'@id': DOMAIN + '/#website'},
             'primaryImageOfPage': {'@type': 'ImageObject', 'url': DOMAIN + '/' + primary_image,
                                    'width': main_width, 'height': main_height}},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': i + 1, 'name': name, 'item': DOMAIN + url}
                for i, (name, url) in enumerate(crumbs)]}
        ]
    }
    ldjson = json.dumps(graph, ensure_ascii=False, indent=2).replace('</', '<\\/')
    details_style = '<style>' + PROJECT_DETAILS_CSS + '</style>' if 'project-followup' in body or 'project-stats' in body else ''
    return f'''<!DOCTYPE html>
<html lang="fr" data-theme="light">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta name="theme-color" content="#14336E"><meta property="og:type" content="website"><meta property="og:site_name" content="MénageUp"><meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{DOMAIN}/{esc(og_image)}"><meta property="og:image:width" content="{og_width}"><meta property="og:image:height" content="{og_height}"><meta property="og:image:type" content="image/webp"><meta property="og:image:alt" content="Photographie d'une réalisation MénageUp">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{DOMAIN}/{esc(og_image)}">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="512x512" href="/favicon.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/fonts.css"><link rel="stylesheet" href="/assets/realisations.css">
<script defer src="/assets/navigation-menu.js"></script>
{details_style}
<script type="application/ld+json">{ldjson}</script>
</head>
<body>{header(quote)}{body}{footer()}</body>
</html>
'''


def breadcrumbs(items):
    parts = [f'<a href="{esc(url)}">{esc(name)}</a>' for name, url in items[:-1]] + [f'<span aria-current="page">{esc(items[-1][0])}</span>']
    return '<nav class="wrap breadcrumb" aria-label="Fil d’Ariane">' + '<span aria-hidden="true">/</span>'.join(parts) + '</nav>'


def proof_note(hub=False):
    text = 'Photographies des réalisations présentées. Retrouvez les étapes sur chaque page.' if hub else 'Photographies de la réalisation présentée. Ouvrez chaque photo pour la voir en entier.'
    return f'''<div class="wrap"><div class="proof-note"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="3" y="6" width="18" height="15" rx="3"/><path d="M8 6l1-3h6l1 3"/><circle cx="12" cy="13" r="3.5"/></svg><p>{esc(text)}</p></div></div>'''


def photo(item, layout):
    original_width, _ = dimensions(item['file'])
    frame_class = 'photo-frame' + (' low-resolution' if original_width < 640 and item.get('fit') != 'center-crop' else '')
    classes = 'proof-photo' + (' wide' if item.get('wide') else '')
    if item.get('wide'):
        sizes = '(max-width:700px) calc(100vw - 36px), (max-width:1040px) calc(100vw - 64px), 980px'
    elif layout == 'pair':
        sizes = '(max-width:700px) calc(100vw - 36px), (max-width:1224px) calc((100vw - 88px) / 2), 568px'
    else:
        sizes = '(max-width:700px) calc(100vw - 36px), (max-width:900px) calc((100vw - 88px) / 2), (max-width:1224px) calc((100vw - 112px) / 3), 371px'
    return f'''<figure class="{classes}"><div class="photo-topline"><span class="photo-stage">{esc(item['stage'])}</span><a href="/{esc(item['file'])}" aria-label="Voir la photo complète : {esc(item['alt'])}">Voir la photo complète ↗</a></div><div class="{frame_class}">{image_tag(item['file'], item['alt'], sizes)}</div><figcaption>{esc(item['caption'])}</figcaption></figure>'''


def project_stats(case):
    if not case.get('stats'):
        return ''
    items = ''.join(f'<div><dt>{esc(item["label"])}</dt><dd>{esc(item["value"])}</dd></div>' for item in case['stats'])
    return '<dl class="project-stats" aria-label="Les chiffres de cette intervention">' + items + '</dl>'


def project_context(case):
    context = case.get('context')
    if not context:
        return ''
    points = ''.join(f'<article><h3>{esc(item["title"])}</h3><p>{esc(item["text"])}</p></article>' for item in context['points'])
    return f'''<section class="section project-context" id="contexte"><div class="wrap"><div class="section-head"><div><p class="eyebrow">Le contexte de la réalisation</p><h2>{esc(context['title'])}</h2></div><p>{esc(context['intro'])}</p></div><div class="context-grid">{points}</div></div></section>'''


def project_follow_up(case):
    follow_up = case.get('follow_up')
    if not follow_up:
        return ''
    return f'''<section class="section project-followup"><div class="wrap"><div class="section-head"><div><p class="eyebrow">Photos de réalisation et avis clients</p><h2>{esc(follow_up['title'])}</h2></div><p>{esc(follow_up['text'])}</p></div><div class="related-links"><a href="/realisations/">Voir nos réalisations ↗</a><a href="https://share.google/d4WL0FlPcgTL4Hdfk" target="_blank" rel="noopener noreferrer" aria-label="Lire les avis sur Google (nouvel onglet)">Lire les avis sur Google ↗</a></div></div></section>'''


def case_page(case):
    path = HUB_PATH + case['slug'] + '/'
    quote = quote_link(path, case['service_code'], case['audience'], case['city'])
    crumbs = [('Accueil', '/'), ('Réalisations', HUB_PATH), (case['city'] + ' (' + case['postal_code'] + ')', path)]
    sections = []
    for section in case['sections']:
        photos = ''.join(photo(item, section['layout']) for item in section['photos'])
        sections.append(f'''<section class="section" id="{esc(section['id'])}"><div class="wrap"><div class="section-head"><div><p class="eyebrow">{esc(section['eyebrow'])}</p><h2>{esc(section['title'])}</h2></div><p>{esc(section['intro'])}</p></div><div class="photo-grid {esc(section['layout'])}">{photos}</div></div></section>''')
    related = ''.join(f'<a href="{esc(item["href"])}">{esc(item["label"])} ↗</a>' for item in case['related'])
    guide = {
        'grandnettoyage': ('nettoyer-logement-inhabite-depuis-longtemps', 'Guide : préparer un logement longtemps inhabité'),
        'debarras': ('debarras-puis-nettoyage-logement', 'Pour un projet en intérieur : débarras puis nettoyage'),
    }.get(case['service_code'])
    if guide:
        related += f'<a href="/conseils/{guide[0]}/">{esc(guide[1])} ↗</a>'
    hero_img = image_tag(case['hero'], case['hero_alt'], '(max-width:700px) calc(100vw - 36px), (max-width:1224px) calc((100vw - 120px) / 2), 552px', eager=True)
    body = breadcrumbs(crumbs) + f'''<main id="contenu"><section class="hero"><div class="wrap hero-grid"><div><p class="eyebrow">{esc(case['category'])}</p><h1>{esc(case['h1'])}</h1><p class="intro">{esc(case['intro'])}</p>{project_stats(case)}<div class="case-meta"><span>{esc(case['city'])} · {esc(case['postal_code'])}</span><span>Photos de l'intervention</span></div><div class="hero-actions"><a class="btn" href="#photos">Voir les photos ↓</a><a class="btn ghost" href="{esc(quote)}">Parlons de votre besoin ↗</a></div></div><figure class="hero-figure"><div class="hero-image">{hero_img}<span class="photo-stage">{esc(case['hero_stage'])}</span></div><figcaption><span>{esc(case['city'])} — {esc(case['hero_stage'].lower())}.</span><a href="/{esc(case['hero'])}">Voir la photo complète ↗</a></figcaption></figure></div></section>{proof_note()}{project_context(case)}<div id="photos">{''.join(sections)}</div>{project_follow_up(case)}<section class="project-cta"><div class="wrap project-cta-grid"><div><h2>{esc(case['quote_title'])}</h2><p>{esc(case['quote_text'])}</p></div><a class="btn" href="{esc(quote)}">Demander un devis gratuit ↗</a></div></section><section class="related"><div class="wrap"><h2>Pour préparer la suite.</h2><div class="related-links">{related}<a href="/realisations/">Toutes nos réalisations ↗</a></div></div></section></main>'''
    return document(case['title'], case['description'], path, case['og_image'], case['primary_image'], crumbs, body, quote)


def hub_page(data):
    hub = data['hub']
    cards = []
    for case in data['cases']:
        image = image_tag(case['hero'], case['hero_alt'], '(max-width:700px) calc(100vw - 36px), (max-width:1224px) calc((100vw - 90px) / 2), 567px')
        cards.append(f'''<a class="project-card" href="{HUB_PATH}{esc(case['slug'])}/"><div class="project-card-image">{image}<span class="photo-stage">{esc(case['hero_stage'])}</span></div><div class="project-card-copy"><div class="case-meta"><span>{esc(case['city'])} · {esc(case['postal_code'])}</span></div><h2>{esc(case['category'])}</h2><p>{esc(case['card_text'])}</p><span class="card-link">Voir la réalisation ↗</span></div></a>''')
    quote = quote_link(HUB_PATH)
    crumbs = [('Accueil', '/'), ('Réalisations', HUB_PATH)]
    body = breadcrumbs(crumbs) + f'''<main id="contenu"><div class="wrap"><section class="hub-hero"><p class="eyebrow">Réalisations MénageUp · Seine-et-Marne</p><h1>{esc(hub['h1'])}</h1><p class="intro">{esc(hub['intro'])}</p></section></div>{proof_note(hub=True)}<section class="wrap projects-grid" aria-label="Nos réalisations">{''.join(cards)}</section><section class="project-cta"><div class="wrap project-cta-grid"><div><h2>Parlons de vos espaces.</h2><p>Indiquez la commune, l'état des lieux et les tâches à prévoir. Nous préparons avec vous le périmètre de la prestation et votre devis.</p></div><a class="btn" href="{esc(quote)}">Demander un devis gratuit ↗</a></div></section></main>'''
    first = data['cases'][0]
    return document(hub['title'], hub['description'], HUB_PATH, first['og_image'], first['primary_image'], crumbs, body, quote)


def sitemap_tree(data, changed):
    """Update only the project hub/cases; keep every unrelated URL and lastmod unchanged."""
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    image_ns = 'http://www.google.com/schemas/sitemap-image/1.1'
    ET.register_namespace('', ns)
    ET.register_namespace('image', image_ns)
    tree = ET.parse(ROOT / 'sitemap.xml')
    root = tree.getroot()
    known = {node.find('{' + ns + '}loc').text: node for node in root}
    if len(known) != len(root):
        raise ValueError('Duplicate sitemap URL')
    entries = {DOMAIN + HUB_PATH: [case['primary_image'] for case in data['cases']]}
    for case in data['cases']:
        files = [item['file'] for section in case['sections'] for item in section['photos']]
        entries[DOMAIN + HUB_PATH + case['slug'] + '/'] = list(dict.fromkeys(files + [case['primary_image']]))
    for url, images in entries.items():
        node = known.get(url)
        if node is None:
            node = ET.SubElement(root, '{' + ns + '}url')
            ET.SubElement(node, '{' + ns + '}loc').text = url
            ET.SubElement(node, '{' + ns + '}lastmod').text = CONTENT_DATE
        elif url in changed:
            lastmod = node.find('{' + ns + '}lastmod')
            if lastmod is None:
                lastmod = ET.SubElement(node, '{' + ns + '}lastmod')
            lastmod.text = CONTENT_DATE
        for old in list(node.findall('{' + image_ns + '}image')):
            node.remove(old)
        for file in dict.fromkeys(images):
            dimensions(file)
            image = ET.SubElement(node, '{' + image_ns + '}image')
            ET.SubElement(image, '{' + image_ns + '}loc').text = DOMAIN + '/' + file
    ET.indent(tree, space='  ')
    return tree


def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    cases = data['cases']
    if len({case['slug'] for case in cases}) != len(cases):
        raise ValueError('Duplicate real-project slug')
    service_script = (ROOT / 'assets/devis-context.js').read_text(encoding='utf-8')
    outputs = {ROOT / 'realisations/index.html': hub_page(data)}
    for case in cases:
        if not re.fullmatch(r'[a-z0-9-]+', case['slug']):
            raise ValueError('Invalid real-project slug')
        if not re.search(r'\b' + re.escape(case['service_code']) + r"\s*:", service_script):
            raise ValueError('Unknown quote service')
        outputs[ROOT / 'realisations' / case['slug'] / 'index.html'] = case_page(case)
    changed = {DOMAIN + '/' + file.parent.relative_to(ROOT).as_posix() + '/'
               for file, html in outputs.items()
               if not file.exists() or file.read_text(encoding='utf-8') != html}
    # Render and validate sitemap data successfully before writing any output.
    tree = sitemap_tree(data, changed)
    for file, html in outputs.items():
        url = DOMAIN + '/' + file.parent.relative_to(ROOT).as_posix() + '/'
        if url in changed:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(html, encoding='utf-8', newline='\n')
    tree.write(ROOT / 'sitemap.xml', encoding='UTF-8', xml_declaration=True)
    print(f'{len(outputs)} real-project pages built; {len(changed)} HTML files changed; '
          f'{len(tree.getroot())} sitemap URLs. Unrelated entries retained. No deployment.')


if __name__ == '__main__':
    main()
