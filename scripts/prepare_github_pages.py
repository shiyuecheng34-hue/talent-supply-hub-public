#!/usr/bin/env python3
"""将 EdenX 构建产物改写为可部署到 GitHub Pages 仓库子路径。"""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


def replace_or_fail(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f'未找到待替换内容: {old}')
    return text.replace(old, new)


def patch_index() -> None:
    index = DIST / 'index.html'
    text = index.read_text()
    text = replace_or_fail(text, 's.p="/"', 's.p="./"')
    text = text.replace(' src="/static/', ' src="./static/')
    text = text.replace(' href="/static/', ' href="./static/')
    index.write_text(text)
    shutil.copy2(index, DIST / '404.html')


def patch_routes_manifest() -> None:
    manifest = DIST / 'routes-manifest.json'
    data = json.loads(manifest.read_text())
    for route in data.get('routeAssets', {}).values():
        route['assets'] = [asset.replace('/static/', './static/') for asset in route.get('assets', [])]
        route['referenceCssAssets'] = [
            asset.replace('/static/', './static/')
            for asset in route.get('referenceCssAssets', [])
        ]
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main() -> None:
    if not (DIST / 'index.html').exists():
        raise FileNotFoundError('请先运行 pnpm run build 并执行 prepare_dist.py')
    patch_index()
    patch_routes_manifest()
    print({'index': str(DIST / 'index.html'), 'fallback': str(DIST / '404.html')})


if __name__ == '__main__':
    main()
