"""把 Q4-优质潜力P0.xlsx 转成前端使用的紧凑 JSON。

- 星图 ID 全程保持字符串，避免长整型精度丢失
- 字面量 'NULL' 与空白统一转成 null
- 数值列（画像比例、双报价）保留数字类型，0 报价按代理商模块同口径展示为 ¥0
- 行采用数组结构而非对象，控制 5w+ 行的产物体积
"""
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / 'p0_data/Q4-P0.xlsx'
OUT = ROOT / 'src/data/p0Authors.json'

TEXT_COLUMNS = {0, 1, 2, 3, 4, 5}


def normalize(value, is_text):
    if value is None:
        return None
    if is_text:
        text = str(value).strip()
        if text == '' or text.upper() == 'NULL':
            return None
        return text
    if isinstance(value, str):
        text = value.strip()
        if text == '' or text.upper() == 'NULL':
            return None
        try:
            value = float(text)
        except ValueError:
            return text
    # 整数浮点去掉无意义 .0
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb['Sheet1']
    iterator = ws.iter_rows(values_only=True)
    headers = [str(cell).strip() for cell in next(iterator)]

    rows = []
    seen = set()
    for raw in iterator:
        if all(cell is None or (isinstance(cell, str) and not cell.strip()) for cell in raw):
            continue
        row = [normalize(cell, idx in TEXT_COLUMNS) for idx, cell in enumerate(raw)]
        star_id = row[1]
        if not star_id or star_id in seen:
            continue
        seen.add(star_id)
        rows.append(row)

    payload = {
        'meta': {
            'source': 'Q4-优质潜力P0.xlsx',
            'sourceUrl':
                'https://bytedance.larkoffice.com/file/PIn7bKeXYoCN7AxmLeEcrk6on7c',
            'total': len(rows),
        },
        'headers': headers,
        'rows': rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')),
                   encoding='utf-8')
    size_mb = OUT.stat().st_size / 1e6
    print(f'written {OUT} rows={len(rows)} size={size_mb:.2f}MB')


if __name__ == '__main__':
    main()
