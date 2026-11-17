"""P0 作者头像分片图集；独立分片，不修改既有代理/行业/节点精灵图与坐标。"""
import json
import math
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT.parent / '.cache/avatars/p0_latest'
ASSETS = ROOT / 'avatar-assets'
TILE, DISPLAY, COLS, PER_SHARD = 72, 56, 16, 1024


def main():
    data = json.loads((ROOT / 'src/data/p0Authors.json').read_text())
    # 按页面行序排布分片：同一页的 50 位达人尽量落在同一张分片图，减少请求数。
    order = [row[1] for row in data['rows']]
    target_ids = set(order)
    successes_by_id = {}
    for path in CACHE.glob('*.json'):
        if path.name.startswith('mapping'):
            continue
        status = json.loads(path.read_text())
        sid = str(status['id'])
        if status.get('status') == 'ok' and sid in target_ids:
            image_path = ASSETS / f'p0-{sid}.jpg'
            assert image_path.exists(), image_path
            successes_by_id[sid] = image_path
    successes = [(sid, successes_by_id[sid]) for sid in order if sid in successes_by_id]
    imports, entries, shards = [], [], []
    for shard, offset in enumerate(range(0, len(successes), PER_SHARD)):
        chunk = successes[offset:offset + PER_SHARD]
        rows = math.ceil(len(chunk) / COLS)
        sprite = Image.new('RGB', (COLS * TILE, rows * TILE), '#102744')
        name = f'p0-avatar-sprite-{shard}.jpg'
        imports.append(f"import sprite{shard} from '../assets/{name}';")
        for index, (sid, image_path) in enumerate(chunk):
            col, row = index % COLS, index // COLS
            with Image.open(image_path) as im:
                tile = ImageOps.fit(im.convert('RGB'), (TILE, TILE), method=Image.Resampling.LANCZOS)
            sprite.paste(tile, (col * TILE, row * TILE))
            entries.append(
                f"  '{sid}': {{ avatarUrl: sprite{shard}, avatarPosition: '-{col * DISPLAY}px -{row * DISPLAY}px', "
                f'spriteSize: [{COLS * DISPLAY}, {rows * DISPLAY}] }},'
            )
        destination = ROOT / 'src/assets' / name
        sprite.save(destination, 'JPEG', quality=78, optimize=True, progressive=True)
        shards.append({'file': name, 'count': len(chunk), 'bytes': destination.stat().st_size})
    content = (
        '\n'.join(imports)
        + '\n\ntype P0Sprite = { avatarUrl: string; avatarPosition: string; spriteSize: [number, number] };\n'
        + 'export const p0AvatarSprites: Record<string, P0Sprite> = {\n'
        + '\n'.join(entries)
        + '\n};\n'
    )
    (ROOT / 'src/data/p0AvatarSprites.ts').write_text(content)
    report = {
        'avatars': len(successes),
        'shards': shards,
        'note': 'P0 独立分片；原图留作缓存不进入 dist。',
    }
    (ROOT / 'src/data/p0SpriteAudit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
