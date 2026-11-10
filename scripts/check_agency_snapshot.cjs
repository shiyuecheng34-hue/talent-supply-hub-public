const assert = require('node:assert/strict');
const s = require('../src/data/agencySnapshot.json');
const allowed = new Set(
  s.meta.filters.find(f => f.datasetFieldId === '10000038313360').detail.value,
);
assert.equal(s.records.length, 14903);
assert.equal(new Set(s.records.map(r => r.id)).size, 14903);
assert(s.records.every(r => allowed.has(r.id)));
const fields = ['industry', 'fans', 'tag'];
const filter = f =>
  s.records.filter(r => fields.every(k => !f[k] || r[k] === f[k]));
assert.equal(filter({}).length, 14903);
for (const key of fields) {
  for (const value of new Set(s.records.map(r => r[key]))) {
    const result = filter({ [key]: value });
    assert(result.length > 0 && result.every(r => r[key] === value));
  }
}
const first = s.records[0];
const combo = filter({
  industry: first.industry,
  fans: first.fans,
  tag: first.tag,
});
assert(combo.length && combo.length < s.records.length);
assert.equal(filter({ industry: '不存在的行业' }).length, 0);
assert.equal(
  s.meta.filters.find(f => f.type === 'whereDate').detail.dateMode,
  'data_days',
);
console.log({
  rows: s.records.length,
  whitelist: allowed.size,
  outsideWhitelist: 0,
  combinationMatches: combo.length,
  fieldOptions: Object.fromEntries(
    fields.map(k => [k, new Set(s.records.map(r => r[k])).size]),
  ),
  checks: '全部单字段选项、组合、清空与空结果通过',
});
