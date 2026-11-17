"""从断点状态重建抖音主页映射并输出头像覆盖审计。

- 读取 .cache/avatars/agency_latest 下全部状态文件
- 仅采用 status=ok 且包含 sec_uid 的记录，生成抖音真实主页深链
- 无 sec_uid 的账号不生成主页链接，不使用搜索页兜底
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

total = len(target_ids)
covered = len(profiles)
profile_json = {
    'meta': {
        'source': 'iesdouyin user/info via 数据集5685026星图ID映射',
        'partition': '2026-11-15',
        'generatedAt': '2026-11-17',
        'count': covered,
        'note': '仅保留 sec_uid 生成的抖音真实主页深链；无 sec_uid 的账号不生成主页链接。',
    },
    'profiles': dict(sorted(profiles.items())),
}
(ROOT / 'src/data/agencyProfileUrls.json').write_text(
    json.dumps(profile_json, ensure_ascii=False, indent=2) + '\n'
)

audit = {
    'total': total,
    'avatarCovered': covered,
    'coverage': round(covered / total, 4),
    'statusBreakdown': dict(status_counter),
    'shortIdOnlyPendingUniqueIdRetry': status_counter.get('profile_status_5', 0),
    'note': 'profile_status_5 表示历史请求以 short_id/user_id 参数通道未命中，并不代表账号不存在或永久不可恢复；数字号可改用 unique_id 参数通道重试，成功后更新为 ok。missing_handle 为数据集无任何抖音句柄。',
}
(ROOT / 'src/data/agencyAvatarAudit.json').write_text(
    json.dumps(audit, ensure_ascii=False, indent=2) + '\n'
)
print(json.dumps(audit, ensure_ascii=False))
