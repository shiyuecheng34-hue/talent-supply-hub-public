"""构建行业/节点样本达人头像分片精灵图与真实主页映射。

覆盖 11 个行业样本（1,099）+ 4 个节点样本（215）并集 1,296 个星图 ID，
头像来源按优先级：
1. 本轮补抓缓存 .cache/avatars/industry_latest（status=ok）
2. 代理商 ok 缓存 .cache/avatars/agency_latest（原图 avatar-assets/agency-<id>.jpg）
3. 旧行业精灵图 avatar-assets/avatar-sprite.jpg 按历史坐标裁切
   （历史坐标为 56px 网格，原图 4000x3200 由 2240x1792 放大 1.7857 倍，
   实际瓦片为 100px，需按 col*100/row*100 裁切）
4. avatarSupplement.ts 追加区（56 网格 y=1512 起，即实际 row 27 起）
无可用头像的 ID 不进入精灵图，页面保留姓名首字兜底。

输出：
- src/assets/industry-avatar-sprite-<n>.jpg（分片，随构建进入 dist）
- src/data/industryAvatarSprites.ts（ID → 分片/坐标）
- src/data/industryTalentProfiles.json（ID → 真实 sec_uid 主页 + 抖音号）
- src/data/industryAvatarAudit.json（覆盖审计）
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
INDUSTRY_CACHE = ROOT.parent / '.cache/avatars/industry_latest'
AGENCY_CACHE = ROOT.parent / '.cache/avatars/agency_latest'
TILE, DISPLAY, COLS, PER_SHARD = 72, 56, 16, 1024

industry_ids = set(
    re.findall(r"\n\s{6,}'(\d{19})',\n\s+'\d", (ROOT / 'src/data/industrySamples.ts').read_text())
)
node_ids = set(
    re.findall(r"^\s+'(\d{19})',$", (ROOT / 'src/data/nodeSamples.ts').read_text(), re.M)
)
target_ids = sorted(industry_ids | node_ids)

# ---- 1. 收集三类头像来源 ----
industry_ok = {}
for path in INDUSTRY_CACHE.glob('*.json'):
    data = json.loads(path.read_text())
    if data.get('status') == 'ok':
        industry_ok[data['id']] = data['record']

agency_ok = {}
for path in AGENCY_CACHE.glob('*.json'):
    if path.name.startswith('mapping-'):
        continue
    data = json.loads(path.read_text())
    if isinstance(data, dict) and data.get('status') == 'ok':
        agency_ok[data['id']] = data['record']

old_blocks = dict(
    re.findall(r"'(\d{19})': \{(.*?)\n  \}", (ROOT / 'src/data/douyinAvatarMap.ts').read_text(), re.S)
)
old_sprite = Image.open(ROOT / 'avatar-assets/avatar-sprite.jpg').convert('RGB')
# 旧精灵图：56px 坐标网格 → 100px 实际像素（4000/2240 = 3200/1792 = 1.7857）
GRID, PIXEL, SUP_COL0_ROW = 56, 100, 27
supplement_text = (ROOT / 'src/data/avatarSupplement.ts').read_text()
supplement_index = {
    sid: index
    for index, sid in enumerate(re.findall(r"'(\d{19})'", supplement_text))
}

# 代理商映射（displayId 兜底）
agency_mapping = {}
for path in AGENCY_CACHE.glob('mapping-*.json'):
    for row in json.loads(path.read_text()):
        agency_mapping[row['star_author_id']] = row

avatar_sources = []  # (id, PIL.Image)
source_counter = Counter()
profiles = {}

for sid in target_ids:
    profile_url = None
    display_id = ''

    if sid in industry_ok:
        rec = industry_ok[sid]
        image_path = ROOT / 'avatar-assets' / f'industry-{sid}.jpg'
        with Image.open(image_path) as im:
            avatar_sources.append((sid, im.convert('RGB').copy()))
        source_counter['industry_fetch'] += 1
        profile_url = rec.get('secUid') and f"https://www.douyin.com/user/{rec['secUid']}"
        display_id = rec.get('displayId') or rec.get('uniqueId') or ''

    elif sid in agency_ok:
        rec = agency_ok[sid]
        image_path = ROOT / 'avatar-assets' / f'agency-{sid}.jpg'
        with Image.open(image_path) as im:
            avatar_sources.append((sid, im.convert('RGB').copy()))
        source_counter['agency_cache'] += 1
        profile_url = rec.get('secUid') and f"https://www.douyin.com/user/{rec['secUid']}"
        display_id = rec.get('displayId') or rec.get('uniqueId') or ''

    elif sid in old_blocks and 'avatarPosition' in old_blocks[sid]:
        body = old_blocks[sid]
        gx, gy = (abs(int(v)) for v in re.search(
            r"avatarPosition: '(-?\d+)px (-?\d+)px'", body).groups())
        x, y = gx // GRID * PIXEL, gy // GRID * PIXEL
        tile = old_sprite.crop((x, y, x + PIXEL, y + PIXEL))
        avatar_sources.append((sid, tile.copy()))
        source_counter['legacy_sprite_crop'] += 1
        match = re.search(r"profileUrl:\n?\s*'(https[^']+)'", body)
        if match and '/user/' in match.group(1):
            profile_url = match.group(1)
        display_id = re.search(r"displayId: '([^']*)'", body).group(1)

    elif sid in supplement_index:
        # 运行时 supplementalAvatarIds 仅给无坐标条目追加头像，不含 sec_uid 深链
        index = supplement_index[sid]
        x = (index % 40) * PIXEL
        y = (SUP_COL0_ROW + index // 40) * PIXEL
        tile = old_sprite.crop((x, y, x + PIXEL, y + PIXEL))
        avatar_sources.append((sid, tile.copy()))
        source_counter['legacy_supplement_crop'] += 1
        if sid in old_blocks:
            match = re.search(r"displayId: '([^']*)'", old_blocks[sid])
            if match:
                display_id = match.group(1)

    # displayId 兜底：旧 map → 代理商映射
    if not display_id and sid in old_blocks:
        m = re.search(r"displayId: '([^']*)'", old_blocks[sid])
        if m:
            display_id = m.group(1)
    if not display_id and sid in agency_mapping:
        row = agency_mapping[sid]
        display_id = str(row.get('aweme_unique_id') or row.get('aweme_short_id') or '')

    profiles[sid] = {'profileUrl': profile_url, 'displayId': display_id}

avatar_sources.sort(key=lambda item: item[0])
covered_ids = {sid for sid, _ in avatar_sources}

# ---- 2. 生成分片精灵图 ----
imports, entries, shards = [], [], []
for shard, offset in enumerate(range(0, len(avatar_sources), PER_SHARD)):
    chunk = avatar_sources[offset:offset + PER_SHARD]
    rows = math.ceil(len(chunk) / COLS)
    sprite = Image.new('RGB', (COLS * TILE, rows * TILE), '#102744')
    name = f'industry-avatar-sprite-{shard}.jpg'
    imports.append(f"import sprite{shard} from '../assets/{name}';")
    for index, (sid, image) in enumerate(chunk):
        col, row = index % COLS, index // COLS
        tile = ImageOps.fit(image, (TILE, TILE), method=Image.Resampling.LANCZOS)
        sprite.paste(tile, (col * TILE, row * TILE))
        entries.append(
            f"  '{sid}': {{ avatarUrl: sprite{shard}, avatarPosition: '-{col * DISPLAY}px -{row * DISPLAY}px', "
            f"spriteSize: [{COLS * DISPLAY}, {rows * DISPLAY}] }},"
        )
    destination = ROOT / 'src/assets' / name
    sprite.save(destination, 'JPEG', quality=78, optimize=True, progressive=True)
    shards.append({'file': name, 'count': len(chunk), 'bytes': destination.stat().st_size})

ts_content = (
    '\n'.join(imports)
    + "\n\ntype IndustrySprite = { avatarUrl: string; avatarPosition: string; spriteSize: [number, number] };\n"
    + "export const industryAvatarSprites: Record<string, IndustrySprite> = {\n"
    + '\n'.join(entries)
    + '\n};\n'
)
(ROOT / 'src/data/industryAvatarSprites.ts').write_text(ts_content)

profiles_json = {
    'meta': {
        'source': 'industry fetch + agency cache + legacy sprite; iesdouyin user/info via 数据集5685026',
        'generatedAt': '2026-11-17',
        'targets': len(target_ids),
        'avatarCovered': len(covered_ids),
        'deepLinkCovered': sum(1 for v in profiles.values() if v['profileUrl']),
        'note': 'profileUrl 仅收录 sec_uid 真实主页深链；无法核验的账号为 null，页面不输出伪链接。',
    },
    'profiles': dict(sorted(profiles.items())),
}
(ROOT / 'src/data/industryTalentProfiles.json').write_text(
    json.dumps(profiles_json, ensure_ascii=False, indent=2)
)

audit = {
    'targets': len(target_ids),
    'industryTargets': len(industry_ids),
    'nodeTargets': len(node_ids),
    'unionTargets': len(target_ids),
    'avatarCovered': len(covered_ids),
    'avatarCoverage': round(len(covered_ids) / len(target_ids), 4),
    'avatarBreakdown': dict(source_counter),
    'deepLinkCovered': sum(1 for v in profiles.values() if v['profileUrl']),
    'displayIdCovered': sum(1 for v in profiles.values() if v['displayId']),
    'unresolved': len(target_ids) - len(covered_ids),
    'shards': shards,
}
(ROOT / 'src/data/industryAvatarAudit.json').write_text(
    json.dumps(audit, ensure_ascii=False, indent=2)
)
print(json.dumps(audit, ensure_ascii=False))
