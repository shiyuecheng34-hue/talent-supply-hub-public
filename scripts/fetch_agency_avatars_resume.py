"""A 代理商重点头像断点续跑（无时间盒版本）。

- 映射直接读取 .cache/avatars/agency_latest/mapping-*.json（2026-11-15 分区，14,903 条全覆盖）
- 已有 status=ok 的跳过；瞬时失败（http_444 / ProxyError / timeout 等）自动重试
- 永久失败（profile_status_5 / identity_mismatch / no_avatar / missing_handle）保留不重跑
- 受控并发 + 单请求超时 + 有限重试，状态逐 ID 落盘，可随时中断后续跑
"""
import concurrent.futures as cf
import json
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/agency_latest'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.iesdouyin.com/'}
TRANSIENT = {'http_444', 'ProxyError', 'timeout', 'profile_non_json_or_invalid_image',
             'ConnectionError', 'timebox_unattempted'}
MAX_WORKERS = 6

mapping = {}
for path in CACHE.glob('mapping-*.json'):
    for row in json.loads(path.read_text()):
        mapping[row['star_author_id']] = row

ids = [r['id'] for r in json.loads((ROOT / 'src/data/agencySnapshot.json').read_text())['records']]
assert len(ids) == 14903 and len(mapping) == 14903


def fetch_one(sid: str):
    status_file = CACHE / f'{sid}.json'
    if status_file.exists():
        prev = json.loads(status_file.read_text())
        if prev.get('status') == 'ok':
            return prev
        if prev.get('status') not in TRANSIENT:
            return prev
    row = mapping[sid]
    unique = str(row.get('aweme_unique_id') or '').strip()
    short = str(row.get('aweme_short_id') or '').strip()
    key, handle = ('unique_id', unique) if unique not in ('', '0') else ('short_id', short)
    status = {'id': sid, 'status': 'missing_handle', 'attempts': 0}
    if handle and handle != '0':
        for attempt in range(3):
            status['attempts'] = attempt + 1
            try:
                response = requests.get(
                    'https://www.iesdouyin.com/web/api/v2/user/info/',
                    params={key: handle}, headers=HEADERS, timeout=8,
                )
                response.raise_for_status()
                data = response.json()
                if data.get('status_code') != 0:
                    status['status'] = f"profile_status_{data.get('status_code')}"
                    time.sleep(0.3 + 0.2 * attempt)
                    continue
                user = data.get('user_info') or {}
                if (unique and str(user.get('unique_id') or '').lower() != unique.lower()) or \
                   (not unique and str(user.get('short_id') or '') != short):
                    status['status'] = 'identity_mismatch'
                    continue
                urls = (user.get('avatar_medium') or user.get('avatar_thumb') or {}).get('url_list', [])
                if not urls:
                    status['status'] = 'no_avatar'
                    continue
                image = requests.get(urls[0], headers=HEADERS, timeout=8)
                image.raise_for_status()
                with Image.open(BytesIO(image.content)) as im:
                    im.convert('RGB').save(ROOT / 'avatar-assets' / f'agency-{sid}.jpg', quality=85)
                status.update(
                    status='ok',
                    record={
                        'uniqueId': unique, 'shortId': short, 'displayId': handle,
                        'nickName': user.get('nickname') or '',
                        'profileUrl': 'https://www.douyin.com/search/' + quote(handle) + '?type=user',
                        'avatarUrl': f'/avatars/agency-{sid}.jpg',
                    },
                )
                break
            except requests.Timeout:
                status['status'] = 'timeout'
            except requests.HTTPError as e:
                status['status'] = f'http_{e.response.status_code}'
            except ValueError:
                status['status'] = 'profile_non_json_or_invalid_image'
            except Exception as e:
                status['status'] = type(e).__name__
            time.sleep(0.4 + 0.3 * attempt)
    status_file.write_text(json.dumps(status, ensure_ascii=False))
    return status


def main():
    todo = []
    for sid in ids:
        f = CACHE / f'{sid}.json'
        if not f.exists() or json.loads(f.read_text()).get('status') in TRANSIENT:
            todo.append(sid)
    print(json.dumps({'todo': len(todo)}, ensure_ascii=False), flush=True)
    counts = Counter()
    started = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for i, status in enumerate(pool.map(fetch_one, todo), 1):
            counts[status['status']] += 1
            if i % 200 == 0:
                print(json.dumps({'done': i, 'elapsed': round(time.monotonic() - started),
                                  'counts': dict(counts)}, ensure_ascii=False), flush=True)
    print(json.dumps({'finished': len(todo), 'elapsed': round(time.monotonic() - started),
                      'counts': dict(counts)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
