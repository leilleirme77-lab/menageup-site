"""Build reviewed local entry pages; one commune directory, no mass city pages.

Run after service/advice builders. Commune data comes from geo.api.gouv.fr.
Does not submit forms, access Google accounts, or publish.
"""
from pathlib import Path
from datetime import date
import json
import os
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

from build_guides import document, image_tag, breadcrumbs, esc
from seo_shared import with_sector_navigation

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://menageup.fr'
TODAY = date.fromisoformat(os.environ.get('MENAGEUP_CONTENT_DATE', date.today().isoformat())).isoformat()
TOURNAN = '/nettoyage-tournan-en-brie/'
ZONES = '/zones-intervention-seine-et-marne-77/'


def quote(path, service='autre', audience='part', city=''):
    params = dict(service=service, audience=audience, source=path)
    if city:
        params['ville'] = city
    return '/?' + urlencode(params) + '#devis'


def styled_document(title, description, path, image, alt, crumbs, body, cta):
    page = document(title, description, path, image, alt, crumbs, body, cta)
    page = page.replace(' aria-current="location"', '')
    page = page.replace('</head>', '<link rel="stylesheet" href="/assets/local-seo.css">'
                        '<script defer src="/assets/communes-77.js"></script></head>')
    return with_sector_navigation(page, path)


def tournan_page():
    cta = quote(TOURNAN, city='Tournan-en-Brie')
    services = [
        ('/nettoyage-logement-inoccupe-77/', 'Grand nettoyage de logement', 'Nettoyage de logements très sales ou restés fermés. Nous définissons les pièces et les surfaces à traiter, en tenant compte du mobilier à conserver.'),
        ('/debarras-maison-appartement-77/', 'Débarras et encombrants', 'Maison, appartement, cave ou garage : vous choisissez les objets à conserver et ceux à enlever. Nous préparons leur sortie, leur transport et leur destination.'),
        ('/nettoyage-fin-de-chantier-77/', 'Nettoyage après travaux', 'Dépoussiérage et nettoyage des surfaces après les travaux salissants. Si des gravats ou des matériaux restent à enlever, leur évacuation est précisée séparément au devis.'),
        ('/nettoyage-base-vie-chantier-77/', 'Entretien de bases vie', 'Bureaux de chantier, vestiaires, réfectoires et sanitaires : nous définissons avec vous les tâches et la fréquence selon les modules, les effectifs et les horaires du site.'),
        ('/menage-a-domicile-77/', 'Ménage à domicile', 'Un besoin régulier ou ponctuel, avec repassage éventuel. Les pièces, les priorités, la fréquence et les produits sont définis avec vous.'),
        ('/nettoyage-copropriete-77/', 'Parties communes d’immeuble', 'Halls, escaliers, ascenseurs et espaces communs pour syndics et copropriétés, selon un cahier des charges et un suivi convenus.'),
        ('/nettoyage-bureaux-commerces-77/', 'Bureaux et commerces', 'Locaux de travail, boutiques et sanitaires : surfaces, horaires, accès et consignes de fermeture permettent d’organiser l’entretien.'),
        ('/nettoyage-vitres-77/', 'Vitres et vitrines', 'Fenêtres, baies et vitrines accessibles : précisez les faces, dimensions, encadrements et traces particulières pour évaluer la prestation.'),
    ]
    cards = ''.join(f'<a class="local-service" href="{href}"><h3>{esc(title)}</h3><p>{esc(text)}</p><span>Voir la prestation <span aria-hidden="true">↗</span></span></a>' for href, title, text in services)
    hero = image_tag('assets/realisations/chatres-77610/sejour-apres.webp', 'Séjour remis en ordre après le grand nettoyage MénageUp à Châtres, près du secteur de Tournan-en-Brie', '(max-width:800px) calc(100vw - 36px), 550px', True)
    before = image_tag('assets/realisations/chatres-77610/sejour-avant.webp', 'Séjour avant notre grand nettoyage à Châtres, avec meubles conservés et surfaces encombrées', '(max-width:700px) calc(100vw - 36px), 550px')
    after = image_tag('assets/realisations/chatres-77610/sejour-apres.webp', 'Même séjour à Châtres après le nettoyage et la remise en ordre', '(max-width:700px) calc(100vw - 36px), 550px')
    questions = [
        ('Peut-on demander un débarras et un grand nettoyage à Tournan-en-Brie ?', 'Oui. Indiquez les pièces à nettoyer, les objets à conserver et ceux à enlever. Le devis détaille le débarras, la manutention, l’évacuation et le nettoyage des espaces libérés. Une visite peut être nécessaire pour évaluer un logement très encrassé.'),
        ('Intervenez-vous aussi à Gretz-Armainvilliers, Presles-en-Brie et Châtres ?', 'Oui, nous étudions les interventions dans ces communes et les autres secteurs du 77. Nous confirmons avec vous les accès, la fréquence et les disponibilités avant de fixer la prestation. Vous pouvez consulter les photos de notre grand nettoyage réalisé à Châtres.'),
        ('Les photos avant et après sont-elles transmises au client ?', 'Oui. Nous vous tenons informé avant et pendant l’intervention, puis vous transmettons les photos avant et après avec un bilan du travail réalisé. Nous expliquons les points traités et les éventuelles difficultés rencontrées, en préservant la confidentialité des lieux.'),
        ('Le crédit d’impôt est-il automatiquement applicable ?', 'Non. Il dépend de la prestation, de votre situation et des conditions du dispositif. La déclaration SAP et l’avance immédiate de MénageUp ne sont pas confirmées : aucun avantage fiscal n’est annoncé comme acquis. Le débarras et le nettoyage de locaux professionnels ne doivent pas être assimilés au ménage à domicile pour ce dispositif.'),
        ('Comment préparer un devis sans connaître la surface exacte ?', 'La commune, le type de lieu, les pièces concernées, l’état général et quelques photos suffisent pour commencer l’échange. Signalez les escaliers, le stationnement, les objets lourds et l’accès à l’eau. Une visite peut compléter ces informations avant le chiffrage.'),
    ]
    faq = ''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in questions)
    body = breadcrumbs([('Accueil', '/'), ('Nettoyage à Tournan-en-Brie', TOURNAN)]) + f'''
<main id="contenu"><section class="wrap local-hero"><div><p class="eyebrow">MénageUp · Tournan-en-Brie · 77220</p>
<h1>Nettoyage et débarras<br> à Tournan-en-Brie.</h1>
<p class="intro">MénageUp intervient à Tournan-en-Brie pour le ménage à domicile, le grand nettoyage, l’entretien des locaux et le débarras. Nous accompagnons les particuliers, les copropriétés et les entreprises, pour un passage ponctuel ou des prestations régulières.</p>
<p class="local-intro-note">Expliquez-nous ce qu’il faut nettoyer, enlever ou conserver. Nous vous proposons un devis détaillé et vous tenons informé jusqu’au bilan de l’intervention, avec des photos avant et après.</p>
<div class="local-actions"><a class="btn" href="{esc(cta)}">Décrire mon projet à Tournan</a><a href="tel:+33648304965">06 48 30 49 65</a></div></div>
<figure>{hero}<figcaption>Grand nettoyage réalisé par MénageUp à Châtres (77610), dans le secteur de la Brie.</figcaption></figure></section>
<section class="wrap local-section" id="prestations"><div class="local-section-heading"><p class="eyebrow">Selon votre besoin</p><h2>Nos prestations à Tournan-en-Brie.</h2><p>Une même demande peut combiner plusieurs étapes. L’enlèvement des objets, le nettoyage des surfaces et l’entretien régulier sont distingués au devis.</p></div><div class="local-service-grid">{cards}</div></section>
<section class="local-tint"><div class="wrap local-section"><p class="eyebrow">Des lieux et des accès différents</p><h2>Préparer l’intervention dans votre logement ou votre immeuble.</h2><div class="local-columns"><div><h3>Dans une maison ou un appartement</h3><p>Précisez les pièces concernées, le nombre de niveaux, les revêtements et le mobilier conservé. Tomettes, parquet, pierre ou vitrage traité demandent une méthode compatible avec le support. Le nettoyage ne répare ni une usure ni un dégât du bâtiment.</p><p>Pour une cave, un grenier ou un garage, indiquez les marches, les passages étroits et les objets lourds. La sortie des volumes est préparée avant de fixer les moyens et le planning.</p></div><div><h3>Dans des locaux professionnels ou des parties communes</h3><p>Indiquez les heures d’occupation, la personne qui ouvre les lieux, les espaces accessibles et les tâches attendues. Pour un syndic, un repérage par hall, cage d’escalier et espace commun aide à comparer les périmètres.</p><p>Sur un chantier, le contact sur place, les consignes de circulation, les modules et l’effectif permettent d’étudier le nettoyage de la base vie et les éventuels besoins de fin de travaux.</p></div></div></div></section>
<section class="wrap local-section"><p class="eyebrow">Une réalisation du secteur, documentée</p><h2>À Châtres : une habitation fermée depuis six ans.</h2><p class="local-lead">Le propriétaire a confirmé six ans d’inoccupation et la présence de rongeurs, d’oiseaux et de déjections sur place. MénageUp a réalisé un grand nettoyage et une remise en ordre, avec les meubles et équipements conservés : neuf heures d’intervention et trois intervenants pour ce chantier précis.</p>
<div class="local-pair"><figure>{before}<figcaption>Avant · séjour à Châtres.</figcaption></figure><figure>{after}<figcaption>Après · mêmes lieux, mobilier conservé.</figcaption></figure></div><p>Cette réalisation présente le grand nettoyage et la remise en ordre d’une habitation, avec le mobilier conservé. L’état et les besoins de votre logement sont évalués lors de notre échange.</p>
<a class="local-text-link" href="/realisations/grand-nettoyage-chatres-77610/">Voir les photos du séjour et de la cuisine à Châtres ↗</a>
<p>Pour un besoin d’enlèvement, découvrez aussi notre <a href="/realisations/debarras-exterieur-pontault-combault-77340/">débarras extérieur à Pontault-Combault</a> : les photos montrent le passage avant et après l’enlèvement des encombrants.</p></section>
<section class="local-tint"><div class="wrap local-section"><p class="eyebrow">Avant, pendant, après</p><h2>Un interlocuteur à chaque étape.</h2><ol class="local-steps"><li><h3>Décrire les lieux</h3><p>Vous nous indiquez la commune, les pièces concernées, leur état et les objets à conserver ou à enlever.</p></li><li><h3>Définir la prestation</h3><p>Un échange ou une visite permet de préciser les tâches, les conditions d’accès et la date d’intervention avant de valider le devis.</p></li><li><h3>Faire le point sur le résultat</h3><p>Vous recevez les photos avant et après et un bilan du travail réalisé. Si une découverte modifie les tâches prévues, nous en parlons avec vous.</p></li></ol><a href="https://share.google/d4WL0FlPcgTL4Hdfk" target="_blank" rel="noopener noreferrer">Consulter les avis sur notre fiche Google ↗</a></div></section>
<section class="wrap local-section"><p class="eyebrow">Tournan et la Brie environnante</p><h2>Votre demande dans le 77220 et les communes voisines.</h2><p>Nous étudions vos projets à Tournan-en-Brie, Gretz-Armainvilliers, Presles-en-Brie, Favières, Châtres et Chevry-Cossigny, ainsi que dans les autres communes du 77. Précisez le lieu et la fréquence souhaitée : nous convenons avec vous des modalités et du planning.</p><p>Notre siège social est à La Houssaye-en-Brie. Pour votre intervention à Tournan-en-Brie ou dans les communes voisines, vous disposez du même contact MénageUp.</p><a class="local-text-link" href="{ZONES}">Retrouver votre commune et les secteurs du 77 ↗</a><h2 class="local-faq-title">Vos questions à Tournan-en-Brie.</h2><div class="local-faq">{faq}</div></section>
<section class="project-cta"><div class="wrap project-cta-grid"><div><h2>Votre projet à Tournan commence ici.</h2><p>Grand nettoyage, débarras, entretien régulier ou besoin particulier : présentez votre situation. Nous étudions chaque demande de devis.</p></div><a class="btn" href="{esc(cta)}">Demander mon devis gratuit ↗</a></div></section></main>'''
    return styled_document('MénageUp à Tournan-en-Brie (77220) | Nettoyage et débarras', 'Nettoyage à Tournan-en-Brie : ménage, copropriétés, bureaux, grand nettoyage et débarras. Réalisations en photos dans le 77 et devis personnalisé.', TOURNAN, 'assets/realisations/chatres-77610/sejour-apres.webp', 'Séjour après une réalisation de grand nettoyage MénageUp à Châtres', [('Accueil', '/'), ('Nettoyage à Tournan-en-Brie', TOURNAN)], body, cta)


def zones_page(communes):
    groups = [
        ('Brie et secteur de Tournan', [('Tournan-en-Brie', '/nettoyage-tournan-en-brie/'), ('Ozoir-la-Ferrière', '/nettoyage-ozoir-la-ferriere/'), ('Roissy-en-Brie', '/nettoyage-roissy-en-brie/'), ('Pontault-Combault', '/nettoyage-pontault-combault/'), ('Brie-Comte-Robert', '/nettoyage-brie-comte-robert/')], 'La Houssaye-en-Brie, Châtres, Gretz-Armainvilliers, Presles-en-Brie, Fontenay-Trésigny et les communes environnantes peuvent être précisées dans votre demande.'),
        ('Marne-la-Vallée et nord-ouest du 77', [('Torcy', '/nettoyage-torcy/'), ('Chelles', '/nettoyage-chelles/'), ('Bussy-Saint-Georges', '/nettoyage-bussy-saint-georges/'), ('Champs-sur-Marne', '/nettoyage-champs-sur-marne/'), ('Noisiel', '/nettoyage-noisiel/'), ('Lagny-sur-Marne', '/nettoyage-lagny-sur-marne/'), ('Montévrain', '/nettoyage-montevrain/')], 'Vous pouvez aussi indiquer Serris, Meaux, Claye-Souilly, Mitry-Mory ou Villeparisis : le besoin et les conditions de déplacement sont étudiés avant confirmation.'),
        ('Melun et Sénart', [('Melun', '/nettoyage-melun/'), ('Savigny-le-Temple', '/nettoyage-savigny-le-temple/'), ('Combs-la-Ville', '/nettoyage-combs-la-ville/'), ('Moissy-Cramayel', '/nettoyage-moissy-cramayel/')], 'Pour Lieusaint, Cesson, Le Mée-sur-Seine, Dammarie-les-Lys et les autres communes, précisez l’adresse d’intervention, les accès et la fréquence souhaitée.'),
        ('Est et sud du département', [('Coulommiers', '/nettoyage-coulommiers/')], 'Provins, Nangis, La Ferté-sous-Jouarre, Fontainebleau, Montereau-Fault-Yonne et Nemours : décrivez votre projet. Le lieu, le volume, la récurrence et les moyens disponibles déterminent l’organisation possible.'),
    ]
    sectors = ''.join(f'<article class="local-sector"><h3>{esc(name)}</h3><div class="local-town-links">' + ''.join(f'<a href="{url}">{esc(town)}</a>' for town, url in links) + f'</div><p>{esc(text)}</p></article>' for name, links, text in groups)
    # Public administrative names/codes only, fetched from the official API.
    dataset = json.dumps(communes, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    cta = quote(ZONES)
    body = breadcrumbs([('Accueil', '/'), ('Seine-et-Marne : nos secteurs', ZONES)]) + f'''
<main id="contenu"><section class="wrap local-directory-hero"><p class="eyebrow">MénageUp · Seine-et-Marne · 77</p><h1>Nettoyage et débarras :<br> votre projet dans le 77.</h1><p class="intro">Retrouvez les pages de nos principaux secteurs et précisez votre commune pour une demande de devis. Entretien régulier, base vie, remise en état ou débarras : la prestation, les accès et le planning sont étudiés ensemble.</p><p>Depuis notre siège à La Houssaye-en-Brie, nous étudions vos demandes en Seine-et-Marne. Le lieu, la fréquence et les accès permettent de convenir des modalités d’intervention et du planning.</p></section>
<section class="wrap local-search" aria-labelledby="commune-title"><h2 id="commune-title">Dans quelle commune se trouve votre projet ?</h2><p>Saisissez le nom de votre commune ou son code postal pour préparer une demande adaptée à votre lieu d’intervention.</p><div data-commune-search hidden><label for="commune-search">Nom de commune ou code postal</label><input id="commune-search" type="search" placeholder="Ex. Tournan, Meaux ou 77610" autocomplete="off" maxlength="100" aria-describedby="commune-search-help"><p id="commune-search-help">Saisissez au moins deux caractères. Choisissez ensuite la commune pour ouvrir votre demande.</p><p data-commune-status role="status" aria-live="polite"></p><ul class="commune-results" data-commune-results></ul></div><noscript><p>Vous pouvez nous indiquer directement votre commune dans le <a href="{esc(cta)}">formulaire de demande de devis</a>.</p></noscript><script type="application/json" id="communes-77-data">{dataset}</script></section>
<section class="wrap local-section"><p class="eyebrow">Les pages de nos secteurs</p><h2>Un point de départ proche de votre besoin.</h2><div class="local-sector-grid">{sectors}</div></section>
<section class="local-tint"><div class="wrap local-section"><h2>Choisir la prestation avant de choisir un planning.</h2><div class="local-columns"><div><h3>Un logement à nettoyer ou à débarrasser</h3><p>Un entretien régulier et une habitation fermée depuis plusieurs années ne se préparent pas de la même manière. Indiquez les pièces, l’état, les éléments conservés et les objets à enlever.</p><div class="local-town-links"><a href="/menage-a-domicile-77/">Ménage à domicile</a><a href="/nettoyage-logement-inoccupe-77/">Grand nettoyage</a><a href="/debarras-maison-appartement-77/">Débarras de logement</a></div></div><div><h3>Un immeuble, des locaux ou un chantier</h3><p>Pour une copropriété ou des bureaux, précisez les surfaces et les fréquences. Pour le BTP, distinguez les modules de base vie, les locaux à livrer et les matériaux à évacuer.</p><div class="local-town-links"><a href="/nettoyage-copropriete-77/">Parties communes</a><a href="/nettoyage-bureaux-commerces-77/">Bureaux et commerces</a><a href="/nettoyage-base-vie-chantier-77/">Bases vie</a><a href="/debarras-chantier-77/">Débarras de chantier</a></div></div></div></div></section>
<section class="wrap local-section"><h2>Nos réalisations à Châtres et Pontault-Combault.</h2><p>Le <a href="/realisations/grand-nettoyage-chatres-77610/">grand nettoyage de Châtres (77610)</a> et le <a href="/realisations/debarras-exterieur-pontault-combault-77340/">débarras extérieur de Pontault-Combault (77340)</a> présentent nos photos avant et après, avec le contexte et le périmètre de chaque intervention.</p><p>Pour préparer votre projet, indiquez la commune exacte, le lieu à traiter, l’état général, la fréquence et les contraintes d’accès. Nous confirmons ensuite avec vous les tâches, les accès et le planning.</p><p class="local-source">Source du répertoire : <a href="https://geo.api.gouv.fr/decoupage-administratif/communes">API officielle de découpage administratif</a>, {len(communes)} communes référencées au 22 octobre 2026. Un code postal peut concerner plusieurs communes ; sélectionnez bien le nom correspondant à votre lieu d’intervention.</p></section>
<section class="project-cta"><div class="wrap project-cta-grid"><div><h2>Votre commune. Votre besoin.</h2><p>Présentez-nous votre nettoyage ou débarras en Seine-et-Marne. Nous examinons chaque demande pour définir un périmètre et un devis adaptés.</p></div><a class="btn" href="{esc(cta)}">Préparer ma demande ↗</a></div></section></main>'''
    return styled_document('Nettoyage et débarras en Seine-et-Marne : nos secteurs | MénageUp', 'Retrouvez votre commune du 77 et les prestations MénageUp : ménage, copropriétés, bureaux, bases vie, grand nettoyage et débarras sur devis.', ZONES, 'assets/realisations/chatres-77610/sejour-apres.webp', 'Réalisation de grand nettoyage MénageUp à Châtres, en Seine-et-Marne', [('Accueil', '/'), ('Nos secteurs dans le 77', ZONES)], body, cta)


def main():
    communes = json.loads((ROOT / 'content/communes-77.json').read_text(encoding='utf-8'))
    if not communes or len({c['code'] for c in communes}) != len(communes):
        raise ValueError('Invalid commune data')
    outputs = {TOURNAN: tournan_page(), ZONES: zones_page(communes)}
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    image_ns = 'http://www.google.com/schemas/sitemap-image/1.1'
    ET.register_namespace('', ns)
    ET.register_namespace('image', image_ns)
    tree = ET.parse(ROOT / 'sitemap.xml')
    root = tree.getroot()
    for path, html in outputs.items():
        target = ROOT / path.strip('/') / 'index.html'
        if target.exists() and target.read_text(encoding='utf-8') == html:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding='utf-8', newline='\n')
        node = next((x for x in root if x.findtext('{' + ns + '}loc') == DOMAIN + path), None)
        if node is None:
            node = ET.SubElement(root, '{' + ns + '}url')
            ET.SubElement(node, '{' + ns + '}loc').text = DOMAIN + path
        lastmod = node.find('{' + ns + '}lastmod')
        if lastmod is None:
            lastmod = ET.SubElement(node, '{' + ns + '}lastmod')
        lastmod.text = TODAY
        for old in node.findall('{' + image_ns + '}image'):
            node.remove(old)
        image = ET.SubElement(node, '{' + image_ns + '}image')
        ET.SubElement(image, '{' + image_ns + '}loc').text = DOMAIN + '/assets/realisations/chatres-77610/sejour-apres.webp'
    ET.indent(tree, space='  ')
    tree.write(ROOT / 'sitemap.xml', encoding='UTF-8', xml_declaration=True)
    print('Tournan page and commune directory built. No publication.')


if __name__ == '__main__':
    main()
