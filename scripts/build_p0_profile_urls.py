"""P0 作者抖音主页重建：合并代理、行业与 P0 抓取的 sec_uid 真实深链。

- 只收录可拼成 https://www.douyin.com/user/<sec_uid> 的真实 sec_uid
- 无 sec_uid 的账号不生成链接，页面不输出伪链接
- 输入：src/data/agencyProfileUrls.json、src/data/industryTalentProfiles.json、
  .cache/avatars/p0_latest/*.json（抓取状态，record.secUid）
- 输出：src/data/p0ProfileUrls.json（id → sec_uid，URL 由前端拼接，控制产物体积）
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/p0_latest'
USER_URL = re.compile(r'^https://www\.douyin\.com/user/([A-Za-z0-9_\-]+)$')


def sec_uid_of(value) -> str | None:
    """从主页 URL 或 {profileUrl} 结构中提取 sec_uid。"""
    if isinstance(value, str):
        match = USER_URL.match(value)
        return match.group(1) if match else None
    if isinstance(value, dict):
        return sec_uid_of(value.get('profileUrl') or '')
    return None


def main():
    data = json.loads((ROOT / 'src/data/p0Authors.json').read_text())
    target_ids = {row[1] for row in data['rows']}
    profiles: dict[str, str] = {}

    sources = [
        ROOT / 'src/data/agencyProfileUrls.json',
        ROOT / 'src/data/industryTalentProfiles.json',
    ]
    for path in sources:
        payload = json.loads(path.read_text())
        for sid, value in (payload.get('profiles') or {}).items():
            sec_uid = sec_uid_of(value)
            if sec_uid:
                profiles[sid] = sec_uid

    for path in CACHE.glob('*.json'):
        if path.name.startswith('mapping'):
            continue
        status = json.loads(path.read_text())
        if status.get('status') != 'ok':
            continue
        record = status.get('record') or {}
        sec_uid = str(record.get('secUid') or '')
        if sec_uid and USER_URL.match(f'https://www.douyin.com/user/{sec_uid}'):
            profiles[str(status['id'])] = sec_uid

    scoped = {sid: sec_uid for sid, sec_uid in profiles.items() if sid in target_ids}
    assert all(USER_URL.match(f'https://www.douyin.com/user/{uid}') for uid in scoped.values())
    payload = {
        'meta': {
            'note': 'P0作者抖音主页 sec_uid，只收录已核验的真实主页；无 sec_uid 的账号不生成链接',
            'coverage': len(scoped),
            'total': len(data['rows']),
        },
        'profiles': dict(sorted(scoped.items())),
    }
    (ROOT / 'src/data/p0ProfileUrls.json').write_text(
        json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n'
    )
    print(json.dumps({'coverage': len(scoped), 'total': len(data['rows']),
                      'gap': len(data['rows']) - len(scoped)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
