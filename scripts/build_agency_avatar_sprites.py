"""新增A模块头像分片图集；不修改既有行业/节点精灵图或坐标。"""
import json
import math
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/agency_latest'
TILE, DISPLAY, COLS, PER_SHARD = 72, 56, 16, 1024


def main():
    target_ids = {r['id'] for r in json.loads((ROOT / 'src/data/agencySnapshot.json').read_text())['records']}
    successes = []
    for path in CACHE.glob('*.json'):
        if path.name.startswith('mapping-'):
            continue
        status = json.loads(path.read_text())
        sid = status['id']
        if status['status'] == 'ok' and sid in target_ids:
            image_path = ROOT / 'avatar-assets' / f'agency-{sid}.jpg'
            assert image_path.exists()
            successes.append((sid, image_path))
    successes.sort()
    imports, entries, shards = [], [], []
    for shard, offset in enumerate(range(0, len(successes), PER_SHARD)):
        chunk = successes[offset:offset + PER_SHARD]
        rows = math.ceil(len(chunk) / COLS)
        sprite = Image.new('RGB', (COLS * TILE, rows * TILE), '#102744')
        name = f'agency-avatar-sprite-{shard}.jpg'
        imports.append(f"import sprite{shard} from '../assets/{name}';")
        for index, (sid, image_path) in enumerate(chunk):
            col, row = index % COLS, index // COLS
            with Image.open(image_path) as im:
                tile = ImageOps.fit(im.convert('RGB'), (TILE, TILE), method=Image.Resampling.LANCZOS)
            sprite.paste(tile, (col * TILE, row * TILE))
            entries.append(f"  '{sid}': {{ avatarUrl: sprite{shard}, avatarPosition: '-{col * DISPLAY}px -{row * DISPLAY}px', spriteSize: [{COLS * DISPLAY}, {rows * DISPLAY}] }},")
        destination = ROOT / 'src/assets' / name
        sprite.save(destination, 'JPEG', quality=78, optimize=True, progressive=True)
        shards.append({'file': name, 'count': len(chunk), 'bytes': destination.stat().st_size})
    content = '\n'.join(imports) + '\n\ntype AgencySprite = { avatarUrl: string; avatarPosition: string; spriteSize: [number, number] };\nexport const agencyAvatarSprites: Record<string, AgencySprite> = {\n' + '\n'.join(entries) + '\n};\n'
    (ROOT / 'src/data/agencyAvatarSprites.ts').write_text(content)
    report = {'avatars': len(successes), 'shards': shards, 'note': '分片图片通过src/assets import进入构建，原图留作断点缓存不进入dist。'}
    (ROOT / 'src/data/agencySpriteAudit.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
