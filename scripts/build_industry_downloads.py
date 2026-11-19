#!/usr/bin/env python3
"""从完整飞书导出构建行业下载快照，校验行数和长 ID，不使用页面样本。"""
import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_HEADERS = {
    '推荐优先级',
    '是否补充推荐',
    '星图作者一级分类(T-3标签)',
    '星图作者二级分类(T-3标签)',
}
GROUPS = [
    ('industry-beauty', '美妆', 7389),
    ('industry-food', '食品饮料', 1969),
    ('industry-fashion', '服装配饰', 2761),
    ('industry-mom', '母婴宠物', 1733),
    ('industry-care', '日化', 5728),
    ('industry-health', '医药健康', 1801),
    ('industry-digital', '3C及电器', 5204),
    ('industry-auto', '汽车', 3221),
    ('industry-game', '游戏', 29215),
    ('industry-commerce', '互联网电商服务', 9986),
    ('industry-finance', '金融业', 2131),
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
        # 飞书导出的 dimension 可能为 A1，必须遍历真实单元格而非信任它。
        sheet.reset_dimensions()
        iterator = sheet.iter_rows(values_only=True)
        headers = list(next(iterator))[:29]
        assert len(headers) == 29 and headers[0] == '达人星图id'
        forbidden_indices = {
            index
            for index, value in enumerate(headers)
            if isinstance(value, str) and value.strip() in FORBIDDEN_HEADERS
        }
        assert forbidden_indices, '未找到需要移除的敏感列，请检查源表字段'
        allowed_indices = [
            index for index in range(len(headers)) if index not in forbidden_indices
        ]
        rows = [list(row[:29]) for row in iterator if any(v is not None and str(v).strip() for v in row)]
        assert len(rows) == expected, (label, len(rows), expected)
        for row in rows:
            for index in (0, 1):
                value = row[index]
                if isinstance(value, int) and abs(value) <= 2**53 - 1:
                    row[index] = str(value)
            assert isinstance(row[0], str) and row[0].isdigit(), (label, row[0])
        filtered_headers = [headers[index] for index in allowed_indices]
        assert not any(
            isinstance(value, str) and value.strip() in FORBIDDEN_HEADERS
            for value in filtered_headers
        )
        filtered_rows = [[row[index] for index in allowed_indices] for row in rows]
        data = {
            'headers': filtered_headers,
            'rows': filtered_rows,
            'source': 'snapshot',
            'capturedAt': captured_at,
        }
        (target / f'{binding_id}.data').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        counts[binding_id] = len(rows)
    workbook.close()
    print(json.dumps({'capturedAt': captured_at, 'counts': counts, 'total': sum(counts.values())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
