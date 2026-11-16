#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Fetch real Douyin avatars for Agency module (A + B lists).

Source boundary (MUST keep):
  https://data.bytedance.net/aeolus/pages/dataQuery?appId=1002633&id=1791867289012435&isDefault=1&rid=17268794&sid=5685026

We only use the exported full table CSV from that DataQuery history/chart.

Because the exported columns do not include `unique_id`/`short_id`, this script uses:
  - 星图达人抖音昵称 (as candidate unique_id) when it is a valid unique_id;
  - otherwise marks it as `unmapped_handle`.

It is intentionally incremental + resumable:
  - success saves image immediately
  - status persisted in .cache/avatars/query_full_status.json

"""

from __future__ import annotations

import csv
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

REPO = Path(__file__).resolve().parents[1]
ASSETS_DIR = REPO / "avatar-assets"
DATA_DIR = REPO / "src" / "data"
CACHE_DIR = REPO.parent / ".cache" / "avatars"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

A_SNAPSHOT = DATA_DIR / "agencySnapshot.json"
B_OVERALL = DATA_DIR / "qianchuan-overall.json"
B_MONETIZATION = DATA_DIR / "qianchuan-monetization.json"

AEOLUS_EXPORT = REPO.parent / "viz_download_single_17268794_短直-查询表.csv"

STATUS_FILE = CACHE_DIR / "query_full_status.json"

OUT_TS = DATA_DIR / "avatarQueryOverrides.ts"

# Hard limits per user request
MAX_RETRIES = 2
PROFILE_TIMEOUT = 15
IMAGE_TIMEOUT = 20

HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "referer": "https://www.iesdouyin.com/",
    "accept": "application/json, text/plain, */*",
}


@dataclass
class TargetGroup:
    key: str
    title: str
    ids: List[str]


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_target_groups() -> List[TargetGroup]:
    a = _load_json(A_SNAPSHOT)
    a_ids = [str(r.get("id")) for r in a.get("records", []) if r.get("id")]

    b1 = _load_json(B_OVERALL)
    b1_ids = [str(r.get("id")) for r in b1.get("records", []) if r.get("id")]

    b2 = _load_json(B_MONETIZATION)
    b2_ids = [str(r.get("id")) for r in b2.get("records", []) if r.get("id")]

    return [
        TargetGroup(key="A", title="A·代理商重点", ids=a_ids),
        TargetGroup(key="B_overall", title="B·整体底池", ids=b1_ids),
        TargetGroup(key="B_monetization", title="B·千川代理关注变现", ids=b2_ids),
    ]


def read_aeolus_mapping(csv_path: Path) -> Dict[str, Dict[str, str]]:
    """Return mapping: star_id -> {nickname, douyin_uid}."""
    if not csv_path.exists():
        raise FileNotFoundError(str(csv_path))

    out: Dict[str, Dict[str, str]] = {}
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = (row.get("达人星图id") or "").strip()
            if not sid:
                continue
            out[sid] = {
                "nick": (row.get("星图达人抖音昵称") or "").strip(),
                "douyin_uid": (row.get("抖音用户UID") or "").strip(),
            }
    return out


def load_status() -> Dict[str, Any]:
    if STATUS_FILE.exists():
        with STATUS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "version": 1,
        "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ids": {},
    }


def save_status(status: Dict[str, Any]) -> None:
    tmp = STATUS_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
    tmp.replace(STATUS_FILE)


def is_success(status_entry: Dict[str, Any]) -> bool:
    return status_entry.get("status") == "ok" and bool(status_entry.get("avatarPath"))


def try_fetch_profile_by_unique_id(unique_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    url = f"https://www.iesdouyin.com/web/api/v2/user/info/?unique_id={unique_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=PROFILE_TIMEOUT)
        data = r.json()
    except Exception as e:
        return None, f"profile_request_error: {e}"

    if not isinstance(data, dict):
        return None, "profile_bad_json"

    if data.get("status_code") != 0:
        return None, f"profile_status_code_{data.get('status_code')}"

    ui = data.get("user_info")
    if not isinstance(ui, dict):
        return None, "profile_missing_user_info"

    return ui, None


def pick_avatar_url(user_info: Dict[str, Any]) -> Optional[str]:
    for k in ["avatar_medium", "avatar_thumb", "avatar_larger"]:
        obj = user_info.get(k)
        if isinstance(obj, dict):
            urls = obj.get("url_list")
            if isinstance(urls, list) and urls:
                for u in urls:
                    if isinstance(u, str) and u.startswith("http"):
                        return u
    return None


def download_image(url: str, out_path: Path) -> Optional[str]:
    try:
        r = requests.get(url, headers={"user-agent": HEADERS["user-agent"], "referer": "https://www.douyin.com/"}, timeout=IMAGE_TIMEOUT)
        if r.status_code != 200:
            return f"image_http_{r.status_code}"
        content = r.content
        if not content or len(content) < 1024:
            return "image_too_small"
        out_tmp = out_path.with_suffix(out_path.suffix + ".tmp")
        out_tmp.write_bytes(content)
        out_tmp.replace(out_path)
        return None
    except Exception as e:
        return f"image_request_error: {e}"


def parse_existing_overrides_ts(path: Path) -> Dict[str, Dict[str, str]]:
    """Very small parser for the existing TS literal object."""
    if not path.exists():
        return {}

    text = path.read_text("utf-8")
    # match blocks like: 'id': { ... avatarUrl: '/avatars/query-id.jpg', ... }
    blocks = re.findall(r"'(?P<id>\d+)':\s*\{(?P<body>[^}]*?)\}\s*,", text, flags=re.S)
    out: Dict[str, Dict[str, str]] = {}
    for sid, body in blocks:
        def pick(key: str) -> str:
            m = re.search(rf"{re.escape(key)}\s*:\s*'([^']*)'", body)
            return m.group(1) if m else ""

        out[sid] = {
            "uniqueId": pick("uniqueId"),
            "shortId": pick("shortId"),
            "displayId": pick("displayId"),
            "nickName": pick("nickName"),
            "profileUrl": pick("profileUrl"),
            "avatarUrl": pick("avatarUrl"),
        }
    return out


def write_overrides_ts(
    overrides: Dict[str, Dict[str, str]],
    meta: Dict[str, Any],
) -> None:
    lines: List[str] = []
    lines.append("// Auto-generated by scripts/fetch_avatars_from_query_full.py")
    lines.append("// Do not edit manually.")
    lines.append("")
    lines.append("import type { DouyinAvatarRecord } from './douyinAvatarMap';")
    lines.append("")
    lines.append("export const avatarQueryOverridesMeta = " + json.dumps(meta, ensure_ascii=False, indent=2) + " as const;")
    lines.append("")
    lines.append("export const avatarQueryOverrides: Record<string, DouyinAvatarRecord> = {")

    def esc_ts_string(v: str) -> str:
        return (v or "").replace("\\\\", "\\\\\\\\").replace("'", "\\'")

    for sid in sorted(overrides.keys(), key=lambda x: int(x)):
        rec = overrides[sid]
        lines.append(f"  '{sid}': {{")
        lines.append(f"    uniqueId: '{esc_ts_string(rec.get('uniqueId',''))}',")
        lines.append(f"    shortId: '{esc_ts_string(rec.get('shortId',''))}',")
        lines.append(f"    displayId: '{esc_ts_string(rec.get('displayId',''))}',")
        lines.append(f"    nickName: '{esc_ts_string(rec.get('nickName',''))}',")
        lines.append(f"    profileUrl: '{esc_ts_string(rec.get('profileUrl',''))}',")
        lines.append(f"    avatarUrl: '{esc_ts_string(rec.get('avatarUrl',''))}',")
        lines.append("  },")

    lines.append("};")
    lines.append("")

    OUT_TS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    groups = load_target_groups()
    all_ids: List[str] = []
    for g in groups:
        all_ids.extend(g.ids)

    union_ids = sorted(set(all_ids), key=lambda x: int(x))

    aeolus_map = read_aeolus_mapping(AEOLUS_EXPORT)

    status = load_status()
    ids_status: Dict[str, Any] = status.setdefault("ids", {})

    existing = parse_existing_overrides_ts(OUT_TS)

    downloaded_before = sum(1 for sid, s in ids_status.items() if isinstance(s, dict) and is_success(s))

    stats = {
        "total_union_ids": len(union_ids),
        "in_aeolus": 0,
        "not_in_aeolus": 0,
        "attempted": 0,
        "ok": 0,
        "failed": 0,
        "unmapped_handle": 0,
        "skipped_existing_ok": 0,
    }

    # Ensure output dir exists
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for i, sid in enumerate(union_ids, start=1):
        if sid in existing:
            # Already has override in code; treat as ok and skip network.
            stats["skipped_existing_ok"] += 1
            if sid not in ids_status:
                ids_status[sid] = {
                    "status": "ok",
                    "source": "existing_override",
                    "avatarPath": existing[sid].get("avatarUrl"),
                }
            continue

        m = aeolus_map.get(sid)
        if not m:
            stats["not_in_aeolus"] += 1
            ids_status.setdefault(sid, {"status": "not_in_aeolus"})
            continue

        stats["in_aeolus"] += 1
        nick = (m.get("nick") or "").strip()

        if not nick:
            stats["unmapped_handle"] += 1
            ids_status.setdefault(sid, {"status": "unmapped_handle", "reason": "empty_nick"})
            continue

        # Resume
        s0 = ids_status.get(sid)
        if isinstance(s0, dict) and is_success(s0):
            stats["skipped_existing_ok"] += 1
            continue

        # Attempt fetch with limited retries
        stats["attempted"] += 1
        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            ui, err = try_fetch_profile_by_unique_id(nick)
            if err:
                last_err = err
                # backoff
                time.sleep(0.4 + random.random() * 0.6)
                continue

            avatar_src = pick_avatar_url(ui)
            if not avatar_src:
                last_err = "profile_no_avatar"
                time.sleep(0.2)
                continue

            out_name = f"query-{sid}.jpg"
            out_path = ASSETS_DIR / out_name
            img_err = download_image(avatar_src, out_path)
            if img_err:
                last_err = img_err
                time.sleep(0.4 + random.random() * 0.6)
                continue

            unique_id_real = str(ui.get("unique_id") or nick)
            short_id = str(ui.get("short_id") or "")
            nickname_real = str(ui.get("nickname") or "")
            display_id = unique_id_real or short_id or nick

            existing[sid] = {
                "uniqueId": unique_id_real,
                "shortId": short_id,
                "displayId": display_id,
                "nickName": nickname_real.replace("'", "\\'"),
                "profileUrl": f"https://www.douyin.com/search/{display_id}?type=user",
                "avatarUrl": f"/avatars/{out_name}",
            }

            ids_status[sid] = {
                "status": "ok",
                "attempts": attempt,
                "nickCandidate": nick,
                "uniqueId": unique_id_real,
                "shortId": short_id,
                "avatarPath": str(out_path),
                "avatarUrl": existing[sid]["avatarUrl"],
            }
            save_status(status)
            stats["ok"] += 1
            last_err = None
            break

        if last_err:
            ids_status[sid] = {
                "status": "failed",
                "nickCandidate": nick,
                "error": last_err,
            }
            save_status(status)
            stats["failed"] += 1
            if last_err.startswith("profile_status_code_5"):
                stats["unmapped_handle"] += 1

        # be nice
        time.sleep(0.05 + random.random() * 0.08)

        if i % 500 == 0:
            print(f"progress {i}/{len(union_ids)} ok={stats['ok']} failed={stats['failed']} ...")

    meta = {
        "sourceAeoQuery": str(AEOLUS_EXPORT),
        "sourceBoundaryUrl": "https://data.bytedance.net/aeolus/pages/dataQuery?appId=1002633&id=1791867289012435&isDefault=1&rid=17268794&sid=5685026",
        "generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "totalUnionIds": stats["total_union_ids"],
        "alreadyHadOverrides": len(parse_existing_overrides_ts(OUT_TS)),
        "downloadedBefore": downloaded_before,
        "downloadedNow": stats["ok"],
        "failedNow": stats["failed"],
        "note": "由于该 DataQuery 导出列不包含 unique_id/short_id，本脚本仅以‘星图达人抖音昵称’作为 unique_id 候选进行 user/info 查询；不合法时会计入 unmapped_handle。",
    }

    write_overrides_ts(existing, meta)

    # final stats persisted
    status["lastRun"] = {
        "at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stats": stats,
    }
    save_status(status)

    print(json.dumps({"stats": stats, "statusFile": str(STATUS_FILE), "outTs": str(OUT_TS)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
