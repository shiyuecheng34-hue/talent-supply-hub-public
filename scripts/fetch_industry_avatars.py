"""行业/节点样本达人头像补抓（2026-11-17）。

背景：线上行业/节点卡片引用的旧精灵图 /avatars/avatar-sprite.jpg 已不部署，
卡片头像全部退化为姓名首字。本脚本针对 11 个行业样本 + 4 个节点样本中
既不在代理商 ok 缓存、也无法从旧精灵图裁切恢复的 ID 补抓。

句柄来源（按优先级合并）：
1. 旧 douyinAvatarMap 中的 uniqueId / shortId（10-11 分区历史抓取记录）
2. 代理商映射缓存 mapping-*.json（11-15 分区）
3. 本轮 Dataset SQL 最新分区查询结果（11-15/11-16）

接口约束（2026-11-17 实测复核）：
- unique_id 参数可用，返回 status_code=0 + sec_uid + 头像
- short_id 参数统一返回 status_code=5「参数不合法」，标记为永久失败不重试
- 无任何句柄标记 missing_handle
成功记录直接保存 sec_uid 主页深链，身份核验不通过记 identity_mismatch。
"""
import concurrent.futures as cf
import json
import re
import time
from collections import Counter
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/industry_latest'
CACHE.mkdir(parents=True, exist_ok=True)
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.iesdouyin.com/'}
MAX_WORKERS = 4

# 1. 旧 map 句柄
old_blocks = dict(
    re.findall(r"'(\d{19})': \{(.*?)\n  \}", (ROOT / 'src/data/douyinAvatarMap.ts').read_text(), re.S)
)
# 2. 代理商映射缓存
agency_mapping = {}
for path in (ROOT.parent / '.cache/avatars/agency_latest').glob('mapping-*.json'):
    for row in json.loads(path.read_text()):
        agency_mapping[row['star_author_id']] = row
# 3. 本轮风神最新分区查询
fresh = json.load(open('/tmp/industry_fresh_handles.json'))

# 目标：行业 + 节点样本并集
industry_ids = set(
    re.findall(r"\n\s{6,}'(\d{19})',\n\s+'\d", (ROOT / 'src/data/industrySamples.ts').read_text())
)
node_ids = set(
    re.findall(r"^\s+'(\d{19})',$", (ROOT / 'src/data/nodeSamples.ts').read_text(), re.M)
)
target_ids = industry_ids | node_ids

# 代理商 ok 与旧精灵图可覆盖的 ID 无需补抓
agency_ok = set()
for path in (ROOT.parent / '.cache/avatars/agency_latest').glob('*.json'):
    if path.name.startswith('mapping-'):
        continue
    data = json.loads(path.read_text())
    if isinstance(data, dict) and data.get('status') == 'ok':
        agency_ok.add(data['id'])
old_sprite_ids = {sid for sid, body in old_blocks.items() if 'avatarPosition' in body}
todo_ids = sorted(target_ids - agency_ok - old_sprite_ids)

handles = {}
for sid in todo_ids:
    unique = short = ''
    body = old_blocks.get(sid)
    if body:
        unique = re.search(r"uniqueId: '([^']*)'", body).group(1)
        short = re.search(r"shortId: '([^']*)'", body).group(1)
    row = agency_mapping.get(sid)
    if row:
        unique = unique or str(row.get('aweme_unique_id') or '')
        short = short or str(row.get('aweme_short_id') or '')
    row = fresh.get(sid)
    if row:
        unique = unique or row.get('unique_id') or ''
        short = short or row.get('short_id') or ''
    handles[sid] = {'unique_id': unique.strip(), 'short_id': short.strip()}


def fetch_one(sid: str):
    status_file = CACHE / f'{sid}.json'
    if status_file.exists():
        return json.loads(status_file.read_text())
    handle_info = handles[sid]
    unique, short = handle_info['unique_id'], handle_info['short_id']
    if not unique and not short:
        status = {'id': sid, 'status': 'missing_handle', 'attempts': 0}
        status_file.write_text(json.dumps(status, ensure_ascii=False))
        return status
    if not unique:
        # short_id 通道当日实测统一 status5，记永久失败不发请求
        status = {'id': sid, 'status': 'profile_status_5', 'attempts': 0,
                  'note': 'short_id-only; iesdouyin v2 rejects short_id (2026-11-17 verified)'}
        status_file.write_text(json.dumps(status, ensure_ascii=False))
        return status

    status = {'id': sid, 'status': 'failed', 'attempts': 0}
    for attempt in range(3):
        status['attempts'] = attempt + 1
        try:
            response = requests.get(
                'https://www.iesdouyin.com/web/api/v2/user/info/',
                params={'unique_id': unique}, headers=HEADERS, timeout=8,
            )
            response.raise_for_status()
            data = response.json()
            if data.get('status_code') != 0:
                status['status'] = f"profile_status_{data.get('status_code')}"
                time.sleep(0.4 + 0.3 * attempt)
                continue
            user = data.get('user_info') or {}
            if str(user.get('unique_id') or '').lower() != unique.lower():
                status['status'] = 'identity_mismatch'
                continue
            urls = (user.get('avatar_medium') or user.get('avatar_thumb') or {}).get('url_list', [])
            if not urls:
                status['status'] = 'no_avatar'
                continue
            image = requests.get(urls[0], headers=HEADERS, timeout=8)
            image.raise_for_status()
            with Image.open(BytesIO(image.content)) as im:
                im.convert('RGB').save(ROOT / 'avatar-assets' / f'industry-{sid}.jpg', quality=85)
            sec_uid = user.get('sec_uid') or ''
            status.update(
                status='ok',
                record={
                    'uniqueId': unique,
                    'shortId': short,
                    'displayId': unique,
                    'nickName': user.get('nickname') or '',
                    'secUid': sec_uid,
                    'profileUrl': f'https://www.douyin.com/user/{sec_uid}' if sec_uid else '',
                    'avatarUrl': f'/avatars/industry-{sid}.jpg',
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
        time.sleep(0.5 + 0.4 * attempt)
    status_file.write_text(json.dumps(status, ensure_ascii=False))
    time.sleep(0.15)
    return status


def main():
    print(json.dumps({'targets': len(target_ids), 'todo': len(todo_ids),
                      'uniqueFetchable': sum(1 for v in handles.values() if v['unique_id']),
                      'shortOnly': sum(1 for v in handles.values() if not v['unique_id'] and v['short_id']),
                      'noHandle': sum(1 for v in handles.values() if not v['unique_id'] and not v['short_id'])},
                     ensure_ascii=False), flush=True)
    counts = Counter()
    started = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for i, status in enumerate(pool.map(fetch_one, todo_ids), 1):
            counts[status['status']] += 1
            if i % 50 == 0:
                print(json.dumps({'done': i, 'elapsed': round(time.monotonic() - started),
                                  'counts': dict(counts)}, ensure_ascii=False), flush=True)
    print(json.dumps({'finished': len(todo_ids), 'elapsed': round(time.monotonic() - started),
                      'counts': dict(counts)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
