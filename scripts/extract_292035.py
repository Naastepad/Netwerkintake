import csv
import hashlib
import json
import re
from pathlib import Path

import pdfplumber
from bs4 import BeautifulSoup

OUT = Path('output')
OUT.mkdir(exist_ok=True)
PDF = OUT / 'source.pdf'
HTML = OUT / 'detail_292035.html'

HEADERS = [
    'pdf_pagina', 'folio', 'datum', 'verkoper', 'koper', 'eigendom',
    'straat_ligging', 'belending_oost', 'belending_zuid',
    'belending_west', 'belending_noord', 'opmerkingen'
]


def clean(value):
    if value is None:
        return ''
    return re.sub(r'\s+', ' ', str(value).replace('\r', ' ').replace('\n', ' ')).strip()


html = HTML.read_text(encoding='utf-8', errors='replace')
soup = BeautifulSoup(html, 'lxml')
page_title = soup.title.get_text(' ', strip=True) if soup.title else ''
meta = {}
for tag in soup.find_all('meta'):
    key = tag.get('name') or tag.get('property')
    value = tag.get('content')
    if key and value:
        meta[key] = value

rows = []
page_table_counts = []
with pdfplumber.open(PDF) as pdf:
    page_count = len(pdf.pages)
    for page_number, page in enumerate(pdf.pages, 1):
        tables = page.extract_tables() or []
        page_new_rows = 0
        for table in tables:
            for raw_row in table or []:
                if not raw_row:
                    continue
                values = [clean(value) for value in raw_row]
                if not any(values):
                    continue
                joined = ' '.join(values).lower()
                if values[0].lower() == 'folio' or (
                    'folio' in joined and 'datum' in joined and 'verkoper' in joined
                ):
                    continue
                if len(values) < 10:
                    values += [''] * (10 - len(values))
                elif len(values) > 10:
                    values = values[:9] + [' '.join(values[9:])]

                folio, date = values[0], values[1]
                new_row = bool(folio) and (bool(re.search(r'\d', folio)) or bool(date))
                if not new_row and rows and rows[-1][0] == page_number:
                    previous = rows[-1]
                    for index, value in enumerate(values, start=1):
                        if value:
                            previous[index] = (previous[index] + ' ' + value).strip()
                    continue

                rows.append([page_number] + values + [''])
                page_new_rows += 1
        page_table_counts.append([page_number, len(tables), page_new_rows])

# Deduplicate exact duplicates only.
deduplicated = []
seen = set()
for row in rows:
    key = tuple(row)
    if key not in seen:
        seen.add(key)
        deduplicated.append(row)
rows = deduplicated

nisse_pattern = re.compile(
    r'(?<![A-Za-zÀ-ÿ])(Nissepadt|Nissepat|Nissepad|Nisse)(?![A-Za-zÀ-ÿ])',
    re.IGNORECASE,
)
nisse_rows = [row for row in rows if nisse_pattern.search(' | '.join(map(str, row)))]

for filename, data in [
    ('all_rows.csv', rows),
    ('nissepat_matches.csv', nisse_rows),
]:
    with (OUT / filename).open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerows(data)

summary = {
    'record_id': '292035',
    'detail_url': 'https://collecties.erfgoedvangoes.nl/detail.php?nav_id=2-1&index=12&imgid=53565660&id=292035',
    'pdf_url': 'https://collecties.erfgoedvangoes.nl/HttpHandler/icoon.ico?file=53565660&pdfviewer=1',
    'imgid': '53565660',
    'html_title': page_title,
    'meta': meta,
    'page_count': page_count,
    'row_count': len(rows),
    'nisse_count': len(nisse_rows),
    'first_row': rows[0] if rows else None,
    'last_row': rows[-1] if rows else None,
    'page_table_counts': page_table_counts,
    'pdf_sha256': hashlib.sha256(PDF.read_bytes()).hexdigest(),
    'pdf_bytes': PDF.stat().st_size,
}
(OUT / 'summary.json').write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8'
)

with (OUT / 'summary.txt').open('w', encoding='utf-8') as handle:
    handle.write(f"HTML title: {page_title}\n")
    handle.write(f"PDF pages: {page_count}\n")
    handle.write(f"Rows: {len(rows)}\n")
    handle.write(f"Nisse matches: {len(nisse_rows)}\n")
    handle.write(f"First: {rows[0] if rows else None}\n")
    handle.write(f"Last: {rows[-1] if rows else None}\n")
    handle.write(f"PDF SHA256: {summary['pdf_sha256']}\n\n")
    for row in nisse_rows:
        handle.write('NISSE: ' + ' | '.join(map(str, row)) + '\n')

print((OUT / 'summary.txt').read_text(encoding='utf-8'))
