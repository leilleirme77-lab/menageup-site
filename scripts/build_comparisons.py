"""Shared immersive before/after cards. Builds local pages; does not deploy."""
from pathlib import Path
from html import escape as e
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'content/comparisons.json'
START = '<!-- COMPARISONS:START -->'
END = '<!-- COMPARISONS:END -->'
CSS = '<link rel="stylesheet" href="/assets/comparisons.css">'
JS = '<script src="/assets/comparisons.js" defer></script>'
CAROUSEL_JS = '<script src="/assets/realisations-carousel.js" defer></script>'
CAROUSEL_START = '<!-- REALISATIONS-CAROUSEL:START -->'
CAROUSEL_END = '<!-- REALISATIONS-CAROUSEL:END -->'


def comparison_items():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    for item in data:
        item['href'] = '/realisations/chantier-' + item['slug'].split('-', 1)[1] + '/'
    return data


def photo_info(file):
    file = file.lstrip('/')
    path = ROOT / file
    with Image.open(path) as image:
        width, height = image.size
    small = path.with_name(path.stem + '-640.webp')
    if not small.is_file():
        small = path
    with Image.open(small) as image:
        small_width = image.width
    return dict(small='/' + small.relative_to(ROOT).as_posix(), large='/' + file,
                smallWidth=small_width, width=width, height=height)


def case_comparison(case):
    pair = next(section for section in case['sections'] if section['layout'] == 'pair')
    return dict(slug=case['slug'], title=case['card_title'], description=case['card_summary'],
                city=case['city'], postal_code=case['postal_code'], category=case['service_code'],
                href='/realisations/' + case['slug'] + '/', retouched=False,
                avant=photo_info(pair['photos'][0]['file']), apres=photo_info(pair['photos'][1]['file']))


def comparison_card(item, detail_link=True, suffix=''):
    slug, title = item['slug'] + suffix, item['title']
    retouched = item.get('retouched', True)
    city = item.get('city')
    location = (city + ' · ' + item['postal_code']) if city and item.get('postal_code') else 'Intervention de chantier · lieu non précisé'
    note = 'Visuels retouchés' if retouched else ''
    images = []
    for side, cls in [('apres', 'mu-after'), ('avant', 'mu-before')]:
        photo = item[side]
        for key in ['small', 'large']:
            if not (ROOT / photo[key].lstrip('/')).is_file():
                raise ValueError('Missing comparison image: ' + photo[key])
        variants = f'{e(photo["small"])} {photo["smallWidth"]}w'
        if photo['small'] != photo['large']:
            variants += f', {e(photo["large"])} {photo["width"]}w'
        alt = title + ' — ' + ('avant' if side == 'avant' else 'après') + (' (visuel retouché)' if retouched else '')
        position = e(item.get('position_' + side, item.get('position', '50% 35%')))
        images.append(f'<img class="{cls}" src="{e(photo["small"])}" srcset="{variants}" sizes="(max-width:760px) 92vw, 580px" width="{photo["width"]}" height="{photo["height"]}" loading="lazy" decoding="async" style="object-position:{position}" alt="{e(alt)}" aria-hidden="{str(side == "avant").lower()}">')
    href = item.get('href') if detail_link else None
    action = 'Voir la réalisation' if href else 'Agrandir les deux photos'
    link_attrs = 'data-dossier' if href else 'data-enlarge'
    return f'''<article class="mu-comparison" data-comparison data-view="apres" data-title="{e(title)}" data-retouched="{str(retouched).lower()}" data-avant="{e(item['avant']['large'])}" data-apres="{e(item['apres']['large'])}">
<div class="mu-comparison-stage" id="photo-{e(slug)}">{''.join(images)}
<a class="mu-comparison-open" {link_attrs} href="{e(href or item['apres']['large'])}" aria-label="{action} : {e(title)}"></a>
<span class="mu-comparison-state" data-state aria-hidden="true">Après</span>{f'<span class="mu-comparison-provenance">{note}</span>' if note else ''}
<div class="mu-comparison-overlay"><span class="mu-comparison-location">{e(location)}</span><h3>{e(title)}</h3><p>{e(item.get('description',''))}</p><span class="mu-comparison-hint" data-hint>Survolez pour voir l’avant</span><span class="mu-comparison-action">{action} ↗</span></div>
<div class="mu-comparison-controls" role="group" aria-label="Vue de {e(title)}" hidden><button type="button" data-side="avant" aria-pressed="false" aria-controls="photo-{e(slug)}">Avant</button><button type="button" data-side="apres" aria-pressed="true" aria-controls="photo-{e(slug)}">Après</button></div>
</div></article>'''


def comparisons_section(preview=False):
    data = comparison_items()
    if preview:
        data = [data[0], data[-1]]
    cards = ''.join(comparison_card(item) for item in data)
    section_id = 'comparaisons' if preview else 'interventions-chantier'
    action = '<a class="btn" href="/realisations/#interventions-chantier">Voir les 8 vues de chantier ↗</a>' if preview else ''
    return f'''{START}
<section class="mu-comparisons" id="{section_id}" data-realisation-section="chantier" aria-labelledby="{section_id}-title"><div class="mu-comparisons-head"><div><span class="eyebrow">Remise en état</span><h2 id="{section_id}-title">Interventions de chantier.</h2><p>Intérieurs, circulations et abords : parcourez les différentes zones en avant / après.</p></div>{action}</div><p class="mu-comparisons-notice">Ces comparaisons comprennent des visuels retouchés. La localisation précise n’est pas renseignée.</p><div class="mu-comparisons-grid">{cards}</div></section>
{END}'''


def build_home():
    path = ROOT / 'index.html'
    html = path.read_text(encoding='utf-8')
    cases = json.loads((ROOT / 'content/realisations.json').read_text(encoding='utf-8'))['cases']
    items = [case_comparison(case) for case in cases] + comparison_items()
    cards = ''.join(comparison_card(item, suffix='-home') for item in items)
    carousel = f'''{CAROUSEL_START}
<div class="mu-realisation-carousel" data-realisation-carousel role="region" aria-roledescription="carrousel" aria-label="Nos réalisations avant et après">
<div class="mu-realisation-viewport" data-realisation-viewport id="realisations-defilantes">{cards}</div>
</div>
{CAROUSEL_END}'''
    if CAROUSEL_START in html:
        begin, end = html.index(CAROUSEL_START), html.index(CAROUSEL_END) + len(CAROUSEL_END)
        html = html[:begin] + carousel + html[end:]
    else:
        html, replaced = re.subn(r'<div class="real-proof-grid real-proof-grid--immersive">.*?</div>\s*(?=<div class="real-proof-foot">)', lambda _: carousel + '\n', html, count=1, flags=re.S)
        if replaced != 1:
            raise ValueError('Homepage realization cards marker missing')
    if START in html:
        begin, end = html.index(START), html.index(END) + len(END)
        html = html[:begin] + html[end:]
    html = html.replace('Photographies de nos prestations. Les prises de vue peuvent présenter des angles différents.',
                        'Photos avant / après. Les visuels retouchés sont signalés.')
    html = html.replace('Avant / après : survolez les photos pour comparer. Les visuels retouchés sont signalés.',
                        'Photos avant / après. Les visuels retouchés sont signalés.')
    if CSS not in html:
        html = html.replace('</head>', CSS + '\n</head>', 1)
    if JS not in html:
        html = html.replace('</body>', JS + '\n</body>', 1)
    if CAROUSEL_JS not in html:
        html = html.replace(JS, CAROUSEL_JS + '\n' + JS, 1)
    path.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    build_home()
    print('Immersive homepage cards built. No deployment.')
