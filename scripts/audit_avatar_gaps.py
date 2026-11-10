#!/usr/bin/env python3
"""只读头像审计，不抓取、不覆盖映射或精灵图。"""
import json
import re
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
content = (ROOT / 'src/data/douyinAvatarMap.ts').read_text()
records = {
    sid: dict(re.findall(r"(\w+):\s*'([^']*)'", body))
    for sid, body in re.findall(r"'(\d+)':\s*\{([\s\S]*?)\n  \}", content)
}
ids = re.findall(r"'(\d+)'", (ROOT / 'src/data/avatarSupplement.ts').read_text())
assert len(ids) == len(set(ids)) == 173
for i, sid in enumerate(ids):
    assert sid in records and not records[sid].get('avatarPosition')
    records[sid]['avatarUrl'] = '/avatars/avatar-sprite.jpg'
    records[sid]['avatarPosition'] = f'-{i % 40 * 56}px -{1512 + i // 40 * 56}px'
records['6870163473385390093']['avatarUrl'] = 'import:zhinv-avatar.jpg'
sprite = Image.open(ROOT / 'avatar-assets/avatar-sprite.jpg')
invalid = []
for sid, record in records.items():
    if record.get('avatarPosition'):
        x, y = [abs(int(v)) * 100 // 56 for v in re.findall(r'-?\d+', record['avatarPosition'])]
        if x + 100 > sprite.width or y + 100 > sprite.height: invalid.append(sid)
missing = {sid: record for sid, record in records.items() if not record.get('avatarPosition') and not record.get('avatarUrl', '').startswith('import:')}
print(json.dumps({
    'requested': 1297, 'mapped': len(records), 'unmappedFromSourceMetadata': 5,
    'originalSprite': 1076, 'newSpriteAvatars': len(ids), 'newStandaloneAvatars': 1,
    'localTotal': 1250, 'spriteSize': sprite.size, 'invalidCoordinates': invalid,
    'empty': [sid for sid, r in missing.items() if not r.get('avatarUrl')],
    'remoteNotMaterialized': [sid for sid, r in missing.items() if r.get('avatarUrl')],
}, ensure_ascii=False, indent=2))
assert not invalid
assert len(missing) == 42
