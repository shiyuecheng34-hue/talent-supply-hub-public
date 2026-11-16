#!/usr/bin/env python3
"""准备可部署目录：仅复制代码实际引用的历史头像，不携带agency散图。"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


def main():
    source = DIST / 'html/main/index.html'
    if not source.exists():
        raise FileNotFoundError('请先运行 pnpm run build')
    shutil.copy2(source, DIST / 'index.html')
    shutil.rmtree(DIST / 'html')
    target = DIST / 'avatars'
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    required = set()
    for filename in ['douyinAvatarMap.ts', 'avatarQueryOverrides.ts']:
        text = (ROOT / 'src/data' / filename).read_text()
        required.update(re.findall(r"/avatars/([A-Za-z0-9_-]+\.jpg)", text))
    assert not any(name.startswith('agency-') for name in required)
    for name in sorted(required):
        shutil.copy2(ROOT / 'avatar-assets' / name, target / name)
    for path in DIST.rglob('.env*'):
        if path.is_file():
            path.unlink()
    files = [p for p in DIST.rglob('*') if p.is_file()]
    assert len(files) < 1124, f'部署文件数超限：{len(files)}'
    assert not any(re.fullmatch(r'agency-\d+\.jpg', p.name) for p in files), '新增头像应由分片图集承载'
    print({'entry': str(DIST / 'index.html'), 'legacyAvatars': len(required), 'totalFiles': len(files), 'agencyLooseFiles': 0})


if __name__ == '__main__':
    main()
