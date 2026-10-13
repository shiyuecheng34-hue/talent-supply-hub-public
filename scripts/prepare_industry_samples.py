#!/usr/bin/env python3
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src' / 'data' / 'industrySamples.ts'
SHEET_URL = 'https://bytedance.larkoffice.com/sheets/ShwKsQe36hxTiTtEF0Dc4W4cnPe'
INDUSTRIES = [
    ('industry-beauty', '0OYgsp'),
    ('industry-food', '1RZNHB'),
    ('industry-fashion', '2JBIVb'),
    ('industry-mom', '3UBBZb'),
    ('industry-care', '4QiWFQ'),
    ('industry-health', '5rncze'),
    ('industry-digital', '6aYmtl'),
    ('industry-auto', '7myfJs'),
    ('industry-game', '8kFWgq'),
    ('industry-commerce', '9FoKhW'),
    ('industry-finance', '10chQs'),
]


def run_json(cmd):
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if not proc.stdout.strip():
        raise RuntimeError(proc.stderr.strip() or 'empty command output')
    return json.loads(proc.stdout)


def strip_row_prefix(line: str) -> str:
    return re.sub(r'^\[row=\d+\] ', '', line)


def read_sheet(sheet_id: str):
    payload = run_json([
        'lark-cli', 'sheets', '+csv-get',
        '--url', SHEET_URL,
        '--sheet-id', sheet_id,
        '--range', 'A1:AC101',
        '--max-chars', '100000',
    ])
    annotated = payload['data']['annotated_csv']
    clean = '\n'.join(strip_row_prefix(line) for line in annotated.splitlines())
    return list(csv.reader(clean.splitlines()))


def main():
    data = {}
    for binding, sheet_id in INDUSTRIES:
        rows = read_sheet(sheet_id)
        data[binding] = {'headers': rows[0], 'rows': rows[1:]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        'export type IndustrySample = { headers: string[]; rows: string[][] };\n\n'
        f'export const industrySamples: Record<string, IndustrySample> = {json.dumps(data, ensure_ascii=False, indent=2)};\n',
        encoding='utf-8',
    )
    print(json.dumps({k: len(v['rows']) for k, v in data.items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
