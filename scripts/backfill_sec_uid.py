"""为 ok 头像记录回填 sec_uid，并把抖音链接升级为真实主页深链。

- 仅处理 status=ok 且 record 中缺少 secUid 的状态文件
- 复用原查询句柄（unique_id 优先），断点续跑、受控并发
- profileUrl 统一升级为 https://www.douyin.com/user/<sec_uid>
"""
import concurrent.futures as cf
import json
import time
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/agency_latest'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.iesdouyin.com/'}
MAX_WORKERS = 4


def backfill(path: Path):
    status = json.loads(path.read_text())
    if status.get('status') != 'ok' or not status.get('record'):
        return 'not_ok'
    record = status['record']
    if record.get('secUid'):
        return 'already'
    handle = record.get('displayId')
    key = 'unique_id' if record.get('uniqueId') else 'short_id'
    error = 'failed'
    for attempt in range(3):
        try:
            response = requests.get(
                'https://www.iesdouyin.com/web/api/v2/user/info/',
                params={key: handle}, headers=HEADERS, timeout=8,
            )
            response.raise_for_status()
            data = response.json()
            if data.get('status_code') != 0:
                time.sleep(0.3 + 0.2 * attempt)
                continue
            user = data.get('user_info') or {}
            sec_uid = user.get('sec_uid')
            if not sec_uid:
                return 'no_sec_uid'
            record['secUid'] = sec_uid
            record['profileUrl'] = f'https://www.douyin.com/user/{sec_uid}'
            path.write_text(json.dumps(status, ensure_ascii=False))
            time.sleep(0.15)
            return 'upgraded'
        except requests.Timeout:
            error = 'timeout'
            time.sleep(0.8)
        except requests.HTTPError as e:
            error = f'http_{e.response.status_code}'
            time.sleep(1.2 + 0.5 * attempt)
        except Exception as e:
            error = type(e).__name__
            time.sleep(0.6)
    return error or 'failed'


def main():
    todo = [
        p for p in CACHE.glob('*.json')
        if not p.name.startswith('mapping-')
        and (lambda d: d.get('status') == 'ok' and not d.get('record', {}).get('secUid'))(
            json.loads(p.read_text())
        )
    ]
    print(json.dumps({'todo': len(todo)}, ensure_ascii=False), flush=True)
    counts = Counter()
    started = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for i, result in enumerate(pool.map(backfill, todo), 1):
            counts[result] += 1
            if i % 500 == 0:
                print(json.dumps({'done': i, 'elapsed': round(time.monotonic() - started),
                                  'counts': dict(counts)}, ensure_ascii=False), flush=True)
    print(json.dumps({'finished': len(todo), 'elapsed': round(time.monotonic() - started),
                      'counts': dict(counts)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
