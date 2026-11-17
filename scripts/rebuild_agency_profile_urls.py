"""从断点状态重建抖音主页映射并输出头像覆盖审计。

- 读取 .cache/avatars/agency_latest 下全部状态文件
- 仅采用 status=ok 的记录；优先 sec_uid 真实主页，回退搜索页
- 生成 src/data/agencyProfileUrls.json 与 src/data/agencyAvatarAudit.json
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/agency_latest'

snapshot = json.loads((ROOT / 'src/data/agencySnapshot.json').read_text())
target_ids = [r['id'] for r in snapshot['records']]

profiles = {}
status_counter = Counter()
for path in CACHE.glob('*.json'):
    if path.name.startswith('mapping-'):
        continue
    status = json.loads(path.read_text())
    sid = status['id']
    if sid not in set(target_ids):
        continue
    status_counter[status['status']] += 1
    if status['status'] == 'ok' and status.get('record'):
        record = status['record']
        if record.get('secUid'):
            profiles[sid] = f"https://www.douyin.com/user/{record['secUid']}"
        elif record.get('profileUrl'):
            profiles[sid] = record['profileUrl']

total = len(target_ids)
covered = len(profiles)
profile_json = {
    'meta': {
        'source': 'iesdouyin user/info via 数据集5685026星图ID映射',
        'partition': '2026-11-15',
        'generatedAt': '2026-11-17',
        'count': covered,
        'note': '优先 sec_uid 真实主页深链；无 sec_uid 时回退抖音用户搜索页。',
    },
    'profiles': dict(sorted(profiles.items())),
}
(ROOT / 'src/data/agencyProfileUrls.json').write_text(
    json.dumps(profile_json, ensure_ascii=False, indent=2)
)

audit = {
    'total': total,
    'avatarCovered': covered,
    'coverage': round(covered / total, 4),
    'statusBreakdown': dict(status_counter),
    'shortIdOnlyCannotResolve': status_counter.get('profile_status_5', 0),
    'note': 'profile_status_5 为仅有 short_id/无 unique_id 的账号，iesdouyin v2 接口已不接受 short_id/user_id 参数；missing_handle 为数据集无任何抖音句柄。',
}
(ROOT / 'src/data/agencyAvatarAudit.json').write_text(
    json.dumps(audit, ensure_ascii=False, indent=2)
)
print(json.dumps(audit, ensure_ascii=False))
