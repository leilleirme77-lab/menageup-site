"""Build the original-style carousel from reviews supplied by the site owner.

No Google account/API access or invented dates. This is not a live reviews feed.
No self-serving AggregateRating/Review markup is added to the business.
"""
from datetime import date
from html import escape
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!-- REVIEWS:START -->', '<!-- REVIEWS:END -->'


def section(data):
    reviews = data['reviews']
    cards = []
    for review in reviews:
        author = escape(review['author'], quote=True)
        source = 'Extrait d’un avis Google' if review.get('excerpt') else 'Avis publié sur Google'
        cards.append(f'''<li class="rev" data-review-id="{escape(review['id'])}" data-review-author="{author}"><div class="stars" role="img" aria-label="{review['rating']} sur 5">{'★' * review['rating']}</div><blockquote><p>{escape(review['text'])}</p></blockquote><div class="by"><span class="av" aria-hidden="true">{escape(review['initials'])}</span><div><b>{author}</b><small>{source}</small></div></div></li>''')
    average = sum(review['rating'] for review in reviews) / len(reviews)
    rating = f'{average:g}'.replace('.', ',')
    return f'''{START}
<section class="band" id="avis" aria-labelledby="reviews-title"><div class="wrap">
<div class="band-head"><span class="eyebrow">Vos retours</span><h2 id="reviews-title" style="margin-top:12px">Ce que disent nos client·es.</h2></div>
<div class="reviews-carousel" data-review-carousel role="region" aria-label="Avis clients sur Google">
<div class="reviews-summary"><p class="reviews-summary-rating"><strong>{rating}/5</strong><span class="stars" role="img" aria-label="Note moyenne de {rating} sur 5">★★★★★</span><span>{len(reviews)} avis clients sur Google</span></p><a class="reviews-google-link" href="{escape(data['source_url'], quote=True)}" target="_blank" rel="noopener noreferrer" aria-label="Consulter les avis Google de MénageUp (nouvel onglet)">Lire les avis sur Google <span aria-hidden="true">↗</span></a></div>
<p class="reviews-sr" id="reviews-help">Les avis défilent en continu. Vous pouvez mettre le défilement en pause, parcourir les cartes au toucher ou utiliser les flèches du clavier, Début et Fin.</p>
<div class="marq" id="reviews-viewport" tabindex="0" aria-label="Parcourir les avis clients" aria-describedby="reviews-help" data-review-viewport><div class="track" id="revtrack" data-review-track><ul class="review-group" data-review-originals aria-label="Les {len(reviews)} avis clients">{''.join(cards)}</ul></div></div>
<div class="reviews-toolbar" data-review-toolbar hidden><p class="reviews-hint"><span class="reviews-hint-desktop">Survolez un avis pour le lire à votre rythme.</span><span class="reviews-hint-touch">Faites glisser les avis ou utilisez les flèches.</span></p><div class="reviews-controls"><button type="button" class="review-control review-play" data-review-play aria-pressed="false" aria-controls="reviews-viewport" aria-label="Mettre en pause le défilement des avis"><svg class="pause-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h3v14H7zm7 0h3v14h-3z"/></svg><svg class="play-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m8 5 11 7-11 7z"/></svg></button><button type="button" class="review-control" data-review-prev aria-controls="reviews-viewport" aria-label="Afficher l’avis précédent"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m14 6-6 6 6 6" stroke-linecap="round" stroke-linejoin="round"/></svg></button><button type="button" class="review-control" data-review-next aria-controls="reviews-viewport" aria-label="Afficher l’avis suivant"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m10 6 6 6-6 6" stroke-linecap="round" stroke-linejoin="round"/></svg></button></div></div>
<p class="reviews-sr" role="status" aria-live="polite" aria-atomic="true" data-review-status></p>
</div></div></section>
{END}'''


def main():
    data = json.loads((ROOT / 'content/google-reviews.json').read_text(encoding='utf-8'))
    date.fromisoformat(data['reviewed_on'])
    if not re.fullmatch(r'https://share\.google/[A-Za-z0-9]+', data['source_url']):
        raise ValueError('Expected confirmed Google profile URL')
    reviews = data['reviews']
    if not reviews or len({review['id'] for review in reviews}) != len(reviews):
        raise ValueError('Missing or duplicate reviews')
    for review in reviews:
        if not re.fullmatch('[a-z0-9-]+', review['id']) or not 1 <= review['rating'] <= 5:
            raise ValueError('Invalid review identity or rating')
        if re.search(r'€|\beuros?\b', review['text'], re.I):
            raise ValueError('Public monetary amounts are not authorised')
        if not review['author'].strip() or not review['text'].strip():
            raise ValueError('Incomplete review')
    file = ROOT / 'index.html'
    original = file.read_text(encoding='utf-8')
    if (START in original) != (END in original):
        raise ValueError('Incomplete review markers')
    if START in original:
        pattern = re.escape(START) + r'.*?' + re.escape(END)
    else:
        pattern = r'<section\b(?=[^>]*\bid=["\']avis["\'])[^>]*>.*?</section>'
    html, replacements = re.subn(pattern, lambda _: section(data), original, count=1, flags=re.S)
    if replacements != 1:
        raise ValueError('Expected the existing review section')
    for asset in ['<link rel="stylesheet" href="/assets/google-reviews.css">', '<script defer src="/assets/google-reviews.js"></script>']:
        if asset not in html:
            html = html.replace('</head>', asset + '\n</head>', 1)
    changed = html != original
    if changed:
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
    print(json.dumps({'reviews': len(reviews), 'homepage_changed': changed, 'published': False}))


if __name__ == '__main__':
    main()
