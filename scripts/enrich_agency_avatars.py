"""A 代理商重点限定范围：最新分区只读映射、断点抓取、15分钟时间盒。"""
import concurrent.futures as cf
import json
import re
import subprocess
import time
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/agency_latest'
CACHE.mkdir(parents=True, exist_ok=True)
TOOL = ROOT.parent / 'inner_skills/aeolus-platform-analysis/scripts/dataset_sql_query.py'
PARTITION = '2026-11-15'
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.iesdouyin.com/'}
START = time.monotonic()
DEADLINE = START + 900
ids = [r['id'] for r in json.loads((ROOT / 'src/data/agencySnapshot.json').read_text())['records']]
assert len(ids) == len(set(ids)) == 14903


def existing_assets():
    result = set()
    for filename in ['douyinAvatarMap.ts', 'avatarQueryOverrides.ts']:
        text = (ROOT / 'src/data' / filename).read_text()
        for sid, body in re.findall(r"'([0-9]+)':\s*\{([^}]+)\}", text):
            m = re.search(r"avatarUrl:\s*'([^']+)'", body)
            if m and (ROOT / 'avatar-assets' / m[1].split('/')[-1]).exists():
                result.add(sid)
    supplement = (ROOT / 'src/data/avatarSupplement.ts').read_text()
    result.update(re.findall(r"'([0-9]+)'", supplement))
    # 该头像通过 import 引入，非 /avatars 路径。
    result.add('6870163473385390093')
    return result & set(ids)


def mapping_batch(pair):
    index, batch = pair
    cache = CACHE / f'mapping-{PARTITION}-{batch[0]}.json'
    if cache.exists():
        return json.loads(cache.read_text())
    whitelist = ','.join("'" + sid + "'" for sid in batch)
    sql = f"SELECT toString(`[达人星图id]`) AS star_author_id, `[抖音unique_id]` AS aweme_unique_id, toString(`[抖音short_id]`) AS aweme_short_id FROM `[【官】星图达人数据集]` WHERE `[p_date]` = '{PARTITION}' AND toString(`[达人星图id]`) IN ({whitelist}) LIMIT 7500"
    p = subprocess.run(['python3', str(TOOL), '--dataset-id', '5685026', '--sql', sql], capture_output=True, text=True, timeout=240)
    payload = json.loads(p.stdout)
    if payload.get('file'):
        payload = json.loads(Path(payload['file']).read_text())
    if payload.get('code') not in (None, 'aeolus/ok') or 'rows' not in payload:
        raise RuntimeError(payload)
    rows = payload['rows']
    assert all(isinstance(r['star_author_id'], str) and r['star_author_id'] in batch for r in rows)
    assert len(rows) < 7500
    cache.write_text(json.dumps(rows, ensure_ascii=False))
    return rows


def fetch_one(row):
    sid = row['star_author_id']
    status_file = CACHE / f'{sid}.json'
    if status_file.exists():
        return json.loads(status_file.read_text())
    unique = str(row.get('aweme_unique_id') or '').strip()
    short = str(row.get('aweme_short_id') or '').strip()
    key, handle = ('unique_id', unique) if unique else ('short_id', short)
    status = {'id': sid, 'status': 'missing_handle', 'attempts': 0}
    if handle and handle != '0':
        for attempt in range(3):  # 首次 + 最多2次重试；断点后不重复失败ID。
            if time.monotonic() >= DEADLINE:
                return {'id': sid, 'status': 'timebox_unattempted'}
            status['attempts'] = attempt + 1
            try:
                response = requests.get('https://www.iesdouyin.com/web/api/v2/user/info/', params={key: handle}, headers=HEADERS, timeout=5)
                response.raise_for_status()
                data = response.json()
                if data.get('status_code') != 0:
                    status['status'] = f"profile_status_{data.get('status_code')}"
                    continue
                user = data.get('user_info') or {}
                if (unique and str(user.get('unique_id') or '').lower() != unique.lower()) or (not unique and str(user.get('short_id') or '') != short):
                    status['status'] = 'identity_mismatch'
                    continue
                urls = (user.get('avatar_medium') or user.get('avatar_thumb') or {}).get('url_list', [])
                if not urls:
                    status['status'] = 'no_avatar'
                    continue
                image = requests.get(urls[0], headers=HEADERS, timeout=5)
                image.raise_for_status()
                with Image.open(BytesIO(image.content)) as im:
                    im.convert('RGB').save(ROOT / 'avatar-assets' / f'agency-{sid}.jpg', quality=85)
                status.update(status='ok', record={'uniqueId': unique, 'shortId': short, 'displayId': handle, 'nickName': user.get('nickname') or '', 'profileUrl': 'https://www.douyin.com/search/' + quote(handle) + '?type=user', 'avatarUrl': '/avatars/agency-' + sid + '.jpg'})
                break
            except requests.Timeout:
                status['status'] = 'timeout'
            except requests.HTTPError as e:
                status['status'] = f'http_{e.response.status_code}'
            except ValueError:
                status['status'] = 'profile_non_json_or_invalid_image'
            except Exception as e:
                status['status'] = type(e).__name__
            time.sleep(0.15)
    status_file.write_text(json.dumps(status, ensure_ascii=False))
    return status


def main():
    existing = existing_assets()
    batches = [(i, ids[start:start + 2000]) for i, start in enumerate(range(0, len(ids), 2000))]
    with cf.ThreadPoolExecutor(max_workers=1) as pool:  # 工具按秒命名落盘，串行避免覆盖。
        mapping = [r for rows in pool.map(mapping_batch, batches) for r in rows]
    mapping_ids = {r['star_author_id'] for r in mapping}
    assert len(mapping_ids) == len(mapping)
    print(json.dumps({'mapped': len(mapping_ids), 'existing': len(existing), 'partition': PARTITION}), flush=True)
    targets = [r for r in mapping if r['star_author_id'] not in existing]
    statuses = []
    # 有界队列，每批8个，禁止将全量任务预先塞入线程池越过时间盒。
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for start in range(0, len(targets), 8):
            if time.monotonic() >= DEADLINE:
                break
            statuses.extend(pool.map(fetch_one, targets[start:start + 8]))
            if start % 200 == 0:
                print(json.dumps({'processed': len(statuses), 'success': sum(s['status'] == 'ok' for s in statuses), 'elapsed': round(time.monotonic() - START)}), flush=True)
    success = {s['id']: s['record'] for s in statuses if s['status'] == 'ok'}
    out = "import type { DouyinAvatarRecord } from './douyinAvatarMap';\nexport const agencyAvatarOverrides: Record<string, DouyinAvatarRecord> = " + json.dumps(success, ensure_ascii=False, indent=2) + ';\n'
    (ROOT / 'src/data/agencyAvatarOverrides.ts').write_text(out)
    report = {'capturedAt': time.strftime('%Y-%m-%d %H:%M:%S CST'), 'partition': PARTITION, 'targetCount': len(ids), 'mappingSuccess': len(mapping_ids), 'mappingMissing': len(set(ids) - mapping_ids), 'reusedAvatarCount': len(existing), 'newAvatarCount': len(success), 'coverageCount': len(existing | set(success)), 'attempted': len(statuses), 'failures': dict(Counter(s['status'] for s in statuses if s['status'] != 'ok')), 'timeboxUnattempted': len(targets) - len(statuses), 'elapsedSeconds': round(time.monotonic() - START)}
    (ROOT / 'src/data/agencyAvatarAudit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
