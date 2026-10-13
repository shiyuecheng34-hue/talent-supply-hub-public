#!/usr/bin/env python3
import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src' / 'data' / 'douyinAvatarMap.ts'
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
SHEET_URL = 'https://bytedance.larkoffice.com/sheets/ShwKsQe36hxTiTtEF0Dc4W4cnPe'
DATASET_ID = '5685026'
LATEST_PARTITION = '2026-10-11'
AEOLUS_DIR = ROOT.parent / 'inner_skills' / 'aeolus-platform-analysis'


def run_json(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    text = proc.stdout.strip()
    if not text:
        raise RuntimeError(proc.stderr.strip() or 'empty command output')
    return json.loads(text)


def strip_row_prefix(line: str) -> str:
    return re.sub(r'^\[row=\d+\] ', '', line)


def read_ids_for_sheet(sheet_id: str) -> list[str]:
    payload = run_json([
        'lark-cli', 'sheets', '+csv-get',
        '--url', SHEET_URL,
        '--sheet-id', sheet_id,
        '--range', 'A1:AC101',
        '--max-chars', '60000',
    ])
    annotated = payload['data']['annotated_csv']
    clean = '\n'.join(strip_row_prefix(line) for line in annotated.splitlines())
    rows = list(csv.reader(clean.splitlines()))
    if not rows:
        return []
    headers = rows[0]
    try:
        idx = headers.index('达人星图id')
    except ValueError:
        idx = 0
    ids = []
    for row in rows[1:]:
        if idx < len(row):
            value = row[idx].strip()
            if value and value not in ids:
                ids.append(value)
    return ids


def chunked(values, size):
    for i in range(0, len(values), size):
        yield values[i:i + size]


def query_mapping(ids: list[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for chunk in chunked(ids, 180):
        in_list = ','.join(chunk)
        sql = (
            'SELECT `[达人星图id]`, `[抖音unique_id]`, `[抖音short_id]`, `[星图达人抖音昵称]` '
            'FROM `[【官】星图达人数据集]` '
            f"WHERE `[p_date]` = '{LATEST_PARTITION}' AND `[达人星图id]` IN ({in_list}) LIMIT 10000"
        )
        payload = run_json([
            'python3', 'scripts/dataset_sql_query.py',
            '--dataset-id', DATASET_ID,
            '--sql', sql,
        ], cwd=AEOLUS_DIR)
        rows = payload.get('rows')
        if rows is None and payload.get('file'):
            with open(payload['file'], 'r', encoding='utf-8') as file:
                rows = json.load(file).get('rows', [])
        for row in rows or []:
            star_id = str(row.get('star_author_id') or '')
            unique_id = str(row.get('aweme_unique_id') or '')
            short_id = str(row.get('aweme_short_id') or '')
            handle = unique_id or short_id
            result[star_id] = {
                'uniqueId': unique_id,
                'shortId': short_id,
                'displayId': handle,
                'nickName': str(row.get('aweme_nick_name') or ''),
                'profileUrl': f'https://www.douyin.com/search/{handle}?type=user' if handle else '',
                'avatarUrl': '',
            }
    return result


def main():
    ids: list[str] = []
    by_sheet: dict[str, list[str]] = {}
    for binding, sheet_id in INDUSTRIES:
        sheet_ids = read_ids_for_sheet(sheet_id)
        by_sheet[binding] = sheet_ids
        for star_id in sheet_ids:
            if star_id not in ids:
                ids.append(star_id)
    mapping = query_mapping(ids)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        'dataset': '【官】星图达人数据集',
        'datasetId': DATASET_ID,
        'partition': LATEST_PARTITION,
        'source': 'https://data.bytedance.net/aeolus/pages/dataQuery?appId=1002633&isDefault=1&rid=17268794&sid=5685026',
        'matched': len(mapping),
        'requested': len(ids),
        'note': 'avatarUrl 留空时，页面展示姓名首字 fallback；可用同一映射继续补充抖音头像抓取结果。',
    }
    content = (
        'export type DouyinAvatarRecord = { uniqueId: string; shortId: string; displayId: string; nickName: string; profileUrl: string; avatarUrl: string };\n\n'
        f'export const douyinAvatarMeta = {json.dumps(metadata, ensure_ascii=False, indent=2)} as const;\n\n'
        f'export const douyinAvatarMap: Record<string, DouyinAvatarRecord> = {json.dumps(mapping, ensure_ascii=False, indent=2)};\n'
    )
    OUT.write_text(content, encoding='utf-8')
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
