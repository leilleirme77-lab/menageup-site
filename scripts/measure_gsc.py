"""Read an official GSC CSV export, without Google credentials or network calls.

Usage: python scripts/measure_gsc.py --input C:/private/gsc --output C:/private/report.json
The output must stay outside the public website. A sitemap is not indexing proof.
"""
import argparse
import csv
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import unicodedata


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn')


def read_table(root, aliases):
    matches = [f for f in root.glob('*.csv') if normalize(f.stem) in aliases]
    if len(matches) > 1:
        raise ValueError('Ambiguous CSV export: ' + ', '.join(f.name for f in matches))
    if not matches:
        return None, []
    file = matches[0]
    return file, list(csv.DictReader(file.open(encoding='utf-8-sig', newline='')))


def integer(value):
    number = int(value)
    if number < 0:
        raise ValueError('Negative metric')
    return number


def totals(rows):
    clicks = sum(integer(r['Clics']) for r in rows)
    impressions = sum(integer(r['Impressions']) for r in rows)
    return dict(clicks=clicks, impressions=impressions, ctr=round(clicks / impressions * 100, 3) if impressions else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--as-of', type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    site = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output == site or site in output.parents:
        raise ValueError('Do not write private Google data inside the public website')
    source = args.input.resolve()
    chart_file, chart = read_table(source, ['graphique'])
    if not chart_file or not chart:
        raise ValueError('Official Graphique.csv required')
    chart = sorted(chart, key=lambda r: r['Date'])
    dates = [date.fromisoformat(r['Date']) for r in chart]
    if len(set(dates)) != len(dates) or any(d > args.as_of for d in dates):
        raise ValueError('Duplicate or future dates')
    if any((b - a).days != 1 for a, b in zip(dates, dates[1:])):
        raise ValueError('Missing dates: refusing a misleading period comparison')
    filters_file, filters = read_table(source, ['filtres'])
    if not filters_file:
        raise ValueError('Filtres.csv required to record the reporting scope')
    scope = {r['Filtre']: r['Valeur'] for r in filters}
    overall = totals(chart)
    queries_file, queries = read_table(source, ['requetes'])
    pages_file, pages = read_table(source, ['pages'])
    named = totals(queries) if queries else None
    gap = None
    if named:
        gap = {k: overall[k] - named[k] for k in ['clicks', 'impressions']}
    comparison = None
    if len(chart) >= 56:
        previous, current = totals(chart[-56:-28]), totals(chart[-28:])
        comparison = dict(previous={'start': chart[-56]['Date'], 'end': chart[-29]['Date'], **previous}, current={'start': chart[-28]['Date'], 'end': chart[-1]['Date'], **current}, changes={k: {'absolute': current[k] - previous[k], 'percent': round((current[k] / previous[k] - 1) * 100, 2) if previous[k] else None} for k in ['clicks', 'impressions']})
    selected_pages = []
    for row in pages:
        url = next(iter(row.values()))
        if any(word in url for word in ['tournan', 'base-vie', 'debarras', 'inoccupe']):
            selected_pages.append(dict(url=url, **totals([row]), position=float(row['Position'].replace(',', '.'))))
    result = dict(as_of=args.as_of.isoformat(), source=str(source), scope=scope, period={'start': dates[0].isoformat(), 'end': dates[-1].isoformat(), 'days': len(chart), 'age_of_last_row_days': (args.as_of - dates[-1]).days}, property_totals=overall, named_queries={'rows': len(queries), 'totals': named, 'difference_from_property': gap, 'limit': 'Not a list of all searches; do not attribute unidentified clicks to a keyword.'}, page_table={'rows': len(pages), 'totals': totals(pages) if pages else None, 'aggregation': 'By page: do not add to, or require equality with, property totals.', 'selected_pages': selected_pages}, comparison_28_days=comparison, sources=[{'file': str(f), 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in [chart_file, filters_file, queries_file, pages_file] if f], limits=['Exported rows may include preliminary Google data; the CSV does not certify finalization.', 'No Google login, API request, URL inspection or indexing assertion.', 'No monthly search volume or ranking gain inferred from impressions.', 'A 28-day comparison requires 56 consecutive daily rows in the same export and scope.', 'Google documents different property/page aggregation and anonymized query omissions.'], google_explanation='https://support.google.com/webmasters/answer/17011364')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(output), 'period': result['period'], 'totals': overall, 'named_query_rows': len(queries), 'comparison_possible': comparison is not None}))


if __name__ == '__main__':
    main()
