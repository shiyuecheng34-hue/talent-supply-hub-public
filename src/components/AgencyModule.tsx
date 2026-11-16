import enrichment from '@/data/agencyEnrichment.json';
import snapshot from '@/data/agencySnapshot.json';
import { agencyPagination } from '@/lib/agencyPagination';
import { useMemo, useState } from 'react';
import { AgencyAvatar } from './AgencyAvatar';
import { AgencyBookletRail } from './AgencyBookletRail';
import { AgencyPager } from './AgencyPager';

const fields = [
  { key: 'industry', label: '行业' },
  { key: 'fans', label: '粉丝量级' },
  { key: 'tag', label: '内容标签' },
] as const;
const options = Object.fromEntries(
  fields.map(({ key }) => [
    key,
    [...new Set(snapshot.records.map(r => r[key]))].sort(),
  ]),
);
const sourceRows: Record<string, (string | null)[]> = enrichment.records;
const sourceIndex = (name: string) => enrichment.headers.indexOf(name);
const sourceValue = (id: string, name: string) =>
  sourceRows[id]?.[sourceIndex(name)];
const display = (value: string | null | undefined) =>
  value === 'NULL'
    ? '未提供（NULL）'
    : value == null || value === ''
      ? '—'
      : value;
const price = (value: string | null | undefined) => {
  if (value == null || value === '' || value === 'NULL') return '—';
  const amount = Number(value);
  return Number.isFinite(amount)
    ? `¥${amount.toLocaleString('zh-CN')}`
    : display(value);
};
const extraHeaders = enrichment.headers.filter(
  header => !['达人星图id', '植入视频报价', '定制视频报价'].includes(header),
);

export function AgencyModule() {
  const [filters, setFilters] = useState({ industry: '', fans: '', tag: '' });
  const [page, setPage] = useState(1);
  const filtered = useMemo(
    () =>
      snapshot.records.filter(r =>
        fields.every(({ key }) => !filters[key] || r[key] === filters[key]),
      ),
    [filters],
  );
  const pagination = agencyPagination(filtered.length, page);
  return (
    <div id="module-content" className="enter agency-module">
      <section className="content-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">AGENCY · PRIORITY TALENTS</span>
            <h2>代理商重点达人</h2>
            <p>
              保留原底池与三项筛选口径；新增报价及源表全维度，向右滚动查看。
            </p>
          </div>
          <a
            className="source-link"
            href={enrichment.meta.sourceSheet}
            target="_blank"
            rel="noreferrer"
          >
            飞书报价与维度源表 ↗
          </a>
        </div>
        <p className="text-sm text-slate-400 mt-4">
          底池快照：{snapshot.meta.exportedAt} · 增量采集：
          {enrichment.meta.capturedAt} · 源表修订{' '}
          {enrichment.meta.sheetRevision}
          <br />
          植入报价＝21–60s；定制报价＝60s+（元）；0
          按原值展示，不代表缺失。源表与底池存在跨时间差异，新增列标注「源表」。
        </p>
        <div className="flex flex-wrap gap-4 my-6">
          {fields.map(({ key, label }) => (
            <label key={key} className="flex flex-col gap-2 text-sm">
              {label}
              <select
                className="rounded-lg border border-slate-600 bg-slate-900 p-3 text-slate-100"
                value={filters[key]}
                onChange={e => {
                  setFilters({ ...filters, [key]: e.target.value });
                  setPage(1);
                }}
              >
                <option value="">全部{label}</option>
                {options[key].map(value => (
                  <option key={value} value={value}>
                    {display(value)}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <button
            type="button"
            className="text-cyan-300 self-end p-3"
            onClick={() => {
              setFilters({ industry: '', fans: '', tag: '' });
              setPage(1);
            }}
          >
            重置筛选
          </button>
        </div>
        <div className="result-line">
          <span>
            当前匹配 {filtered.length.toLocaleString()} 位 · 全快照筛选 · 每页
            50 位
          </span>
          <a
            href={enrichment.meta.referenceChart}
            target="_blank"
            rel="noreferrer"
          >
            全量核对 · 风神图表 ↗
          </a>
        </div>
        <div
          className="overflow-x-auto agency-table-scroll"
          aria-label="代理商全维度表格，可横向滚动"
        >
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead>
              <tr>
                {[
                  '达人头像',
                  '达人昵称',
                  '达人星图 ID',
                  '植入报价',
                  '定制报价',
                  '行业',
                  '粉丝量级',
                  '内容标签',
                  ...extraHeaders.map(h => `源表 · ${h}`),
                ].map(h => (
                  <th
                    className="p-3 border-b border-slate-700"
                    scope="col"
                    key={h}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(pagination.offset, pagination.end).map(r => (
                <tr key={r.id}>
                  <td className="p-3">
                    <AgencyAvatar id={r.id} name={r.name} />
                  </td>
                  <td className="p-3">{r.name}</td>
                  <td className="p-3">{r.id}</td>
                  <td className="p-3">
                    {price(sourceValue(r.id, '植入视频报价'))}
                  </td>
                  <td className="p-3">
                    {price(sourceValue(r.id, '定制视频报价'))}
                  </td>
                  <td className="p-3">{display(r.industry)}</td>
                  <td className="p-3">{r.fans}</td>
                  <td className="p-3">{display(r.tag)}</td>
                  {extraHeaders.map(header => (
                    <td className="p-3" key={header}>
                      {display(sourceValue(r.id, header))}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {!filtered.length && (
            <p className="p-6">
              没有符合当前组合筛选的达人，请重置或调整条件。
            </p>
          )}
        </div>
        <AgencyPager
          total={filtered.length}
          page={pagination.page}
          onChange={setPage}
        />
      </section>
      <AgencyBookletRail />
    </div>
  );
}
