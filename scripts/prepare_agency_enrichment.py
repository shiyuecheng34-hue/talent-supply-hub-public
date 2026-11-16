"""只读全量导出本地关联；原底池及筛选口径保持不变。"""
import csv
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEET = 'https://bytedance.larkoffice.com/sheets/A3Lxs0tpeh7mxZtl11icVQUrnBe?sheet=d1e6f9'
CHART = 'https://data.bytedance.net/aeolus/pages/dataQuery?appId=1002633&rid=20057009&sid=5685026'


def main():
    base = json.loads((ROOT / 'src/data/agencySnapshot.json').read_text())
    with open('/tmp/agency-sheet.csv', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        headers = [h for h in reader.fieldnames if h]
        sheet = [{h: r[h] for h in headers} for r in reader]
    with (ROOT.parent / 'viz_download_single_20057009_【代理商】-激励部分达人.csv').open(encoding='utf-8-sig', newline='') as f:
        chart = list(csv.DictReader(f))
    assert len(base['records']) == len(sheet) == len(chart) == 14903
    assert len(headers) == 16
    source = {r['达人星图id']: r for r in sheet}
    comparison = {r['达人星图id']: r for r in chart}
    assert len(source) == len(comparison) == 14903
    assert set(source) == {r['id'] for r in base['records']}
    mismatches = sum(source[sid] != comparison.get(sid) for sid in source)
    changes = {key: sum(r[key] != source[r['id']][label] for r in base['records']) for key, label in [('name', '星图达人抖音昵称'), ('industry', '一级行业'), ('fans', '达人粉段'), ('tag', '标签')]}
    metadata = {'capturedAt': time.strftime('%Y-%m-%d %H:%M:%S CST'), 'sheetModifiedAt': '2026-11-16 21:53:38 CST', 'sheetRevision': 11, 'sourceSheet': SHEET, 'referenceChart': CHART, 'baseSnapshotAt': base['meta']['exportedAt'], 'basePartition': base['meta']['partitionMax'], 'chartExportRowsIncludingHeader': 14904, 'sheetRows': len(sheet), 'chartRows': len(chart), 'joined': len(source), 'missing': 0, 'chartSheetMismatchRecords': mismatches, 'baseFieldDifferences': changes, 'limitReached': False, 'note': '报价优先飞书源表 O/P 列（植入视频报价/定制视频报价）；与风神全量导出逐字段核对。原底池字段保留，源表全部维度单独展示。Q:T四个空列非维度。'}
    # 数组压缩字段重复开销；星图ID从未转为Number。
    payload = {'meta': metadata, 'headers': headers, 'records': {sid: [r[h] for h in headers] for sid, r in source.items()}}
    (ROOT / 'src/data/agencyEnrichment.json').write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
