#!/usr/bin/env python3
"""从完整飞书导出构建节点下载快照，供公网版展示与下载复用。"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [
    ('node-1111', '双11', 16500),
    ('node-1212', '双12', 16500),
    ('node-newyear', '跨年_元旦', 16500),
    ('node-christmas', '平安夜_圣诞', 16500),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('workbook')
    args = parser.parse_args()
    workbook = openpyxl.load_workbook(args.workbook, read_only=True, data_only=True)
    target = ROOT / 'download-assets'
    target.mkdir(exist_ok=True)
    captured_at = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
    counts = {}
    for binding_id, label, expected in GROUPS:
        sheet = workbook[label]
        sheet.reset_dimensions()
        iterator = sheet.iter_rows(values_only=True)
        headers = list(next(iterator))[:40]
        assert len(headers) == 40 and headers[0] == '节点', (label, headers[:3])
        rows = [list(row[:40]) for row in iterator if any(v is not None and str(v).strip() for v in row)]
        assert len(rows) == expected, (label, len(rows), expected)
        for row in rows:
            for index in (6,):
                value = row[index]
                if isinstance(value, int) and abs(value) <= 2**53 - 1:
                    row[index] = str(value)
        data = {
            'headers': headers,
            'rows': rows,
            'source': 'snapshot',
            'capturedAt': captured_at,
        }
        (target / f'{binding_id}.data').write_text(
            json.dumps(data, ensure_ascii=False, separators=(',', ':')),
            encoding='utf-8',
        )
        counts[binding_id] = len(rows)
    workbook.close()
    print(json.dumps({'capturedAt': captured_at, 'counts': counts, 'total': sum(counts.values())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
