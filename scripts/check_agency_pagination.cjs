const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
const exportsObject = {};
new Function(
  'exports',
  ts.transpile(fs.readFileSync('src/lib/agencyPagination.ts', 'utf8'), {
    module: ts.ModuleKind.CommonJS,
  }),
)(exportsObject);
const { agencyPagination: paginate } = exportsObject;
const { records } = require('../src/data/agencySnapshot.json');
for (const total of [0, 1, 49, 50, 51, 100, 101, 14903]) {
  const pages = Math.max(1, Math.ceil(total / 50));
  let covered = 0;
  for (let page = 1; page <= pages; page++) {
    const p = paginate(total, page);
    assert(p.end - p.offset <= 50);
    assert.equal(p.offset, covered);
    covered = p.end;
    assert(p.pageNumbers.includes(page));
    assert(p.pageNumbers.includes(1) && p.pageNumbers.includes(pages));
  }
  assert.equal(covered, total);
  assert.equal(paginate(total, -1).page, 1);
  assert.equal(paginate(total, pages + 1).page, pages);
}
const allIds = [];
for (let page = 1; page <= 299; page++) {
  const p = paginate(records.length, page);
  allIds.push(...records.slice(p.offset, p.end).map(r => r.id));
}
assert.deepEqual(
  allIds,
  records.map(r => r.id),
);
assert.equal(new Set(allIds).size, 14903);
const last = paginate(records.length, 299);
assert.equal(last.end - last.offset, 3);
const filtered = records.filter(r => r.industry === records[0].industry);
assert.equal(paginate(filtered.length, 1).offset, 0);
const component = fs.readFileSync('src/components/AgencyModule.tsx', 'utf8');
assert(component.includes('setPage(1)'));
assert(component.includes('snapshot.records.filter'));
assert(component.includes('AgencyAvatar id={r.id} name={r.name}'));
console.log(
  '分页边界0/1/49/50/51/100/101/14903通过；全299页无遗漏无重复，末页3条；全池筛选和重置第一页代码校验通过。',
);
