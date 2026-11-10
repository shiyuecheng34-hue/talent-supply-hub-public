import concurrent.futures
import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [('overall', 'Vdvls4mgshxZ8AtWHOWcGbQTn3c', '6ba567', 13113), ('monetization', 'KR2ZsG8AyhhMgStbxpecPn2unk7', '4d254b', 12436)]

def read(token, sid, start, end):
    result = json.loads(subprocess.check_output(['lark-cli','sheets','+cells-get','--spreadsheet-token',token,'--sheet-id',sid,'--range',f'A{start}:B{end}','--include','value'], text=True))
    assert result['ok']
    data = result['data']
    assert data.get('warning_message') is not None
    assert not data['has_more']
    r = data['ranges'][0]
    assert not r['truncated']
    assert r['row_indices'] == list(range(start, end+1))
    return list(zip(r['row_indices'], [[c.get('value','') for c in row] for row in r['cells']]))

for key, token, sid, count in SOURCES:
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(read,token,sid,start,min(count,start+999)) for start in range(1,count+1,1000)]
        rows = sorted([row for f in futures for row in f.result()])
    assert len(rows) == count
    assert rows[0][1] == ['星图达人id','达人昵称']
    records = []
    for n, values in rows[1:]:
        if not any(values): continue
        id, name = values
        assert isinstance(id,str) and id.isdigit(), (n,id)
        records.append({'id':id,'name':str(name),'sourceRow':n})
    meta = {'sheetId':sid,'sheetName':'Sheet1','source':f'https://bytedance.larkoffice.com/sheets/{token}?sheet={sid}','physicalRows':count,'lastDataRow':records[-1]['sourceRow'],'rows':len(records),'uniqueIds':len({r['id'] for r in records}),'readAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'revision':4}
    (ROOT/f'src/data/qianchuan-{key}.json').write_text(json.dumps({'meta':meta,'records':records},ensure_ascii=False))
    print(meta, 'last:', records[-1], flush=True)
