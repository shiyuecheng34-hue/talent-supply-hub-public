import snapshot from '@/data/agencySnapshot.json';
import { agencyPagination } from '@/lib/agencyPagination';
import { useMemo, useState } from 'react';
import { AgencyAvatar } from './AgencyAvatar';
import { AgencyPager } from './AgencyPager';

import { QianchuanLists } from './QianchuanLists';
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
const display = (value: string) =>
  value === 'NULL' ? '未提供（NULL）' : value;
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
    <div id="module-content" className="enter">
      <section className="content-section">
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
          <span>SNAPSHOT · 风神图表</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr>
                {[
                  '达人头像',
                  '达人昵称',
                  '达人星图 ID',
                  '行业',
                  '粉丝量级',
                  '内容标签',
                ].map(h => (
                  <th className="p-3 border-b border-slate-700" key={h}>
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
                  <td className="p-3">{display(r.industry)}</td>
                  <td className="p-3">{r.fans}</td>
                  <td className="p-3">{display(r.tag)}</td>
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
      <section id="qianchuan-agencies" className="content-section mt-6">
        <span className="eyebrow">B · QIANCHUAN AGENCIES</span>
        <h2>千川代理商</h2>
        <QianchuanLists />
      </section>
    </div>
  );
}
