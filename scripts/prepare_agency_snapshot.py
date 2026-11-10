"""仅转换指定图表完整导出，保留并校验原图表限制。"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
chart = json.loads((ROOT.parent / 'aeolus_pull_chart_19913768_20261110T190822.json').read_text())
filters = chart['simpleChart']['filters']
allowed = set(next(f['detail']['value'] for f in filters if f['datasetFieldId'] == '10000038313360'))
with (ROOT.parent / 'viz_download_single_19913768_代理P0关注.csv').open(newline='') as f:
    raw = list(csv.reader(f))
headers, rows = raw[0], raw[1:]
assert len(raw) == 14904  # 下载工具rowCount包含表头，实际数据14903行
assert all(row[0] in allowed for row in rows), 'ID超出原图表白名单'
records = [dict(id=r[0], name=r[1], industry=r[2], tag=r[3], fans=r[4]) for r in rows]
ids = {r['id'] for r in records}
meta = dict(exportedAt='2026-11-10 19:07:54 CST', partitionMax='2026-11-09', rowCount=len(rows), uniqueIds=len(ids), whitelistCount=len(allowed), missingWhitelistIds=len(allowed-ids), source='https://data.bytedance.net/aeolus/pages/dataQuery?appId=1002633&rid=19913768&sid=5685026', filters=filters, limitReached=False)
(ROOT / 'src/data/agencySnapshot.json').write_text(json.dumps(dict(meta=meta, records=records), ensure_ascii=False))
print({k:v for k,v in meta.items() if k!='filters'})
print({key: sorted({r[key] for r in records}) for key in ['industry','fans','tag']})
