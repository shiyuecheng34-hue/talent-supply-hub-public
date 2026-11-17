"""P0 作者头像断点续跑抓取。

- 映射读取 .cache/avatars/p0_latest/mapping-*.json（2026-11-16 分区）
- 依次尝试 unique_id / short_id 两个 handle（历史上 short_id 报 status5 的账号改 unique_id 可恢复）
- 受控并发 + 单请求超时 + 有限重试，状态逐 ID 落盘，可随时中断后续跑
- 原图保存 avatar-assets/p0-<id>.jpg，状态含 secUid 供生成深链主页
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
CACHE = ROOT.parent / '.cache/avatars/p0_latest'
ASSETS = ROOT / 'avatar-assets'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.iesdouyin.com/'}
TRANSIENT = {'http_444', 'ProxyError', 'timeout', 'profile_non_json_or_invalid_image',
             'ConnectionError', 'timebox_unattempted', 'http_429', 'http_500', 'http_502', 'http_503', 'http_504'}
MAX_WORKERS = 8

mapping: dict[str, dict] = {}
for path in CACHE.glob('mapping-2*.json'):
    for row in json.loads(path.read_text()):
        mapping[str(row['star_author_id'])] = row

ids = sorted(mapping)
print(json.dumps({'todoCandidates': len(ids)}, ensure_ascii=False), flush=True)


def try_handle(sid: str, key: str, handle: str, unique: str, short: str):
    response = requests.get(
        'https://www.iesdouyin.com/web/api/v2/user/info/',
        params={key: handle}, headers=HEADERS, timeout=8,
    )
    response.raise_for_status()
    data = response.json()
    if data.get('status_code') != 0:
        return None, f"profile_status_{data.get('status_code')}"
    user = data.get('user_info') or {}
    if (unique and str(user.get('unique_id') or '').lower() != unique.lower()) or \
       (not unique and str(user.get('short_id') or '') != str(short)):
        return None, 'identity_mismatch'
    urls = (user.get('avatar_medium') or user.get('avatar_thumb') or {}).get('url_list', [])
    if not urls:
        return None, 'no_avatar'
    image = requests.get(urls[0], headers=HEADERS, timeout=8)
    image.raise_for_status()
    with Image.open(BytesIO(image.content)) as im:
        im.convert('RGB').save(ASSETS / f'p0-{sid}.jpg', quality=85)
    record = {
        'uniqueId': unique, 'shortId': short, 'displayId': handle,
        'nickName': user.get('nickname') or '',
        'secUid': str(user.get('sec_uid') or ''),
        'profileUrl': f'https://www.douyin.com/user/{user.get("sec_uid")}' if user.get('sec_uid')
        else 'https://www.douyin.com/search/' + quote(handle) + '?type=user',
        'avatarUrl': f'/avatars/p0-{sid}.jpg',
    }
    return record, 'ok'


def fetch_one(sid: str):
    status_file = CACHE / f'{sid}.json'
    if status_file.exists():
        prev = json.loads(status_file.read_text())
        if prev.get('status') == 'ok' or prev.get('status') not in TRANSIENT:
            return prev
    row = mapping[sid]
    unique = str(row.get('aweme_unique_id') or '').strip()
    short = str(row.get('aweme_short_id') or '').strip()
    handles = []
    if unique and unique != '0':
        handles.append(('unique_id', unique))
    if short and short != '0':
        handles.append(('short_id', short))
    status = {'id': sid, 'status': 'missing_handle', 'attempts': 0}
    for key, handle in handles:
        for attempt in range(3):
            status['attempts'] = attempt + 1
            try:
                record, result = try_handle(sid, key, handle, unique, short)
                if result == 'ok':
                    status.update(status='ok', record=record)
                    status_file.write_text(json.dumps(status, ensure_ascii=False))
                    return status
                status['status'] = result
                # status5「参数不合法」是确定性拒绝（short_id/uid 参数已停用），重试无意义
                if result in ('identity_mismatch', 'profile_status_5', 'no_avatar'):
                    break
                time.sleep(0.3 + 0.2 * attempt)
            except requests.Timeout:
                status['status'] = 'timeout'
            except requests.HTTPError as e:
                status['status'] = f'http_{e.response.status_code}'
            except ValueError:
                status['status'] = 'profile_non_json_or_invalid_image'
            except Exception as e:
                status['status'] = type(e).__name__
            time.sleep(0.4 + 0.3 * attempt)
        if status['status'] == 'ok':
            break
    status_file.write_text(json.dumps(status, ensure_ascii=False))
    return status


def main():
    ASSETS.mkdir(exist_ok=True)
    todo = []
    for sid in ids:
        f = CACHE / f'{sid}.json'
        if not f.exists() or json.loads(f.read_text()).get('status') in TRANSIENT:
            todo.append(sid)
    print(json.dumps({'todo': len(todo)}, ensure_ascii=False), flush=True)
    counts: Counter = Counter()
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
