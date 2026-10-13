#!/usr/bin/env python3
import base64
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_FILE = ROOT / 'src' / 'data' / 'douyinAvatarMap.ts'
AVATAR_DIR = ROOT / 'public' / 'avatars'


def download(item: tuple[str, str]) -> tuple[str, str, bool]:
    star_id, url = item
    target = AVATAR_DIR / f'{star_id}.jpg'
    if target.exists() and target.stat().st_size > 500:
        return star_id, url, True
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.douyin.com/',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = response.read()
        if len(payload) < 500:
            return star_id, url, False
        target.write_bytes(payload)
        return star_id, url, True
    except Exception:
        return star_id, url, False


def main():
    content = MAP_FILE.read_text(encoding='utf-8')
    records = re.findall(
        r"'(\d+)':\s*\{[\s\S]*?avatarUrl:\s*'([^']+)'",
        content,
    )
    remote = [(star_id, url) for star_id, url in records if url.startswith('http')]
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    success = 0
    replacements: list[tuple[str, str, str]] = []
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(download, item): item for item in remote}
        for future in as_completed(futures):
            star_id, url, ok = future.result()
            if ok:
                success += 1
                replacements.append((star_id, url, f'/avatars/{star_id}.jpg'))
    embedded = 0
    for star_id, remote_url in remote:
        target = AVATAR_DIR / f'{star_id}.jpg'
        if not target.exists() or target.stat().st_size <= 500:
            continue
        data_url = 'data:image/jpeg;base64,' + base64.b64encode(target.read_bytes()).decode('ascii')
        content = content.replace(f"'{remote_url}'", f"'{data_url}'", 1)
        embedded += 1
    MAP_FILE.write_text(content, encoding='utf-8')
    print({
        'requested': len(remote),
        'downloaded': success,
        'embedded': embedded,
        'directory': str(AVATAR_DIR),
    })


if __name__ == '__main__':
    main()
