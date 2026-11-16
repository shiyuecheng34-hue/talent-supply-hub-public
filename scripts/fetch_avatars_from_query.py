#!/usr/bin/env python3
"""Fetch Douyin avatar images for a limited set of Xingtu talent IDs.

Strict scope rule:
- Only consider Xingtu IDs that appear in the provided Aeolus query result file
  (exported from the user-provided Aeolus DataQuery URL).
- Use the existing local mapping cache (xingtuId -> uniqueId/shortId) for handle lookup.

This script is intentionally incremental:
- Writes downloaded jpgs into avatar-assets/
- Emits a small TS overrides file which can be applied on top of src/data/douyinAvatarMap.ts

Usage:
  python3 scripts/fetch_avatars_from_query.py \
    --query-file ../aeolus_query_17268794_78673846.json \
    --mapping-cache .cache/avatars/dataset_mapping_cache.json \
    --limit 30
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

import requests


def safe_filename(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", value)


def douyin_user_info(key: str, value: str, timeout: int = 15) -> dict:
    url = f"https://www.iesdouyin.com/web/api/v2/user/info/?{key}={urllib.parse.quote(value)}"
    resp = requests.get(
        url,
        headers={
            "user-agent": "Mozilla/5.0",
            "accept": "application/json, text/plain, */*",
            "referer": "https://www.iesdouyin.com/",
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def pick_avatar_url(payload: dict) -> str | None:
    user_info = (payload or {}).get("user_info") or {}
    # Prefer medium; fall back to thumb.
    for field in ("avatar_medium", "avatar_thumb"):
        node = user_info.get(field) or {}
        url_list = node.get("url_list") or []
        if url_list:
            return str(url_list[0])
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-file", required=True)
    parser.add_argument("--mapping-cache", required=True)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument(
        "--out-ts",
        default="src/data/avatarQueryOverrides.ts",
        help="TS overrides output (relative to repo root)",
    )
    parser.add_argument(
        "--out-dir",
        default="avatar-assets",
        help="Image output dir (relative to repo root)",
    )
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    query_file = Path(args.query_file).expanduser().resolve()
    mapping_cache = (repo_root / args.mapping_cache).resolve()
    out_ts = (repo_root / args.out_ts).resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    query = json.loads(query_file.read_text("utf-8"))
    rows = query.get("rows") or []
    if not rows:
        raise SystemExit(f"No rows found in query file: {query_file}")

    # Column label may vary; tolerate both.
    def get_xingtu_id(row: dict) -> str | None:
        for k in ("达人星图id", "达人星图 ID", "达人星图Id"):
            if k in row and row[k] not in (None, ""):
                return str(row[k]).strip()
        return None

    xingtu_ids = [i for i in (get_xingtu_id(r) for r in rows) if i]
    xingtu_id_set = set(xingtu_ids)

    mapping = json.loads(mapping_cache.read_text("utf-8"))

    picked: list[tuple[str, dict]] = []
    for x_id in xingtu_ids:
        rec = mapping.get(x_id)
        if not isinstance(rec, dict):
            continue
        unique_id = str(rec.get("uniqueId") or "").strip()
        short_id = str(rec.get("shortId") or "").strip()
        if not unique_id and not short_id:
            continue
        picked.append((x_id, rec))
        if len(picked) >= args.limit:
            break

    overrides: dict[str, dict] = {}
    downloaded = 0
    failed = 0

    for x_id, rec in picked:
        unique_id = str(rec.get("uniqueId") or "").strip()
        short_id = str(rec.get("shortId") or "").strip()
        display_id = str(rec.get("displayId") or unique_id or short_id).strip()

        key, value = ("unique_id", unique_id) if unique_id else ("short_id", short_id)

        try:
            payload = douyin_user_info(key, value)
            avatar_remote = pick_avatar_url(payload)
            if not avatar_remote:
                failed += 1
                continue

            # Download jpg
            jpg_name = f"query-{safe_filename(x_id)}.jpg"
            jpg_path = out_dir / jpg_name
            img = requests.get(
                avatar_remote,
                headers={"user-agent": "Mozilla/5.0", "referer": "https://www.iesdouyin.com/"},
                timeout=20,
            )
            img.raise_for_status()
            jpg_path.write_bytes(img.content)
            downloaded += 1

            overrides[x_id] = {
                "uniqueId": unique_id,
                "shortId": short_id,
                "displayId": display_id,
                "nickName": str(rec.get("nickName") or ""),
                "profileUrl": str(rec.get("profileUrl") or ""),
                "avatarUrl": f"/avatars/{jpg_name}",
            }
        except Exception:
            failed += 1
        finally:
            time.sleep(args.sleep)

    meta = {
        "sourceQueryFile": str(query_file),
        "sourceMappingCache": os.path.relpath(mapping_cache, repo_root),
        "pickedFromQuery": len(picked),
        "downloaded": downloaded,
        "failed": failed,
        "note": "仅对出现在指定 DataQuery 返回结果中的星图达人ID做增量补抓；handle 来自本地 mapping cache，头像来自 iesdouyin user/info 接口。",
    }

    out_ts.parent.mkdir(parents=True, exist_ok=True)
    out_ts.write_text(
        "// Auto-generated by scripts/fetch_avatars_from_query.py\n"
        "// Do not edit manually.\n\n"
        "import type { DouyinAvatarRecord } from './douyinAvatarMap';\n\n"
        f"export const avatarQueryOverridesMeta = {json.dumps(meta, ensure_ascii=False, indent=2)} as const;\n\n"
        f"export const avatarQueryOverrides: Record<string, DouyinAvatarRecord> = {json.dumps(overrides, ensure_ascii=False, indent=2)};\n",
        "utf-8",
    )

    print(
        json.dumps(
            {
                "queryRows": len(rows),
                "queryUniqueXingtuIds": len(xingtu_id_set),
                "picked": len(picked),
                "downloaded": downloaded,
                "failed": failed,
                "outTs": os.path.relpath(out_ts, repo_root),
                "outDir": os.path.relpath(out_dir, repo_root),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
