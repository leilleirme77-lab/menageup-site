"""Local SEO release checks. No network requests and no form submissions.

Requires Python 3, beautifulsoup4, Pillow and Node.js on PATH.
Usage: python scripts/audit_site.py --root . --output /path/outside/site/audit.json
Without --output, JSON goes to stdout. A short summary always goes to stderr.
Exit codes: 0 no blocking errors, 1 site errors, 2 incomplete audit/tool failure.
Warnings do not establish indexation, ranking or Core Web Vitals performance.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

try:
    from bs4 import BeautifulSoup
    from PIL import Image
except ImportError as exc:
    print(json.dumps({'status': 'incomplete', 'error': f'Missing dependency: {exc.name}'}))
    raise SystemExit(2)


def nodes(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from nodes(item)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, help='Write machine-readable JSON here')
    args = parser.parse_args()
    root = args.root.resolve()
    issues = []
    issue_keys = set()
    pages = {}
    scripts = {}
    images = {}
    stats = Counter()
    incomplete = False

    def issue(level, code, page, detail):
        key = (level, code, page, detail)
        if key not in issue_keys:
            issue_keys.add(key)
            issues.append(dict(level=level, code=code, page=page, detail=detail))

    def finish():
        counts = Counter(x['level'] for x in issues)
        status = 'incomplete' if incomplete else 'fail' if counts['error'] else 'pass'
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'root': str(root), 'status': status, 'errors': counts['error'],
            'warnings': counts['warning'], 'statistics': dict(stats),
            'issues': issues, 'pages': list(pages), 'images': list(images.values()),
            'limits': [
                'Local source validation only; no HTTP, Googlebot, indexing or GSC assertions.',
                'JavaScript syntax checked without executing application or submitting forms.',
                'No browser layout, accessibility completeness or Core Web Vitals measurement.',
                'Schema checks cover explicit invariants, not every schema.org or Google requirement.',
                'A passing audit does not validate commercial claims or authorize deployment.',
            ],
        }
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload + '\n', encoding='utf-8')
        else:
            print(payload)
        print(f"SEO {status.upper()}: {stats['sitemap_urls']} sitemap URLs, {stats['html_pages']} HTML pages, {counts['error']} errors, {counts['warning']} warnings.", file=sys.stderr)
        return 2 if incomplete else 1 if counts['error'] else 0

    try:
        sitemap = ET.parse(root / 'sitemap.xml').getroot()
    except (OSError, ET.ParseError) as exc:
        issue('error', 'sitemap_unreadable', 'sitemap.xml', str(exc))
        return finish()
    entries = sitemap.findall('{*}url')
    urls = [entry.findtext('{*}loc', '').strip() for entry in entries]
    stats['sitemap_urls'] = len(urls)
    if not urls:
        issue('error', 'empty_sitemap', 'sitemap.xml', 'No URL entries found.')
        return finish()
    first = urlparse(urls[0])
    origin = f'{first.scheme}://{first.netloc}'
    home_url = origin + '/'
    sitemap_set = set(urls)
    for url, count in Counter(urls).items():
        if count > 1:
            issue('error', 'duplicate_sitemap_url', url, f'{count} entries')

    def local_path(value, context=home_url):
        resolved = urlparse(urljoin(context, value))
        if resolved.scheme not in ('http', 'https') or resolved.netloc != first.netloc:
            return None, resolved
        path = (root / unquote(resolved.path).lstrip('/')).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            issue('error', 'path_outside_root', context, 'Local URL resolves outside site root.')
            return None, resolved
        if resolved.path.endswith('/') or path.is_dir():
            path /= 'index.html'
        return path, resolved

    robot = RobotFileParser()
    robots_path = root / 'robots.txt'
    if robots_path.exists():
        robot.parse(robots_path.read_text(encoding='utf-8-sig').splitlines())
    else:
        robot.parse([])
        issue('warning', 'robots_missing', 'robots.txt', 'No local robots.txt file.')

    # Sitemap pages plus published local HTML catch broken links on unsitemapped pages too.
    local_html = set()
    for file in root.rglob('*.html'):
        parts = file.relative_to(root).parts
        if any(p.startswith('.') or p in {'node_modules', 'scripts', 'outils'} for p in parts):
            continue
        local_html.add(file.resolve())
    file_to_url = {}
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.netloc != first.netloc or parsed.query or parsed.fragment:
            issue('error', 'sitemap_url_not_canonical_shape', url, 'Expected same-host HTTPS URL without query/fragment.')
        path, _ = local_path(url)
        if path is None or not path.is_file():
            issue('error', 'sitemap_target_missing', url, 'No corresponding local HTML file.')
            continue
        file_to_url[path] = url
        local_html.add(path)
        if not robot.can_fetch('Googlebot', url):
            issue('error', 'robots_blocks_sitemap_page', url, 'Googlebot disallowed by local robots.txt.')
    for path in local_html:
        relative = path.relative_to(root).as_posix()
        file_to_url.setdefault(path, urljoin(home_url, relative[:-10] if relative.endswith('index.html') else relative))
    for path in sorted(local_html):
        url = file_to_url[path]
        try:
            pages[url] = BeautifulSoup(path.read_text(encoding='utf-8-sig'), 'html.parser')
        except (OSError, UnicodeError) as exc:
            issue('error', 'html_unreadable', url, str(exc))
    stats['html_pages'] = len(pages)
    home = pages.get(home_url)
    valid_services = set()
    if home:
        valid_services = {n.get('value') for n in home.select('input[name="prestations"][value], select[name="prestations"] option[value]') if n.get('value')}
    titles = defaultdict(list)
    descriptions = defaultdict(list)
    inlinks = defaultdict(set)

    def asset(value, context, kind):
        path, parsed = local_path(value, context)
        if path is None:
            return None
        if not path.is_file():
            issue('error', 'missing_' + kind, context, parsed.path)
            return None
        return path

    def image_check(value, context):
        path = asset(value, context, 'image')
        if path is None or str(path) in images:
            return
        record = {'path': path.relative_to(root).as_posix(), 'bytes': path.stat().st_size}
        try:
            if path.suffix.lower() == '.svg':
                ET.parse(path)
                record['format'] = 'SVG'
            else:
                with Image.open(path) as im:
                    record.update(width=im.width, height=im.height, format=im.format)
                    im.verify()
            images[str(path)] = record
        except (OSError, ValueError, ET.ParseError) as exc:
            issue('error', 'invalid_image', context, f'{record["path"]}: {type(exc).__name__}')

    def add_script(code, context, module=False):
        digest = hashlib.sha256((str(module) + code).encode()).hexdigest()
        scripts.setdefault(digest, {'code': code, 'module': module, 'pages': []})['pages'].append(context)

    for url, soup in pages.items():
        listed = url in sitemap_set
        robot_tags = soup.select('meta[name="robots"],meta[name="googlebot"]')
        noindex = any('noindex' in n.get('content', '').lower().replace(',', ' ').split() for n in robot_tags)
        if listed and noindex:
            issue('error', 'noindex_sitemap_page', url, 'Sitemap page has a noindex directive.')
        if not listed and not noindex:
            issue('warning', 'indexable_html_outside_sitemap', url, 'Local HTML is not in sitemap and has no noindex.')
        title_nodes = soup.select('title')
        if len(title_nodes) != 1 or not title_nodes[0].get_text(strip=True):
            issue('error', 'invalid_title', url, 'Expected one nonempty title.')
        elif listed:
            titles[title_nodes[0].get_text(strip=True)].append(url)
        if listed:
            desc = soup.select('meta[name="description"]')
            if len(desc) != 1 or not desc[0].get('content', '').strip():
                issue('error', 'invalid_description', url, 'Expected one nonempty meta description.')
            else:
                descriptions[desc[0]['content'].strip()].append(url)
            canon = soup.select('link[rel~="canonical"]')
            if len(canon) != 1 or canon[0].get('href') != url:
                issue('error', 'invalid_canonical', url, 'Expected one self-referencing absolute canonical matching sitemap.')
            if len(soup.select('h1')) != 1 or not soup.h1.get_text(strip=True):
                issue('error', 'invalid_h1', url, 'Expected one nonempty H1.')
        if not soup.select_one('meta[name="viewport"]'):
            issue('warning', 'viewport_missing', url, 'No viewport declaration.')
        ids = [n['id'] for n in soup.select('[id]')]
        for value, count in Counter(ids).items():
            if count > 1:
                issue('error', 'duplicate_html_id', url, value)
        for anchor in soup.select('a[href]'):
            path, parsed = local_path(anchor['href'], url)
            if path is None:
                continue
            stats['local_links'] += 1
            if not path.is_file():
                issue('error', 'broken_internal_link', url, parsed.path)
                continue
            target_url = file_to_url.get(path)
            if target_url and target_url != url:
                inlinks[target_url].add(url)
            target = pages.get(target_url)
            if parsed.fragment and not parsed.fragment.startswith(':~:text=') and target:
                fragment = unquote(parsed.fragment)
                if not target.find(id=fragment) and not target.find('a', attrs={'name': fragment}):
                    issue('error', 'broken_internal_anchor', url, parsed.path + '#' + fragment)
            query = parse_qs(parsed.query)
            if parsed.fragment == 'devis':
                for key in ('service', 'prestation', 'prestations'):
                    for value in query.get(key, []):
                        stats['qualified_devis_links'] += 1
                        if value not in valid_services:
                            issue('error', 'unknown_devis_service', url, f'{key}={value} is absent from home prestations controls.')
                for source in query.get('source', []):
                    source_parsed = urlparse(source)
                    if not source.startswith('/') or source.startswith('//') or source_parsed.netloc or source_parsed.scheme or source_parsed.query or source_parsed.fragment:
                        issue('error', 'invalid_devis_source', url, 'source must be a same-origin pathname.')
                for details in query.get('details', []):
                    try:
                        decoded = json.loads(details)
                        if not isinstance(decoded, (dict, list)):
                            raise ValueError('Expected structured qualification details.')
                    except ValueError:
                        issue('error', 'invalid_devis_details', url, 'details is not a JSON object or array.')
        for img in soup.select('img'):
            stats['img_elements'] += 1
            if not img.get('src'):
                issue('error', 'image_src_missing', url, 'img has no fallback src.')
            else:
                image_check(img['src'], url)
            if not img.has_attr('alt'):
                issue('warning', 'image_alt_missing', url, img.get('src', ''))
            elif re.search(r'\b(todo|placeholder|à compléter|lorem ipsum)\b', img['alt'], re.I):
                issue('warning', 'image_alt_placeholder', url, img.get('src', ''))
            for dimension in ('width', 'height'):
                if not re.fullmatch(r'[1-9][0-9]*', str(img.get(dimension, ''))):
                    issue('warning', 'image_dimension_missing', url, f'{img.get("src", "")}: {dimension}')
            if img.get('srcset') and not img['srcset'].lstrip().startswith('data:'):
                for candidate in img['srcset'].split(','):
                    parts = candidate.strip().split()
                    if parts:
                        image_check(parts[0], url)
        for source in soup.select('picture source[srcset]'):
            if not source['srcset'].lstrip().startswith('data:'):
                for candidate in source['srcset'].split(','):
                    parts = candidate.strip().split()
                    if parts:
                        image_check(parts[0], url)
        for meta in soup.select('meta[property="og:image"], meta[name="twitter:image"],meta[property="twitter:image"]'):
            if meta.get('content'):
                image_check(meta['content'], url)
        for link in soup.select('link[href]'):
            rel = link.get('rel', [])
            if any(x in rel for x in ('stylesheet', 'icon', 'apple-touch-icon', 'preload')):
                asset(link['href'], url, 'asset')
        for script in soup.select('script'):
            type_ = script.get('type', '').lower().strip()
            if type_ == 'application/ld+json':
                try:
                    data = json.loads(script.string or script.get_text())
                except (ValueError, TypeError):
                    issue('error', 'jsonld_invalid_json', url, 'Structured data is not valid JSON.')
                    continue
                if not isinstance(data, (dict, list)):
                    issue('error', 'jsonld_invalid_root', url, 'Structured data must be an object or array.')
                    continue
                stats['jsonld_blocks'] += 1
                for node in nodes(data):
                    types = node.get('@type', [])
                    types = types if isinstance(types, list) else [types]
                    if 'CleaningService' in types:
                        issue('error', 'schema_unknown_cleaningservice', url, 'CleaningService is not a documented schema.org type; retain an appropriate valid type.')
                    if 'servicePhone' in node:
                        value = node['servicePhone']
                        if not isinstance(value, dict) or value.get('@type') != 'ContactPoint' or not value.get('telephone'):
                            issue('error', 'schema_servicephone_invalid', url, 'servicePhone must be a ContactPoint with telephone.')
                    if 'LocalBusiness' in types:
                        parent = node.get('parentOrganization', {})
                        if isinstance(parent, dict) and parent.get('@id') == node.get('@id') and node.get('@id'):
                            issue('error', 'schema_business_self_parent', url, 'Business is its own parent.')
                        address = node.get('address', {})
                        if not isinstance(address, dict) or not address.get('streetAddress') or not address.get('addressLocality'):
                            issue('warning', 'business_address_unverified_incomplete', url, 'Do not invent physical location; rich-result eligibility not established.')
                    if 'BreadcrumbList' in types:
                        items = node.get('itemListElement', [])
                        if not isinstance(items, list) or not items or not all(isinstance(i, dict) for i in items):
                            issue('error', 'breadcrumb_items', url, 'Expected a nonempty list of breadcrumb objects.')
                            continue
                        if [i.get('position') for i in items] != list(range(1, len(items) + 1)):
                            issue('error', 'breadcrumb_positions', url, 'Breadcrumb positions must be consecutive from 1.')
                        for item in items:
                            if isinstance(item.get('item'), str):
                                asset(item['item'], url, 'breadcrumb_target')
                    if 'ImageObject' in types and isinstance(node.get('url'), str):
                        image_check(node['url'], url)
                    for field in ('image', 'logo', 'primaryImageOfPage'):
                        values = node.get(field, [])
                        values = values if isinstance(values, list) else [values]
                        for value in values:
                            if isinstance(value, str):
                                image_check(value, url)
            elif type_ in ('', 'text/javascript', 'application/javascript', 'module'):
                if script.get('src'):
                    path = asset(script['src'], url, 'script')
                    if path:
                        add_script(path.read_text(encoding='utf-8-sig'), url, type_ == 'module')
                elif script.string and script.string.strip():
                    add_script(script.string, url, type_ == 'module')
        for style in soup.select('style'):
            for match in re.finditer(r'url\(\s*[\"\']?([^\s\)\"\']+)', style.get_text()):
                if not match[1].startswith('#'):
                    asset(match[1], url, 'css_asset')
    for path in root.rglob('*.css'):
        if any(p.startswith('.') or p in {'node_modules', 'outils'} for p in path.relative_to(root).parts):
            continue
        context = urljoin(home_url, path.relative_to(root).as_posix())
        for match in re.finditer(r'url\(\s*[\"\']?([^\s\)\"\']+)', path.read_text(encoding='utf-8-sig')):
            if not match[1].startswith('#'):
                asset(match[1], context, 'css_asset')
    for label, values in [('title', titles), ('description', descriptions)]:
        for value, urls_ in values.items():
            if len(urls_) > 1:
                issue('error' if label == 'title' else 'warning', 'duplicate_' + label, urls_[0], 'Also used by ' + ', '.join(urls_[1:]))
    for url in sitemap_set - {home_url}:
        if url in pages and not inlinks[url]:
            issue('warning', 'no_internal_inlink', url, 'No incoming link from analyzed local HTML.')
    stats['unique_images_verified'] = len(images)
    stats['unique_javascript_blocks'] = len(scripts)
    stats['valid_home_service_ids'] = len(valid_services)
    node_binary = shutil.which('node')
    if scripts and not node_binary:
        issue('error', 'node_missing', '', 'Node.js unavailable; syntax validation incomplete.')
        incomplete = True
    elif scripts:
        with tempfile.TemporaryDirectory(prefix='menageup-js-audit-') as temporary:
            for digest, entry in scripts.items():
                path = Path(temporary) / (digest + ('.mjs' if entry['module'] else '.js'))
                path.write_text(entry['code'], encoding='utf-8')
                try:
                    result = subprocess.run([node_binary, '--check', str(path)], capture_output=True, text=True, timeout=20)
                except (OSError, subprocess.TimeoutExpired):
                    incomplete = True
                    issue('error', 'node_check_incomplete', entry['pages'][0], 'Node.js syntax check could not complete.')
                    continue
                if result.returncode:
                    error = next((s.strip() for s in result.stderr.splitlines() if 'SyntaxError:' in s), 'Node rejected JavaScript syntax.')
                    issue('error', 'javascript_syntax', entry['pages'][0], error)
    return finish()


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
