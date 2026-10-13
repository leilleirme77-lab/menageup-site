"""Build reviewed service content as static, crawlable pages. Does not deploy."""
import html, json, os, re
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DOMAIN='https://menageup.fr'
DATE=date.fromisoformat(os.environ.get('MENAGEUP_CONTENT_DATE', date.today().isoformat())).isoformat()
def esc(value): return html.escape(str(value),quote=True)
def render(service):
    s=service;slug=s['slug'];canonical=DOMAIN+'/'+slug+'/'
    if not re.fullmatch(r'[a-z0-9-]+',slug):raise ValueError('Invalid service slug')
    image='/'+s['image'].lstrip('/');stem=image.removesuffix('.webp')
    if not (ROOT/image.lstrip('/')).is_file():raise ValueError(f'Missing image {image}')
    label={'basevie':'Bases vie de chantier','vitres':'Vitres et vitrines','commerce':'Commerces et boutiques','debarraschantier':'Débarras de chantier','debarras':'Débarras de logement','grandnettoyage':'Grand nettoyage'}[s['service_code']]
    short={'basevie':'Bases vie','vitres':'Vitres & vitrines','commerce':'Commerces','debarraschantier':'Débarras de chantier','debarras':'Débarras de logement','grandnettoyage':'Grand nettoyage'}[s['service_code']]
    audience=s.get('audience','ent')
    if audience not in ['part','ent','copro']:raise ValueError('Invalid audience')
    query=urlencode({'service':s['service_code'],'audience':audience,'source':'/'+slug+'/'})
    direct='/?'+query+'#devis'
    schema={'@context':'https://schema.org','@graph':[
      {'@type':'WebPage','@id':canonical+'#page','url':canonical,'name':s['title'],'description':s['description'],'inLanguage':'fr-FR','isPartOf':{'@id':DOMAIN+'/#website'},'mainEntity':{'@id':canonical+'#service'},'primaryImageOfPage':{'@type':'ImageObject','url':DOMAIN+image,'width':1536,'height':1024}},
      {'@type':'Service','@id':canonical+'#service','name':s['h1'],'url':canonical,'provider':{'@id':DOMAIN+'/#business'},'areaServed':{'@type':'AdministrativeArea','name':'Seine-et-Marne'},'image':DOMAIN+image},
      {'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Accueil','item':DOMAIN+'/'},{'@type':'ListItem','position':2,'name':label,'item':canonical}]}
    ]}
    benefits=''.join(f'<div class="benefit"><span class="number">0{i+1}</span><div><p class="benefit-title">{esc(x["title"])}</p><p>{esc(x["text"])}</p></div></div>' for i,x in enumerate(s['benefits']))
    scope=''.join(f'<article class="scope-card"><span class="number">0{i+1}</span><h3>{esc(x["title"])}</h3><p>{esc(x["text"])}</p></article>' for i,x in enumerate(s['scope']))
    boundaries=''.join(f'<li>{esc(t)}</li>' for t in s['boundaries'])
    process=''.join(f'<div class="process-item"><span class="number">ÉTAPE 0{i+1}</span><h3>{esc(x["title"])}</h3><p>{esc(x["text"])}</p></div>' for i,x in enumerate(s['process']))
    faq=''.join(f'<details><summary>{esc(x["question"])}</summary><p>{esc(x["answer"])}</p></details>' for x in s['faq'])
    towns=''.join(f'<a href="{esc(x["href"])}">{esc(x["label"])}</a>' for x in s['local_links'])
    related=''.join(f'<a href="{esc(x["href"])}">{esc(x["label"])}</a>' for x in s['related'])
    proof=None
    if s['service_code']=='grandnettoyage':
        proof={'href':'/realisations/grand-nettoyage-chatres-77610/','label':'Grand nettoyage à Châtres : voir l’avant / après'}
    elif s['service_code'] in ['debarras','debarraschantier']:
        proof={'href':'/realisations/debarras-exterieur-pontault-combault-77340/','label':'Débarras extérieur à Pontault-Combault : voir la réalisation'}
    if proof:related+=f'<a href="{proof["href"]}">{esc(proof["label"])}</a>'
    guides={
        'grandnettoyage':('nettoyer-logement-inhabite-depuis-longtemps','Préparer le nettoyage d’un logement longtemps inhabité'),
        'debarras':('debarras-puis-nettoyage-logement','Débarras puis nettoyage : organiser les deux étapes'),
        'debarraschantier':('nettoyage-apres-travaux-ou-evacuation-gravats','Après travaux : distinguer nettoyage et évacuation des gravats'),
        'basevie':('entretien-base-vie-chantier-cahier-des-charges','Entretien de base vie : préparer le cahier des charges'),
    }
    guide=guides.get(s['service_code'])
    if guide:related+=f'<a href="/conseils/{guide[0]}/">{esc(guide[1])}</a>'
    mobile_nav='''<details class="service-mobile-menu"><summary>Menu <span aria-hidden="true">☰</span></summary><nav aria-label="Navigation mobile"><a href="/#services">Nos prestations</a><a href="/realisations/">Nos réalisations</a><a href="/conseils/">Conseils</a><a href="#secteur">Votre secteur</a><a href="/qui-sommes-nous/">Qui sommes-nous</a><a href="tel:+33648304965">06 48 30 49 65</a></nav></details>'''
    fields='<div class="field full"><label for="ville">Commune de l’intervention</label><input id="ville" name="ville" type="text" autocomplete="address-level2" placeholder="Ex. Torcy, Melun, Meaux…" maxlength="100" required></div>'
    for field in s['fields']:
        name=esc(field['name']);labeltext=esc(field['label'])
        if field['type']=='select':
            inp=f'<select id="{name}" name="{name}">'+''.join(f'<option value="{esc(o["value"])}">{esc(o["label"])}</option>' for o in field['options'])+'</select>'
        else:
            fractional=name in ['volume','surface']
            maximum=500 if name=='modules' else 10000 if name in ['occupants','volume'] else 1000000
            inp=f'<input id="{name}" name="{name}" type="number" min="{0.01 if fractional else 1}" max="{maximum}" step="{0.01 if fractional else 1}" inputmode="{"decimal" if fractional else "numeric"}" placeholder="À préciser">'
        fields+=f'<div class="field"><label for="{name}">{labeltext}</label>{inp}</div>'
    return f'''<!doctype html>
<html lang="fr" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(s['title'])}</title><meta name="description" content="{esc(s['description'])}"><link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large"><meta name="theme-color" content="#14336E">
<meta property="og:type" content="website"><meta property="og:locale" content="fr_FR"><meta property="og:site_name" content="MénageUp"><meta property="og:title" content="{esc(s['title'])}"><meta property="og:description" content="{esc(s['description'])}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{DOMAIN+image}"><meta property="og:image:width" content="1536"><meta property="og:image:height" content="1024"><meta property="og:image:alt" content="{esc(s['image_alt'])}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{DOMAIN+image}"><meta name="twitter:image:alt" content="{esc(s['image_alt'])}">
<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" href="/favicon.png" sizes="512x512"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/services.css"><script defer src="/assets/devis-context.js"></script>
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('</','<\\/')}</script></head>
<body><a class="skip" href="#contenu">Aller au contenu</a>
<header class="topbar"><div class="wrap topbar-inner"><a class="brand" href="/" aria-label="MénageUp accueil"><img src="/logo-v3.png" alt="MénageUp" width="549" height="160"></a><nav class="desktop-nav" aria-label="Navigation principale"><a href="/#services">Nos prestations</a><a href="/realisations/">Réalisations</a><a href="/conseils/">Conseils</a><a href="#secteur">Votre secteur</a></nav><div class="nav-actions"><a class="phone" href="tel:+33648304965">06 48 30 49 65</a><a class="btn small" href="#preparer-devis">Demander un devis <span aria-hidden="true">↗</span></a>{mobile_nav}</div></div></header>
<main id="contenu"><div class="wrap"><nav class="breadcrumb" aria-label="Fil d’Ariane"><a href="/">Accueil</a><span aria-hidden="true">/</span><span>{esc(label)}</span></nav>
<section class="hero"><div class="hero-grid"><div class="hero-copy"><div class="eyebrow">{esc(s['eyebrow'])}</div><h1>{esc(s['h1'])}</h1><p class="intro">{esc(s['intro'])}</p><div class="hero-actions"><a class="btn" href="#preparer-devis">Parlons de votre besoin <span aria-hidden="true">↗</span></a><a class="btn secondary" href="tel:+33648304965">Nous appeler</a></div><p class="small-note">Une demande précise. Un devis adapté à vos espaces.</p></div>
<figure class="hero-photo"><img src="{image}" srcset="{stem}-640.webp 640w, {stem}-960.webp 960w, {image} 1536w" sizes="(max-width:700px) calc(100vw - 36px), (max-width:1224px) 48vw, 550px" width="1536" height="1024" fetchpriority="high" alt="{esc(s['image_alt'])}"><div class="photo-label"><strong>{esc(short)}</strong><span>SEINE-ET-MARNE · 77</span></div><figcaption>{esc(s['image_caption'])}</figcaption></figure></div></section>
<div class="benefits">{benefits}</div></div>
<section class="section" id="prestation"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Le détail de la prestation</div><h2>Les espaces à prendre en charge.</h2></div><p>Un entretien utile commence par un périmètre clair. Voici les besoins à préciser pour préparer votre demande.</p></div><div class="scope-grid">{scope}</div><aside class="boundaries"><h3>À préciser ensemble avant l’intervention</h3><ul>{boundaries}</ul></aside></div></section>
<section class="section process-band"><div class="wrap"><div class="section-head"><div><div class="eyebrow">Comment ça se passe</div><h2>Du besoin aux bons gestes.</h2></div><p>Votre lieu, vos contraintes et votre rythme guident l’organisation de la prestation.</p></div><div class="process-grid">{process}</div></div></section>
<section class="section customer-followup"><div class="wrap customer-followup-grid"><div><div class="eyebrow">Une relation suivie</div><h2>Vous restez informé.</h2></div><div><p>Nous échangeons avec vous avant l’intervention pour définir les tâches et les accès, puis nous vous tenons informé de son avancement. Les photos avant/après vous sont transmises pour montrer le travail réalisé et faire le point sur le résultat.</p><p>Un besoin particulier ou une situation difficile ? Décrivez votre projet : nous étudions chaque demande de devis.</p><div class="customer-proof-links"><a href="/realisations/">Nos réalisations en photos ↗</a><a href="https://share.google/d4WL0FlPcgTL4Hdfk" target="_blank" rel="noopener noreferrer">Consulter les avis Google ↗</a></div></div></div></section>
<section class="section quote-section" id="preparer-devis"><div class="wrap quote-grid"><div class="quote-copy"><div class="eyebrow">Votre demande</div><h2>Commençons par vos espaces.</h2><p>{esc(s['quote_intro'])}</p><div class="quote-contact">Vous préférez en parler directement ?<a href="tel:+33648304965">06 48 30 49 65</a></div></div><div class="quote-card"><h3>Préparer mon devis</h3><p class="form-intro">Précisez votre besoin, puis laissez vos coordonnées à l’étape suivante.</p><form data-quote-builder data-service="{s['service_code']}" data-audience="{audience}" action="/" method="get"><input type="hidden" name="service" value="{s['service_code']}"><input type="hidden" name="audience" value="{audience}"><input type="hidden" name="source" value="/{slug}/"><div class="field-grid">{fields}</div><button class="btn" type="submit">Continuer ma demande <span aria-hidden="true">→</span></button><p class="small-note">Les quantités approximatives suffisent pour commencer.</p></form><noscript><p><a href="{esc(direct)}">Accéder directement au formulaire de devis</a></p></noscript></div></div></section>
<section class="section" id="secteur"><div class="wrap area-grid"><div><div class="eyebrow">À vos côtés dans le 77</div><h2>Une intervention qui se prépare localement.</h2><p>{esc(s['area_intro'])}</p><div class="town-links">{towns}</div></div><div><div class="eyebrow" style="margin-bottom:25px">Vos questions</div><div class="faq-list">{faq}</div></div></div></section>
<section class="related"><div class="wrap"><h2>Un autre besoin à prévoir ?</h2><div class="related-links">{related}</div></div></section></main>
<footer class="footer"><div class="wrap footer-grid"><div><a class="brand" href="/"><img src="/logo-v3.png" alt="MénageUp" width="549" height="160" loading="lazy"></a><p>Vos espaces, notre exigence.<br>Nettoyage pour particuliers et professionnels en Seine-et-Marne.</p></div><nav class="footer-links" aria-label="Informations"><a href="/realisations/">Nos réalisations</a><a href="/conseils/">Conseils</a><a href="/qui-sommes-nous/">Qui sommes-nous</a><a href="/recrutement/">Rejoindre MénageUp</a><a href="/mentions-legales/">Mentions légales</a><a href="mailto:menageup@outlook.fr">Nous écrire</a></nav></div></footer>
<div class="mobile-cta"><a class="btn secondary" href="tel:+33648304965">Appeler</a><a class="btn" href="#preparer-devis">Préparer mon devis ↗</a></div>
</body></html>'''

def build():
    services=json.loads((ROOT/'content/services.json').read_text(encoding='utf-8'))
    additional=ROOT/'content/services-debarras.json'
    if additional.exists():services+=json.loads(additional.read_text(encoding='utf-8'))
    if len({s['slug'] for s in services})!=len(services):raise ValueError('Duplicate service slug')
    changed=set()
    for s in services:
        out=ROOT/s['slug']/'index.html';out.parent.mkdir(exist_ok=True);result=render(s)
        if not out.exists() or out.read_text(encoding='utf-8')!=result:
            changed.add(DOMAIN+'/'+s['slug']+'/')
            out.write_text(result,encoding='utf-8',newline='\n')
    ns='http://www.sitemaps.org/schemas/sitemap/0.9';image_ns='http://www.google.com/schemas/sitemap-image/1.1'
    ET.register_namespace('',ns);ET.register_namespace('image',image_ns)
    tree=ET.parse(ROOT/'sitemap.xml');root=tree.getroot();known={n.find('{'+ns+'}loc').text:n for n in root}
    for s in services:
        url=DOMAIN+'/'+s['slug']+'/'
        if url not in known:
            node=ET.SubElement(root,'{'+ns+'}url');ET.SubElement(node,'{'+ns+'}loc').text=url;ET.SubElement(node,'{'+ns+'}lastmod').text=DATE
        else:
            node=known[url]
            if url in changed:
                lastmod=node.find('{'+ns+'}lastmod')
                if lastmod is None:lastmod=ET.SubElement(node,'{'+ns+'}lastmod')
                lastmod.text=DATE
        for item in list(node.findall('{'+image_ns+'}image')):node.remove(item)
        img=ET.SubElement(node,'{'+image_ns+'}image');ET.SubElement(img,'{'+image_ns+'}loc').text=DOMAIN+'/'+s['image'].lstrip('/')
    ET.indent(tree,space='  ');tree.write(ROOT/'sitemap.xml',encoding='UTF-8',xml_declaration=True)
    print(f'{len(services)} reviewed services built; {len(root)} sitemap URLs. No deployment performed.')

if __name__=='__main__':build()
