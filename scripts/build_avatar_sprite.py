#!/usr/bin/env python3
import math
import re
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / 'avatar-assets'
MAP_FILE = ROOT / 'src' / 'data' / 'douyinAvatarMap.ts'
SPRITE_FILE = ASSET_DIR / 'avatar-sprite.jpg'
TILE = 100
COLUMNS = 40


def main():
    files = sorted(path for path in ASSET_DIR.glob('*.jpg') if path.name != SPRITE_FILE.name)
    rows = math.ceil(len(files) / COLUMNS)
    sprite = Image.new('RGB', (COLUMNS * TILE, rows * TILE), '#102744')
    positions: dict[str, str] = {}
    for index, path in enumerate(files):
        x = (index % COLUMNS) * TILE
        y = (index // COLUMNS) * TILE
        with Image.open(path) as image:
            tile = ImageOps.fit(image.convert('RGB'), (TILE, TILE), method=Image.Resampling.LANCZOS)
        sprite.paste(tile, (x, y))
        display_x = (index % COLUMNS) * 56
        display_y = (index // COLUMNS) * 56
        positions[path.stem] = f'-{display_x}px -{display_y}px'
    sprite.save(SPRITE_FILE, 'JPEG', quality=84, optimize=True, progressive=True)

    content = MAP_FILE.read_text(encoding='utf-8')
    content = content.replace(
        'avatarUrl: string;\n};',
        'avatarUrl: string;\n  avatarPosition?: string;\n};',
        1,
    )
    for star_id, position in positions.items():
        pattern = re.compile(
            rf"('{star_id}':\s*\{{[\s\S]*?avatarUrl:\s*)'/avatars/{star_id}\.jpg'"
        )
        content = pattern.sub(
            rf"\1'/avatars/avatar-sprite.jpg',\n    avatarPosition: '{position}'",
            content,
            count=1,
        )
        position_pattern = re.compile(
            rf"('{star_id}':\s*\{{[\s\S]*?avatarPosition:\s*)'[^']+'"
        )
        content = position_pattern.sub(rf"\1'{position}'", content, count=1)
    MAP_FILE.write_text(content, encoding='utf-8')
    print({
        'avatars': len(files),
        'sprite': str(SPRITE_FILE),
        'size': SPRITE_FILE.stat().st_size,
        'dimensions': [COLUMNS * TILE, rows * TILE],
    })


if __name__ == '__main__':
    main()
