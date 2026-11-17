"""P0 作者头像缺口：按星图 ID 批量查询风神 5685026 的抖音 unique_id / short_id 映射。

- 输入：p0_data/p0_avatar_gap.json（现有图集未覆盖的星图 ID）
- 分区：2026-11-16（当前最新分区，旧分区缺失的 ID 在新分区可查）
- 输出：.cache/avatars/p0_latest/mapping-2026-11-16-<chunk>.json，断点续跑
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CACHE = WORKSPACE / '.cache/avatars/p0_latest'
GAP_FILE = WORKSPACE / 'p0_data/p0_avatar_gap.json'
AEOLUS_DIR = WORKSPACE / 'inner_skills/aeolus-platform-analysis'
DATASET_ID = '5685026'
PARTITION = '2026-11-16'
CHUNK_SIZE = 180


def run_query(sql: str) -> list[dict]:
    proc = subprocess.run(
        ['python3', 'scripts/dataset_sql_query.py', '--dataset-id', DATASET_ID, '--sql', sql],
        cwd=AEOLUS_DIR, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    text = proc.stdout.strip()
    if not text:
        raise RuntimeError(proc.stderr.strip() or 'empty command output')
    payload = json.loads(text)
    rows = payload.get('rows')
    if rows is None and payload.get('file'):
        rows = json.loads(Path(payload['file']).read_text()).get('rows', [])
    return rows or []


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    gap_ids = json.loads(GAP_FILE.read_text())
    chunks = [gap_ids[i:i + CHUNK_SIZE] for i in range(0, len(gap_ids), CHUNK_SIZE)]
    found: dict[str, dict] = {}
    for index, chunk in enumerate(chunks):
        out = CACHE / f'mapping-{PARTITION}-{index:03d}.json'
        if out.exists():
            rows = json.loads(out.read_text())
        else:
            in_list = ','.join(chunk)
            sql = (
                'SELECT `[达人星图id]`, `[抖音unique_id]`, `[抖音short_id]`, `[星图达人抖音昵称]` '
                'FROM `[【官】星图达人数据集]` '
                f"WHERE `[p_date]` = '{PARTITION}' AND `[达人星图id]` IN ({in_list}) LIMIT 10000"
            )
            rows = run_query(sql)
            out.write_text(json.dumps(rows, ensure_ascii=False))
            print(json.dumps({'chunk': index, 'requested': len(chunk), 'rows': len(rows)}, ensure_ascii=False), flush=True)
        for row in rows:
            found[str(row['star_author_id'])] = row
    missing = [sid for sid in gap_ids if sid not in found]
    (CACHE / 'mapping-missing.json').write_text(json.dumps(missing, ensure_ascii=False))
    summary = {'requested': len(gap_ids), 'matched': len(found), 'noPartitionRow': len(missing), 'chunks': len(chunks)}
    (CACHE / 'mapping-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
