const assert = require('node:assert/strict');
const fs = require('node:fs');
const ts = require('typescript');
function load(path) {
  const e = {};
  new Function(
    'exports',
    'require',
    ts.transpile(fs.readFileSync(path, 'utf8'), {
      module: ts.ModuleKind.CommonJS,
    }),
  )(e, asset =>
    asset.endsWith('.jpg') || asset.endsWith('.png')
      ? { default: asset }
      : load(
          require('node:path').join(
            require('node:path').dirname(path),
            `${asset}.ts`,
          ),
        ),
  );
  return e;
}
const { douyinAvatarMap: avatars } = load('src/data/douyinAvatarMap.ts');
const { agencyPagination: paginate } = load('src/lib/agencyPagination.ts');
for (const [key, rows, unique, lastSize] of [
  ['overall', 13112, 13101, 12],
  ['monetization', 12435, 12424, 35],
]) {
  const s = require(`../src/data/qianchuan-${key}.json`);
  assert.equal(s.records.length, rows);
  assert.equal(new Set(s.records.map(r => r.id)).size, unique);
  assert.equal(s.meta.lastDataRow, s.meta.physicalRows);
  assert(s.records.every(r => typeof r.id === 'string' && /^\d+$/.test(r.id)));
  const rebuilt = [];
  const pages = paginate(rows, 1).totalPages;
  for (let p = 1; p <= pages; p++) {
    const b = paginate(rows, p);
    rebuilt.push(...s.records.slice(b.offset, b.end));
  }
  assert.deepEqual(rebuilt, s.records);
  const last = paginate(rows, pages);
  assert.equal(last.end - last.offset, lastSize);
  const covered = s.records.filter(r => avatars[r.id]?.avatarUrl);
  console.log({
    key,
    rows,
    unique,
    pages,
    lastPageRows: lastSize,
    avatarRows: covered.length,
    avatarUniqueIds: new Set(covered.map(r => r.id)).size,
    nameFallbackRows: rows - covered.length,
  });
}
const app = fs.readFileSync('src/components/AgencyModule.tsx', 'utf8');
assert.equal((app.match(/<AgencyPager/g) || []).length, 1);
assert(!app.includes('查看风神原图表与限制'));
assert(!app.includes('MMM'));
assert(app.includes('setPage(1)'));
console.log('两表完整性、字符串ID、独立全量分页、指定展示删除检查通过');
