#!/usr/bin/env python3
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
SOURCE_HTML = DIST / 'html' / 'main' / 'index.html'
AVATAR_SOURCE = ROOT / 'avatar-assets'
AVATAR_TARGET = DIST / 'avatars'


def main():
    if not SOURCE_HTML.exists():
        raise FileNotFoundError('请先运行 pnpm run build')
    shutil.copy2(SOURCE_HTML, DIST / 'index.html')
    if AVATAR_TARGET.exists():
        shutil.rmtree(AVATAR_TARGET)
    shutil.copytree(AVATAR_SOURCE, AVATAR_TARGET)
    print({
        'entry': str(DIST / 'index.html'),
        'avatars': len(list(AVATAR_TARGET.glob('*.jpg'))),
    })


if __name__ == '__main__':
    main()
