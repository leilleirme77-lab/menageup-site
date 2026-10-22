"""Shared final markup, included before change detection by every page builder."""
import json
import re
from pathlib import Path
from html import escape

IDENTITY = json.loads((Path(__file__).resolve().parents[1] / 'content/company-location.json').read_text(encoding='utf-8'))


def company_identity(html):
    """Describe the company and its registered office, not fabricated city branches."""
    office = IDENTITY['registered_office']

    def enrich(value):
        if isinstance(value, list):
            for item in value:
                enrich(item)
        elif isinstance(value, dict):
            kinds = value.get('@type', [])
            kinds = [kinds] if isinstance(kinds, str) else kinds
            if value.get('@id') == 'https://menageup.fr/#business' and kinds:
                # No verified customer-facing establishment address: use Organization.
                # The separate Google Business profile and its address are untouched.
                value['@type'] = 'Organization'
                value['legalName'] = IDENTITY['legal_name']
                value['address'] = {'@type': 'PostalAddress', 'streetAddress': office['street'], 'postalCode': office['postal_code'], 'addressLocality': office['city'], 'addressCountry': office['country']}
                for field in ['openingHoursSpecification', 'openingHours', 'currenciesAccepted', 'paymentAccepted', 'priceRange']:
                    value.pop(field, None)
            for child in value.values():
                enrich(child)

    def update(match):
        data = json.loads(match.group(2))
        before = json.dumps(data, ensure_ascii=False)
        enrich(data)
        if before == json.dumps(data, ensure_ascii=False):
            return match.group(0)
        return match.group(1) + json.dumps(data, ensure_ascii=False, indent=2).replace('</', '<\\/') + match.group(3)

    html = re.sub(r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)', update, html, flags=re.S)
    if 'data-registered-office' not in html:
        address = escape(office['street'] + ', ' + office['postal_code'] + ' ' + office['city'])
        html = html.replace('</footer>', '<p class="site-registered-office" data-registered-office>Siège social : ' + address + '.</p></footer>', 1)
    return html


def with_sector_navigation(html, path):
    html = company_identity(html)
    path = '/' + path.strip('/')
    trust_path = '/ils-nous-font-confiance/'

    def partner_navigation(match):
        content = match.group(2)
        if trust_path not in content:
            active = ' aria-current="page"' if path == trust_path.rstrip('/') else ''
            link = '<a href="' + trust_path + '"' + active + '>Ils nous font confiance</a>'
            advice = re.search(r'<a\b[^>]*href=["\']/conseils/["\'][^>]*>', content)
            content = content[:advice.start()] + link + content[advice.start():] if advice else content + link
        return match.group(1) + content + match.group(3)

    html = re.sub(r'(<nav\b(?=[^>]*\bclass=["\'][^"\']*\b(?:mainnav|desktop-nav|mobile-links|navpanel)\b[^"\']*["\'])[^>]*>)(.*?)(</nav>)', partner_navigation, html, flags=re.S)
    if '</footer>' in html:
        links = []
        if path != '/nettoyage-tournan-en-brie':
            links.append('<a href="/nettoyage-tournan-en-brie/">Nettoyage à Tournan-en-Brie</a>')
        if path != '/zones-intervention-seine-et-marne-77':
            links.append('<a href="/zones-intervention-seine-et-marne-77/">Nos secteurs en Seine-et-Marne</a>')
        if path != trust_path.rstrip('/'):
            links.append('<a href="' + trust_path + '">Ils nous font confiance</a>')
        if links:
            group = '<div class="site-area-link" data-seo-zone-link>' + ' · '.join(links) + '</div>'
            if 'data-seo-zone-link' in html:
                html = re.sub(r'<div\b[^>]*data-seo-zone-link[^>]*>.*?</div>', lambda _: group, html, count=1, flags=re.S)
            else:
                html = html.replace('</footer>', group + '</footer>', 1)
    if '/assets/local-seo.css' not in html:
        html = html.replace('</head>', '<link rel="stylesheet" href="/assets/local-seo.css">\n</head>', 1)
    return html
