#!/usr/bin/env python3
import csv
import json
import re
import subprocess
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
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
NODES = [
    ('node-1111', '0iHZMy'),
    ('node-1212', '1tVppi'),
    ('node-newyear', '2pzQvF'),
    ('node-christmas', '3PUkix'),
]
INDUSTRY_SHEET_URL = 'https://bytedance.larkoffice.com/sheets/ShwKsQe36hxTiTtEF0Dc4W4cnPe'
NODE_SHEET_URL = 'https://bytedance.larkoffice.com/sheets/BfFYsEunBhI0PKtGKzfc6smbnic'
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


def read_ids_for_sheet(sheet_url: str, sheet_id: str, data_range: str) -> list[str]:
    payload = run_json([
        'lark-cli', 'sheets', '+csv-get',
        '--url', sheet_url,
        '--sheet-id', sheet_id,
        '--range', data_range,
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


def fetch_douyin_profile(record: dict[str, str]) -> dict[str, str]:
    params = []
    if record['uniqueId']:
        params.append(('unique_id', record['uniqueId']))
    if record['shortId']:
        params.append(('short_id', record['shortId']))
    for key, value in params:
        url = f'https://www.iesdouyin.com/web/api/v2/user/info/?{key}={urllib.parse.quote(value)}'
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                payload = json.load(response)
            user = payload.get('user_info') or {}
            avatars = (user.get('avatar_medium') or user.get('avatar_thumb') or {}).get('url_list') or []
            if avatars:
                record['avatarUrl'] = avatars[0]
            sec_uid = str(user.get('sec_uid') or '')
            if sec_uid:
                record['profileUrl'] = f'https://www.douyin.com/user/{sec_uid}'
            if record['avatarUrl']:
                return record
        except Exception:
            continue
    return record


def enrich_avatars(mapping: dict[str, dict[str, str]]) -> int:
    success = 0
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {
            executor.submit(fetch_douyin_profile, record): star_id
            for star_id, record in mapping.items()
        }
        for future in as_completed(futures):
            star_id = futures[future]
            mapping[star_id] = future.result()
            if mapping[star_id]['avatarUrl']:
                success += 1
    return success


def load_existing_mapping() -> dict[str, dict[str, str]]:
    if not OUT.exists():
        return {}
    content = OUT.read_text(encoding='utf-8')
    marker = 'export const douyinAvatarMap: Record<string, DouyinAvatarRecord> = '
    if marker not in content:
        return {}
    raw = content.split(marker, 1)[1].rsplit(';', 1)[0]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def main():
    ids: list[str] = []
    sources = [
        (INDUSTRY_SHEET_URL, INDUSTRIES, 'A1:AC101'),
        (NODE_SHEET_URL, NODES, 'A1:AN101'),
    ]
    for sheet_url, options, data_range in sources:
        for _, sheet_id in options:
            sheet_ids = read_ids_for_sheet(sheet_url, sheet_id, data_range)
            for star_id in sheet_ids:
                if star_id not in ids:
                    ids.append(star_id)
    mapping = query_mapping(ids)
    cached = load_existing_mapping()
    for star_id, record in mapping.items():
        cached_record = cached.get(star_id) or {}
        if cached_record.get('avatarUrl'):
            record['avatarUrl'] = cached_record['avatarUrl']
            record['profileUrl'] = cached_record.get('profileUrl') or record['profileUrl']
    missing = {star_id: record for star_id, record in mapping.items() if not record['avatarUrl']}
    enrich_avatars(missing)
    avatars_matched = sum(bool(record['avatarUrl']) for record in mapping.values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        'dataset': '【官】星图达人数据集',
        'datasetId': DATASET_ID,
        'partition': LATEST_PARTITION,
        'source': 'https://data.bytedance.net/aeolus/pages/dataQuery?appId=1002633&id=1791867289012435&isDefault=1&rid=17268794&sid=5685026',
        'scope': '行业与节点板块每个分组前 100 位达人',
        'matched': len(mapping),
        'requested': len(ids),
        'avatarsMatched': avatars_matched,
        'note': '头像通过抖音用户信息接口按 unique_id / short_id 获取；抓取失败时页面展示姓名首字 fallback。',
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
