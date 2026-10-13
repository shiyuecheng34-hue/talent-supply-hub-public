#!/usr/bin/env python3
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src' / 'data' / 'nodeSamples.ts'
SHEET_URL = 'https://bytedance.larkoffice.com/sheets/BfFYsEunBhI0PKtGKzfc6smbnic'
NODES = [
    ('node-1111', '0iHZMy'),
    ('node-1212', '1tVppi'),
    ('node-newyear', '2pzQvF'),
    ('node-christmas', '3PUkix'),
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
        '--range', 'A1:AN101',
        '--max-chars', '150000',
    ])
    annotated = payload['data']['annotated_csv']
    clean = '\n'.join(strip_row_prefix(line) for line in annotated.splitlines())
    return list(csv.reader(clean.splitlines()))


def main():
    data = {}
    for binding, sheet_id in NODES:
        rows = read_sheet(sheet_id)
        data[binding] = {'headers': rows[0], 'rows': rows[1:]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        'export type NodeSample = { headers: string[]; rows: string[][] };\n\n'
        f'export const nodeSamples: Record<string, NodeSample> = {json.dumps(data, ensure_ascii=False, indent=2)};\n',
        encoding='utf-8',
    )
    print(json.dumps({k: len(v['rows']) for k, v in data.items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
