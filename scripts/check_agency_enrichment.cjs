const assert = require('node:assert/strict');
const fs = require('node:fs');
const enrichment = require('../src/data/agencyEnrichment.json');
const snapshot = require('../src/data/agencySnapshot.json');
assert.equal(enrichment.headers.length, 16);
assert.equal(Object.keys(enrichment.records).length, 14903);
assert.equal(enrichment.meta.chartSheetMismatchRecords, 0);
assert.equal(enrichment.meta.limitReached, false);
for (const record of snapshot.records) {
  assert.equal(typeof record.id, 'string');
  assert.equal(enrichment.records[record.id].length, 16);
  assert.equal(enrichment.records[record.id][1], record.id);
}
const component = fs.readFileSync('src/components/AgencyModule.tsx', 'utf8');
assert(!component.includes('QianchuanLists'));
assert(component.includes("'植入报价',"));
assert(component.includes("'定制报价',"));
assert(component.includes('overflow-x-auto'));
assert(component.includes("value === '' || value === 'NULL'"));
assert(component.includes('Number.isFinite(amount)'));
const meta = JSON.parse(fs.readFileSync('site.meta', 'utf8'));
for (const name of [
  'agency-enrichment',
  'agency-enrichment-chart',
  'agency-avatar-mapping',
]) {
  assert(meta.datasources[name]);
  assert.deepEqual(Object.keys(meta.datasources[name]).sort(), [
    'provider',
    'uri',
  ]);
}
console.log(
  '14903字符串ID全量关联、16维度、报价与缺失兜底、源表与风神零差异、移除千川渲染、数据源声明校验通过。',
);
