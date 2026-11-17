"""行业/节点最后 41 个头像缺口恢复（2026-11-17）。

背景：build_industry_avatar_sprites 首轮后仍有 41 个 ID 无头像。
实测发现数字抖音号以 short_id 参数请求返回 status_code=5，
但同一值改用 unique_id 参数可正常命中（如「麻里」27796347）。
本脚本对每个缺口逐个真实请求 unique_id 通道，不再批量推断：

1. 有 displayId：GET user/info?unique_id=<displayId>，最多 2 次尝试
2. 昵称与旧 map nickName 核对，不一致记 identity_mismatch 不采用
3. 成功则下载 avatar_larger 到 avatar-assets/industry-<id>.jpg，
   并按 industry_latest 缓存格式落盘，供构建脚本第一优先级消费
4. 痣女如花（6870163473385390093）沿用历史运行时覆盖：
   src/assets/zhinv-avatar.jpg + 已核验 sec_uid
5. 无 displayId 且无任何句柄记 missing_handle
所有结果逐条记录，status_code=5 保留原始响应码，不做全局断言。
"""
import json
import re
import time
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/industry_latest'
CACHE.mkdir(parents=True, exist_ok=True)
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/126.0 Safari/537.36'
    ),
    'Referer': 'https://www.iesdouyin.com/',
}
API = 'https://www.iesdouyin.com/web/api/v2/user/info/'
ZHINV_ID = '6870163473385390093'
ZHINV_SEC = 'MS4wLjABAAAAhAIMHZRI61dC4eivwuT99LAKz3VCH2P7u0RsvOQin7w'

# 现有精灵图已覆盖的 ID 不再处理
sprite_text = (ROOT / 'src/data/industryAvatarSprites.ts').read_text()
covered = set(re.findall(r"'(\d{19})'", sprite_text))
profiles = json.loads((ROOT / 'src/data/industryTalentProfiles.json').read_text())['profiles']
missing = sorted(sid for sid in profiles if sid not in covered)
print(f'缺口 {len(missing)} 个')

old_blocks = dict(
    re.findall(
        r"'(\d{19})': \{(.*?)\n  \}",
        (ROOT / 'src/data/douyinAvatarMap.ts').read_text(),
        re.S,
    )
)

session = requests.Session()
session.headers.update(HEADERS)
summary = {'ok': [], 'status5': [], 'identity_mismatch': [], 'missing_handle': [], 'error': []}


def save_ok(sid, info, source):
    sec_uid = info['sec_uid']
    record = {
        'uniqueId': info.get('unique_id') or '',
        'shortId': str(info.get('short_id') or ''),
        'displayId': info.get('unique_id') or str(info.get('short_id') or ''),
        'nickName': info.get('nickname') or '',
        'secUid': sec_uid,
        'profileUrl': f'https://www.douyin.com/user/{sec_uid}',
        'avatarUrl': f'/avatars/industry-{sid}.jpg',
    }
    avatar_field = info.get('avatar_medium') or info.get('avatar_thumb') or info.get('avatar_larger')
    url_list = (avatar_field or {}).get('url_list') or []
    if not url_list:
        raise RuntimeError('avatar_larger.url_list 为空')
    image_response = session.get(url_list[0], timeout=12)
    image_response.raise_for_status()
    image = Image.open(__import__('io').BytesIO(image_response.content)).convert('RGB')
    image.save(ROOT / 'avatar-assets' / f'industry-{sid}.jpg', 'JPEG', quality=88)
    (CACHE / f'{sid}.json').write_text(
        json.dumps(
            {'id': sid, 'status': 'ok', 'attempts': 1, 'source': source, 'record': record},
            ensure_ascii=False,
            indent=1,
        )
    )
    summary['ok'].append(sid)


for sid in missing:
    # 痣女如花：历史运行时覆盖资产
    if sid == ZHINV_ID:
        zhinv = Image.open(ROOT / 'src/assets/zhinv-avatar.jpg').convert('RGB')
        zhinv.save(ROOT / 'avatar-assets' / f'industry-{sid}.jpg', 'JPEG', quality=88)
        (CACHE / f'{sid}.json').write_text(
            json.dumps(
                {
                    'id': sid,
                    'status': 'ok',
                    'attempts': 0,
                    'source': 'runtime_override_asset',
                    'record': {
                        'uniqueId': '',
                        'shortId': '141000699',
                        'displayId': '141000699',
                        'nickName': '痣女如花',
                        'secUid': ZHINV_SEC,
                        'profileUrl': f'https://www.douyin.com/user/{ZHINV_SEC}',
                        'avatarUrl': f'/avatars/industry-{sid}.jpg',
                    },
                },
                ensure_ascii=False,
                indent=1,
            )
        )
        summary['ok'].append(sid)
        print(f'{sid} 痣女如花 -> runtime override')
        continue

    display_id = profiles[sid].get('displayId') or ''
    block = old_blocks.get(sid, '')
    expected_name = ''
    name_match = re.search(r"nickName: '([^']*)'", block)
    if name_match:
        expected_name = name_match.group(1)
    if not display_id:
        summary['missing_handle'].append(sid)
        print(f'{sid} 无可用句柄 -> missing_handle')
        continue

    payload = None
    last_code = None
    for attempt in range(2):
        try:
            response = session.get(API, params={'unique_id': display_id}, timeout=10)
            payload = response.json()
            last_code = payload.get('status_code')
            if last_code == 0:
                break
        except Exception as exc:  # noqa: BLE001 - 需逐条保留失败原因
            last_code = f'error:{type(exc).__name__}'
        time.sleep(1.2 * (attempt + 1))

    if not payload or last_code != 0 or not payload.get('user_info'):
        bucket = summary['error'] if isinstance(last_code, str) else summary['status5']
        bucket.append(sid)
        (CACHE / f'{sid}.json').write_text(
            json.dumps(
                {'id': sid, 'status': 'unique_id_failed', 'code': last_code, 'attempts': 2},
                ensure_ascii=False,
            )
        )
        print(f'{sid} unique_id={display_id} -> 失败 {last_code}')
        time.sleep(0.8)
        continue

    info = payload['user_info']
    if expected_name and info.get('nickname') and info['nickname'] != expected_name:
        summary['identity_mismatch'].append(sid)
        (CACHE / f'{sid}.json').write_text(
            json.dumps(
                {
                    'id': sid,
                    'status': 'identity_mismatch',
                    'expected': expected_name,
                    'returned': info.get('nickname'),
                    'attempts': 1,
                },
                ensure_ascii=False,
            )
        )
        print(f"{sid} 昵称不一致：期望「{expected_name}」返回「{info.get('nickname')}」")
        time.sleep(0.8)
        continue

    try:
        save_ok(sid, info, 'unique_id_fallback')
        print(f"{sid} unique_id={display_id} -> ok（{info.get('nickname')}）")
    except Exception as exc:  # noqa: BLE001
        summary['error'].append(sid)
        print(f'{sid} 头像下载失败：{exc}')
    time.sleep(0.8)

print('\n汇总：', json.dumps({k: len(v) for k, v in summary.items()}, ensure_ascii=False))
print('仍失败：', json.dumps(summary, ensure_ascii=False))
