"""P0 作者抖音 short_id 映射（用于无法获取 sec_uid 的账号提供可点击主页链接）。

背景：抖音 user/info 接口目前仅支持 unique_id/sec_uid；部分作者在数据集中只有 short_id。
这些账号无法在未登录态下拉取头像与 sec_uid，但仍可提供 /user/<short_id> 形式的跳转链接。

- 输入：src/data/p0Authors.json、.cache/avatars/p0_latest/mapping-*.json
- 输出：src/data/p0ShortIds.json（id -> short_id）
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/p0_latest'
OUT = ROOT / 'src/data/p0ShortIds.json'


def main():
    p0 = json.loads((ROOT / 'src/data/p0Authors.json').read_text())
    target_ids = {row[1] for row in p0['rows']}

    mapping = {}
    for path in sorted(CACHE.glob('mapping-2*.json')):
        rows = json.loads(path.read_text())
        for row in rows:
            sid = str(row.get('star_author_id'))
            if sid not in target_ids:
                continue
            unique_id = str(row.get('aweme_unique_id') or '').strip()
            short_id = str(row.get('aweme_short_id') or '').strip()
            # 仅保留 unique_id 缺失但 short_id 存在的账号
            if unique_id in ('', '0') and short_id not in ('', '0'):
                mapping[sid] = short_id

    payload = {
        'meta': {
            'note': 'P0作者 short_id 映射：当缺少 sec_uid 时用于生成 /user/<short_id> 跳转链接（无法保证一定可在未登录态展示头像）',
            'coverage': len(mapping),
            'total': len(target_ids),
        },
        'shortIds': dict(sorted(mapping.items())),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(json.dumps({'coverage': len(mapping), 'total': len(target_ids)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
