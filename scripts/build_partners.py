"""Build the confirmed partner gallery and the progressively enhanced home carousel.

Artwork is supplied by the owner. No fabricated reviews, agency addresses or links.
Add a partner to content/partners.json, then run this script before the final audit.
"""
from pathlib import Path
from datetime import date
import json
import os
import re
import xml.etree.ElementTree as ET
from PIL import Image

from build_guides import document, breadcrumbs, esc
from seo_shared import with_sector_navigation

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://menageup.fr'
PATH = '/ils-nous-font-confiance/'
TODAY = date.fromisoformat(os.environ.get('MENAGEUP_CONTENT_DATE', date.today().isoformat())).isoformat()
START, END = '<!-- PARTNERS:START -->', '<!-- PARTNERS:END -->'


def load_partners():
    partners = json.loads((ROOT / 'content/partners.json').read_text(encoding='utf-8'))
    if not partners or len({p['id'] for p in partners}) != len(partners):
        raise ValueError('Partner registry is empty or contains duplicate IDs')
    for partner in partners:
        with Image.open(ROOT / partner['logo']) as im:
            partner['width'], partner['height'] = im.size
    return partners


def logo(partner):
    return f'<div class="partner-logo"><img src="/{esc(partner["logo"])}" alt="{esc(partner["name"])}" width="{partner["width"]}" height="{partner["height"]}" loading="lazy" decoding="async"></div>'


def arrow(direction='right'):
    path = 'M19 12H5m7 7-7-7 7-7' if direction == 'left' else 'M5 12h14m-7-7 7 7-7 7'
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="{path}" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def home_section(partners):
    slides = ''.join(f'<li class="partner-slide partner-slide--{esc(p["id"])}' + (' partner-slide--dark' if p['background'] == 'dark' else '') + (' partner-slide--background-crop' if p.get('display_fit') == 'background-crop' else '') + f'" data-partner-name="{esc(p["name"])}">{logo(p)}</li>' for p in partners)
    return f'''{START}
<section class="trust-section" id="confiance" aria-labelledby="trust-title"><div class="wrap">
<div class="trust-heading"><div><span class="eyebrow">Nos partenaires</span><h2 id="trust-title">Ils nous font confiance.</h2></div><a class="trust-page-link" href="{PATH}">Découvrir nos partenaires {arrow()}</a></div>
<div class="partner-carousel" data-partner-carousel role="region" aria-roledescription="carrousel" aria-label="Les partenaires de MénageUp">
<p class="partner-sr" id="partner-help">Faites défiler les logos au toucher ou avec les flèches du clavier. La touche Début revient au premier groupe et Fin affiche le dernier.</p>
<ul class="partner-track" id="partner-track" tabindex="0" aria-label="Logos de nos partenaires" aria-describedby="partner-help" data-partner-track>{slides}</ul>
<div class="partner-toolbar" data-partner-toolbar hidden><div class="partner-pagination" aria-label="Choisir un groupe de partenaires" data-partner-pagination></div><div class="partner-controls">
<button type="button" class="partner-control partner-play" data-partner-play aria-pressed="false" aria-controls="partner-track" aria-label="Mettre en pause le défilement automatique des partenaires"><svg class="pause-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h3v14H7zm7 0h3v14h-3z"/></svg><svg class="play-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m8 5 11 7-11 7z"/></svg></button>
<button type="button" class="partner-control" data-partner-prev aria-controls="partner-track" aria-label="Afficher les partenaires précédents">{arrow('left')}</button><button type="button" class="partner-control" data-partner-next aria-controls="partner-track" aria-label="Afficher les partenaires suivants">{arrow()}</button>
</div></div><p class="partner-sr" data-partner-status role="status" aria-live="polite" aria-atomic="true"></p></div></div></section>
{END}'''


def partners_page(partners):
    cards = ''.join(f'<li class="partners-gallery-card partners-gallery-card--{esc(p["id"])}"><div class="partners-gallery-logo' + (' partners-gallery-logo--dark' if p['background'] == 'dark' else '') + f'">{logo(p)}</div><h2>{esc(p["name"])}</h2><p>{esc(p["sector"])}</p></li>' for p in partners)
    cta = '/?service=autre&amp;audience=ent&amp;source=%2Fils-nous-font-confiance%2F#devis'
    body = breadcrumbs([('Accueil', '/'), ('Ils nous font confiance', PATH)]) + f'''
<main id="contenu"><section class="wrap partners-intro"><div><p class="eyebrow">MénageUp · Nos partenaires</p><h1>Ils nous font confiance.</h1><p class="intro">Des professionnels du bâtiment, de l’immobilier et de la restauration à nos côtés. Découvrez les partenaires avec lesquels nous collaborons.</p></div><aside class="partners-aside"><p class="eyebrow">Une relation qui se construit</p><h2>Du premier échange<br>au résultat.</h2><p>Un besoin bien compris, une intervention organisée et un suivi clair : c’est ainsi que nous travaillons avec nos clients et nos partenaires.</p></aside></section>
<section class="wrap partners-gallery" aria-label="Les partenaires présentés par MénageUp"><ul class="partners-gallery-grid">{cards}</ul></section>
<section class="partners-editorial"><div class="wrap"><div class="partners-editorial-heading"><p class="eyebrow">Des métiers différents, une même attention</p><h2>Des lieux propres.<br>Des projets qui avancent.</h2><p>Nos collaborations réunissent plusieurs univers professionnels. Pour chaque demande, nous clarifions les espaces concernés, les accès et les tâches attendues avant de préparer le devis. Voici les besoins auxquels nos prestations peuvent répondre.</p></div><div class="partners-sectors">
<article class="partners-sector"><p class="eyebrow">Bâtiment</p><h3>Accompagner les étapes du chantier.</h3><p>Entretien de base vie, enlèvement d’encombrants ou nettoyage après travaux : chaque opération est distinguée pour préparer les moyens et le passage des équipes.</p><a href="/nettoyage-fin-de-chantier-77/">Le nettoyage après travaux ↗</a></article>
<article class="partners-sector"><p class="eyebrow">Immobilier</p><h3>Préparer la prochaine occupation.</h3><p>Avant un état des lieux, un emménagement ou après une période d’inoccupation : nous étudions la remise en propreté et les éventuels besoins de débarras.</p><a href="/nettoyage-etat-des-lieux-77/">La remise en propreté d’un logement ↗</a></article>
<article class="partners-sector"><p class="eyebrow">Commerces</p><h3>Tenir compte de votre activité.</h3><p>Surfaces accessibles, espaces de vente, vitrines et sanitaires : les tâches et les horaires d’intervention sont définis avec vous, selon l’utilisation des lieux.</p><a href="/nettoyage-commerces-77/">L’entretien des commerces ↗</a></article>
</div></div></section>
<section class="wrap partners-followup"><div class="partners-followup-heading"><p class="eyebrow">La communication fait partie du service</p><h2>Vous savez ce qui est prévu.<br>Vous voyez ce qui est fait.</h2><p>Nous vous tenons informé avant et pendant la prestation, puis faisons le point avec vous sur le résultat.</p></div><ol class="partners-followup-list"><li><h3>Un échange sur le besoin</h3><p>Les espaces, les accès, les éléments à conserver et les priorités sont précisés avant de valider la prestation.</p></li><li><h3>Un point pendant l’intervention</h3><p>Vous disposez d’un contact MénageUp. Si une découverte modifie les tâches prévues, nous en parlons avec vous.</p></li><li><h3>Les photos et le bilan</h3><p>Les vues avant et après et un retour sur le travail réalisé vous permettent de suivre le résultat de l’intervention.</p></li></ol><a href="/realisations/">Voir nos réalisations photographiées à Châtres et Pontault-Combault ↗</a></section>
<section class="project-cta"><div class="wrap project-cta-grid"><div><h2>Un besoin de nettoyage<br>ou un projet de collaboration ?</h2><p>Présentez votre activité, la commune et les espaces concernés. Nous prenons le temps d’étudier votre demande.</p></div><a class="btn" href="{cta}">Parlons de votre projet ↗</a></div></section></main>'''
    html = document('Ils nous font confiance : nos partenaires | MénageUp', 'Découvrez les partenaires de MénageUp dans le bâtiment, l’immobilier et la restauration, ainsi que notre façon de suivre chaque intervention.', PATH, 'hero.jpg', 'Illustration d’un intérieur entretenu', [('Accueil', '/'), ('Ils nous font confiance', PATH)], body, '/?service=autre&audience=ent&source=%2Fils-nous-font-confiance%2F#devis')
    html = html.replace(' aria-current="location"', '').replace('</head>', '<link rel="stylesheet" href="/assets/partners.css"></head>')
    def schema(match):
        graph = json.loads(match.group(1))
        page = graph['@graph'][0]
        page['@type'] = 'CollectionPage'
        page['mainEntity'] = {'@type': 'ItemList', 'name': 'Partenaires de MénageUp', 'numberOfItems': len(partners), 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': p['name'], 'image': DOMAIN + '/' + p['logo']} for i, p in enumerate(partners)]}
        return '<script type="application/ld+json">' + json.dumps(graph, ensure_ascii=False).replace('</', '<\\/') + '</script>'
    html = re.sub(r'<script type="application/ld\+json">(.*?)</script>', schema, html, count=1, flags=re.S)
    return with_sector_navigation(html, PATH)


def main():
    partners = load_partners()
    changed = []
    home_file = ROOT / 'index.html'
    home = home_file.read_text(encoding='utf-8')
    if START not in home or END not in home:
        raise ValueError('Home partner placement markers are missing')
    updated = re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda _: home_section(partners), home, count=1, flags=re.S)
    for asset in ['<link rel="stylesheet" href="/assets/partners.css">', '<script defer src="/assets/partners.js"></script>']:
        if asset not in updated:
            updated = updated.replace('</head>', asset + '\n</head>', 1)
    if updated != home:
        home_file.write_text(updated, encoding='utf-8')
        changed.append('/')
    target = ROOT / PATH.strip('/') / 'index.html'
    page = partners_page(partners)
    if not target.exists() or target.read_text(encoding='utf-8') != page:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding='utf-8')
        changed.append(PATH)
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    image_ns = 'http://www.google.com/schemas/sitemap-image/1.1'
    ET.register_namespace('', ns)
    ET.register_namespace('image', image_ns)
    tree = ET.parse(ROOT / 'sitemap.xml')
    entries = {node.findtext('{' + ns + '}loc'): node for node in tree.getroot()}
    for path in ['/', PATH]:
        node = entries.get(DOMAIN + path)
        if node is None:
            node = ET.SubElement(tree.getroot(), '{' + ns + '}url')
            ET.SubElement(node, '{' + ns + '}loc').text = DOMAIN + path
        if path in changed:
            lastmod = node.find('{' + ns + '}lastmod')
            if lastmod is None:
                lastmod = ET.SubElement(node, '{' + ns + '}lastmod')
            lastmod.text = TODAY
        if path == PATH:
            for old in list(node.findall('{' + image_ns + '}image')):
                node.remove(old)
            for p in partners:
                image = ET.SubElement(node, '{' + image_ns + '}image')
                ET.SubElement(image, '{' + image_ns + '}loc').text = DOMAIN + '/' + p['logo']
    ET.indent(tree, space='  ')
    tree.write(ROOT / 'sitemap.xml', encoding='UTF-8', xml_declaration=True)
    print(json.dumps({'partners': len(partners), 'changed': changed}, ensure_ascii=False))


if __name__ == '__main__':
    main()
