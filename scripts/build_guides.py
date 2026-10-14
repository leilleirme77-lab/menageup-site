"""Build reviewed, static advice pages. No publication or automatic content generation."""
from pathlib import Path
from html import escape
from datetime import date
from urllib.parse import urlencode
import json
import re
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://menageup.fr'
HUB = '/conseils/'
FILES = ['content/guides-logement.json', 'content/guides-chantier.json']


def esc(value):
    return escape(str(value), quote=True)


def image_tag(file, alt, sizes, eager=False):
    original = ROOT / file
    with Image.open(original) as im:
        width, height = im.size
    variants = []
    for suffix in ('-640', '-960', ''):
        candidate = original.with_name(original.stem + suffix + '.webp')
        if candidate.is_file():
            with Image.open(candidate) as im:
                w, h = im.size
            if candidate.stat().st_size < 400_000:
                variants.append((w, h, candidate.relative_to(ROOT).as_posix()))
    variants.sort()
    src = variants[0][2] if variants else file
    attrs = f'src="/{esc(src)}" alt="{esc(alt)}" width="{width}" height="{height}" decoding="async"'
    if variants:
        attrs += f' srcset="{esc(", ".join("/" + f + " " + str(w) + "w" for w, h, f in variants))}" sizes="{esc(sizes)}"'
    attrs += ' fetchpriority="high"' if eager else ' loading="lazy"'
    return '<img ' + attrs + '>'


def quote(path, guide=None):
    params = {'source': path}
    if guide:
        params.update(service=guide['service_code'], audience=guide['audience'])
    return '/?' + urlencode(params) + '#devis'


def header(cta):
    links = '<a href="/#services">Nos prestations</a><a href="/realisations/">Réalisations</a><a href="/conseils/" aria-current="location">Conseils</a><a href="/qui-sommes-nous/">Qui sommes-nous</a>'
    return f'''<a class="skip" href="#contenu">Aller au contenu</a><div class="reading-progress" aria-hidden="true"></div>
<header class="topbar"><div class="wrap topbar-inner"><a class="brand" href="/" aria-label="MénageUp — accueil"><img src="/logo-v3.png" alt="MénageUp" width="549" height="160"></a><nav class="desktop-nav" aria-label="Navigation principale">{links}</nav><div class="nav-actions"><a class="btn small" href="{esc(cta)}"><span class="desktop-label">Demander un devis</span><span class="mobile-label">Devis gratuit</span></a><details class="mobile-menu"><summary aria-label="Menu de navigation"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg></summary><nav class="mobile-links" aria-label="Navigation mobile">{links}<a href="tel:+33648304965">Appeler MénageUp</a></nav></details></div></div></header>'''


def footer():
    return '''<footer class="footer"><div class="wrap footer-grid"><div><a class="brand" href="/" aria-label="MénageUp — accueil"><img src="/logo-v3.png" alt="MénageUp" width="549" height="160" loading="lazy"></a><p>Vos espaces, notre exigence.<br>Seine-et-Marne (77) et Île-de-France.</p></div><nav class="footer-links" aria-label="Liens utiles"><a href="/conseils/">Conseils</a><a href="/realisations/">Réalisations</a><a href="/qui-sommes-nous/">Qui sommes-nous</a><a href="/mentions-legales/">Mentions légales</a><a href="tel:+33648304965">06 48 30 49 65</a></nav></div></footer>'''


def breadcrumbs(items):
    parts = [f'<a href="{esc(url)}">{esc(name)}</a>' for name, url in items[:-1]]
    parts.append(f'<span aria-current="page">{esc(items[-1][0])}</span>')
    return '<nav class="wrap breadcrumb" aria-label="Fil d’Ariane">' + '<span aria-hidden="true">/</span>'.join(parts) + '</nav>'


def document(title, description, path, image, alt, crumbs, body, cta, guide=None):
    canonical = DOMAIN + path
    with Image.open(ROOT / image) as im:
        w, h = im.size
    image_object = {'@type': 'ImageObject', 'url': DOMAIN + '/' + image, 'width': w, 'height': h}
    page = {'@type': 'WebPage', '@id': canonical + '#page', 'url': canonical, 'name': title,
            'description': description, 'inLanguage': 'fr-FR', 'isPartOf': {'@id': DOMAIN + '/#website'},
            'primaryImageOfPage': image_object}
    graph = [page, {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': name, 'item': DOMAIN + url}
        for i, (name, url) in enumerate(crumbs)]}]
    if guide:
        article_id = canonical + '#article'
        page['mainEntity'] = {'@id': article_id}
        graph.append({'@type': 'Article', '@id': article_id, 'headline': guide['h1'],
                      'description': description, 'inLanguage': 'fr-FR', 'image': image_object,
                      'mainEntityOfPage': {'@id': canonical + '#page'},
                      'author': {'@type': 'Organization', 'name': 'MénageUp', 'url': DOMAIN + '/qui-sommes-nous/'},
                      'publisher': {'@type': 'Organization', 'name': 'MénageUp', 'url': DOMAIN + '/',
                                    'logo': {'@type': 'ImageObject', 'url': DOMAIN + '/logo-v3.png'}},
                      'dateModified': guide['updated_at']})
        if guide.get('published_at'):
            graph[-1]['datePublished'] = guide['published_at']
    ld = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False).replace('</', '<\\/')
    article_meta = f'<meta property="article:modified_time" content="{guide["updated_at"]}">' if guide else ''
    if guide and guide.get('published_at'):
        article_meta += f'<meta property="article:published_time" content="{guide["published_at"]}">'
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{canonical}"><meta name="robots" content="index,follow,max-image-preview:large"><meta name="theme-color" content="#14336e">
<meta property="og:type" content="{'article' if guide else 'website'}"><meta property="og:site_name" content="MénageUp"><meta property="og:locale" content="fr_FR"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{DOMAIN}/{image}"><meta property="og:image:width" content="{w}"><meta property="og:image:height" content="{h}"><meta property="og:image:alt" content="{esc(alt)}">{article_meta}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{DOMAIN}/{image}"><meta name="twitter:image:alt" content="{esc(alt)}">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" href="/favicon.png" sizes="512x512"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="stylesheet" href="/assets/fonts.css"><link rel="stylesheet" href="/assets/realisations.css"><link rel="stylesheet" href="/assets/guides.css"><script type="application/ld+json">{ld}</script><script defer src="/assets/navigation-menu.js"></script><script defer src="/assets/guides.js"></script></head><body>{header(cta)}{body}{footer()}</body></html>
'''


def section_html(section):
    parts = [f'<section class="guide-section" id="{esc(section["id"])}"><h2>{esc(section["title"])}</h2>']
    parts += [f'<p>{esc(p)}</p>' for p in section.get('paragraphs', [])]
    for key, cls in [('bullets', ''), ('checklist', ' class="guide-checklist"')]:
        if section.get(key):
            parts.append('<ul' + cls + '>' + ''.join(f'<li>{esc(p)}</li>' for p in section[key]) + '</ul>')
    if section.get('table'):
        table = section['table']
        parts.append(f'<div class="table-scroll" tabindex="0" role="region" aria-label="Tableau : {esc(section["title"])}"><table><caption>{esc(section["title"])}</caption><thead><tr>')
        parts += [f'<th scope="col">{esc(p)}</th>' for p in table['headers']]
        parts.append('</tr></thead><tbody>')
        for row in table['rows']:
            cells = [f'<th scope="row">{esc(row[0])}</th>']
            cells += [f'<td>{esc(cell)}</td>' for cell in row[1:]]
            parts.append('<tr>' + ''.join(cells) + '</tr>')
        parts.append('</tbody></table></div>')
    return ''.join(parts) + '</section>'


def category(guide):
    return 'Chantier' if guide['audience'] == 'ent' else 'Logement'


def guide_page(g):
    path = HUB + g['slug'] + '/'
    cta = quote(path, g)
    crumbs = [('Accueil', '/'), ('Conseils', HUB), (g['title'], path)]
    words = len(re.findall(r'\S+', ' '.join(g['intro']) + json.dumps(g['sections'], ensure_ascii=False) + json.dumps(g['faq'], ensure_ascii=False)))
    minutes = max(1, round(words / 200))
    d = date.fromisoformat(g['updated_at'])
    months = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
    date_label = f'{d.day} {months[d.month - 1]} {d.year}'
    toc = ''.join(f'<li><a href="#{esc(s["id"])}">{esc(s["title"])}</a></li>' for s in g['sections'])
    with Image.open(ROOT / g['image']) as im:
        portrait = im.height > im.width
    image = image_tag(g['image'], g['image_alt'], '(max-width:700px) calc(100vw - 36px), (max-width:1050px) calc(100vw - 64px), 790px' if not portrait else '(max-width:360px) calc(100vw - 36px), 300px', True)
    figure_class = 'guide-figure portrait' if portrait else 'guide-figure'
    sections = ''.join(section_html(s) for s in g['sections'])
    checklist = g.get('quote_fields', [item for s in g['sections'] for item in s.get('checklist', [])])
    copy_box = ''
    if checklist:
        template = 'Bonjour MénageUp, voici ma demande :\n\n' + '\n'.join('- ' + item + '\n  À préciser :' for item in checklist) + '\n\nPhotos disponibles :\nTéléphone et créneau de rappel :'
        copy_box = f'''<section class="quote-helper" id="preparer-ma-demande"><p class="eyebrow">À compléter pour votre demande</p><h2>Préparez les informations utiles.</h2><p>Copiez cette trame et complétez-la avec votre situation avant de nous contacter.</p><label for="quote-template">Trame à compléter</label><textarea id="quote-template" readonly rows="8">{esc(template)}</textarea><button class="btn" type="button" data-copy-template hidden>Copier la trame</button><p class="copy-status" role="status" aria-live="polite"></p><a href="{esc(cta)}">Ouvrir le formulaire de devis ↗</a></section>'''
    faq = ''.join(f'<details><summary>{esc(q["question"])}</summary><p>{esc(q["answer"])}</p></details>' for q in g['faq'])
    sources = ''.join(f'<li><a href="{esc(s["url"])}">{esc(s["label"])}</a><p>{esc(s["context"])}</p></li>' for s in g.get('sources', []))
    related = ''.join(f'<a href="{esc(r["href"])}">{esc(r["label"])} ↗</a>' for r in g['related'])
    body = breadcrumbs(crumbs) + f'''<main id="contenu"><article class="wrap guide-layout"><header class="guide-heading"><p class="eyebrow">Conseils MénageUp · {category(g)} · Seine-et-Marne</p><h1>{esc(g['h1'])}</h1><p class="guide-meta">Par <a href="/qui-sommes-nous/">MénageUp</a> · Mise à jour <time datetime="{g['updated_at']}">{date_label}</time> · Environ {minutes} min de lecture</p><div class="guide-intro">{''.join('<p>' + esc(p) + '</p>' for p in g['intro'])}</div></header><aside class="guide-aside" aria-label="Repères de lecture"><details class="guide-toc" open><summary>Dans ce guide</summary><nav aria-label="Sommaire"><ol>{toc}</ol></nav></details><div class="aside-contact"><p>Vous préparez une intervention dans le 77 ?</p><a class="btn" href="{esc(cta)}">Parlons de votre besoin</a><a href="tel:+33648304965">06 48 30 49 65</a></div></aside><div class="guide-content"><figure class="{figure_class}">{image}<figcaption>{esc(g['image_caption'])}</figcaption></figure>{sections}{copy_box}<section class="guide-faq" id="questions"><h2>Vos questions pratiques.</h2>{faq}</section><section class="guide-sources" id="sources"><h2>Sources et repères.</h2><p>Ces ressources précisent les points d’organisation, de prévention ou de gestion des déchets évoqués dans le guide.</p><ul>{sources}</ul></section></div></article><section class="project-cta"><div class="wrap project-cta-grid"><div><h2>Une demande, un périmètre clair.</h2><p>Nous échangeons sur vos espaces, les accès et les opérations attendues. Le suivi de l’intervention et les photos avant et après permettent de faire le point avec vous.</p></div><a class="btn" href="{esc(cta)}">Demander un devis gratuit ↗</a></div></section><section class="related"><div class="wrap"><h2>Pour avancer dans votre projet.</h2><div class="related-links">{related}</div></div></section></main>'''
    return document(g['title'], g['description'], path, g['image'], g['image_alt'], crumbs, body, cta, g)


def guide_filters(count_label):
    choices = [('tous', 'Tous les conseils'), ('logement', 'Logement et débarras'), ('chantier', 'Travaux et base vie')]
    check = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m5 12 4 4L19 6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    options = ''.join(f'<div class="guide-filter-option" id="guide-option-{value}" role="option" aria-selected="{str(value == "tous").lower()}" data-value="{value}"><span>{label}</span>{check}</div>' for value, label in choices)
    return f'''<div class="guide-filters" hidden><span class="guide-filter-label" id="guide-category-label">Votre projet</span><div class="guide-filter-control"><button class="guide-filter-trigger" type="button" id="guide-category" role="combobox" aria-labelledby="guide-category-label guide-category-value" aria-controls="guide-category-options" aria-haspopup="listbox" aria-expanded="false" data-value="tous"><span id="guide-category-value">Tous les conseils</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 9 6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg></button><div class="guide-filter-options" id="guide-category-options" role="listbox" aria-labelledby="guide-category-label" hidden>{options}</div></div><p role="status" aria-live="polite" data-filter-status>{esc(count_label)}</p></div>'''


def hub_page(guides):
    title = 'Conseils nettoyage, débarras et chantier dans le 77 | MénageUp'
    description = 'Préparez votre nettoyage ou débarras en Seine-et-Marne : logement inhabité, remise en état après travaux et entretien des bases vie de chantier.'
    crumbs = [('Accueil', '/'), ('Conseils', HUB)]
    cards = []
    for g in guides:
        img = image_tag(g['image'], g['image_alt'], '(max-width:700px) calc(100vw - 36px), (max-width:1224px) calc((100vw - 90px) / 2), 567px')
        cards.append(f'''<a class="project-card guide-card" href="{HUB}{g['slug']}/" data-guide-card data-category="{category(g).lower()}"><div class="project-card-image">{img}</div><div class="project-card-copy"><p class="eyebrow">{category(g)} · Guide pratique</p><h2>{esc(g['h1'])}</h2><p>{esc(g['description'])}</p><span class="card-link">Lire le guide ↗</span></div></a>''')
    count_label = str(len(guides)) + (' guides disponibles' if len(guides) != 1 else ' guide disponible')
    body = breadcrumbs(crumbs) + f'''<main id="contenu"><div class="wrap"><section class="hub-hero"><p class="eyebrow">Conseils MénageUp · Seine-et-Marne</p><h1>Préparer les lieux.<br>Clarifier le besoin.</h1><p class="intro">Du logement longtemps inhabité à la base vie de chantier, ces guides vous aident à décrire les travaux de propreté, organiser les accès et préparer une demande précise.</p></section>{guide_filters(count_label)}</div><section class="wrap projects-grid" aria-label="Nos guides pratiques">{''.join(cards)}</section><section class="project-cta"><div class="wrap project-cta-grid"><div><h2>Votre situation mérite un échange.</h2><p>Décrivez votre besoin et votre commune. Nous étudions les opérations, l’état des lieux et les conditions d’intervention pour préparer le devis.</p></div><a class="btn" href="{esc(quote(HUB))}">Demander un devis gratuit ↗</a></div></section></main>'''
    return document(title, description, HUB, guides[0]['image'], guides[0]['image_alt'], crumbs, body, quote(HUB))


def main():
    guides = [g for file in FILES for g in json.loads((ROOT / file).read_text(encoding='utf-8'))]
    if len({g['slug'] for g in guides}) != len(guides):
        raise ValueError('Duplicate guide slug')
    script = (ROOT / 'assets/devis-context.js').read_text(encoding='utf-8')
    for g in guides:
        if not re.fullmatch(r'[a-z0-9-]+', g['slug']):
            raise ValueError('Invalid guide slug')
        date.fromisoformat(g['updated_at'])
        if g.get('published_at'):
            date.fromisoformat(g['published_at'])
        if not re.search(r'\b' + re.escape(g['service_code']) + r'\s*:', script):
            raise ValueError('Unknown quote service')
        ids = [s['id'] for s in g['sections']]
        if len(set(ids)) != len(ids) or any(not re.fullmatch('[a-z0-9-]+', i) for i in ids):
            raise ValueError('Invalid or duplicate section ID')
        for s in g['sections']:
            if s.get('table') and any(len(row) != len(s['table']['headers']) for row in s['table']['rows']):
                raise ValueError('Uneven table')
    outputs = {ROOT / 'conseils/index.html': hub_page(guides)}
    outputs.update({ROOT / 'conseils' / g['slug'] / 'index.html': guide_page(g) for g in guides})
    changed = {file for file, html in outputs.items() if not file.exists() or file.read_text(encoding='utf-8') != html}
    ns, ins = 'http://www.sitemaps.org/schemas/sitemap/0.9', 'http://www.google.com/schemas/sitemap-image/1.1'
    ET.register_namespace('', ns)
    ET.register_namespace('image', ins)
    tree = ET.parse(ROOT / 'sitemap.xml')
    root = tree.getroot()
    known = {node.find('{' + ns + '}loc').text: node for node in root}
    if len(known) != len(root):
        raise ValueError('Duplicate sitemap URL')
    for file in outputs:
        path = '/' + file.parent.relative_to(ROOT).as_posix() + '/'
        url = DOMAIN + path
        guide = next((g for g in guides if path == HUB + g['slug'] + '/'), None)
        images = [guide['image']] if guide else list(dict.fromkeys(g['image'] for g in guides))
        modified = guide['updated_at'] if guide else max(g['updated_at'] for g in guides)
        node = known.get(url)
        if node is None:
            node = ET.SubElement(root, '{' + ns + '}url')
            ET.SubElement(node, '{' + ns + '}loc').text = url
        if file in changed:
            lm = node.find('{' + ns + '}lastmod')
            if lm is None:
                lm = ET.SubElement(node, '{' + ns + '}lastmod')
            lm.text = modified
        for old in node.findall('{' + ins + '}image'):
            node.remove(old)
        for image in images:
            im = ET.SubElement(node, '{' + ins + '}image')
            ET.SubElement(im, '{' + ins + '}loc').text = DOMAIN + '/' + image
    ET.indent(tree, space='  ')
    for file in changed:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(outputs[file], encoding='utf-8', newline='\n')
    tree.write(ROOT / 'sitemap.xml', encoding='UTF-8', xml_declaration=True)
    print(f'{len(outputs)} advice pages built; {len(changed)} HTML files changed; {len(root)} sitemap URLs. No deployment.')


if __name__ == '__main__':
    main()
