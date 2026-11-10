import snapshot from '@/data/agencySnapshot.json';
import { useMemo, useState } from 'react';

const entries = [
  {
    title: '整体底池',
    url: 'https://mmm.bytedance.net/apps/bi/new-analyze?v=5gklF%2F05tHoEtfBmb5Mvx1GXlKCjKEllV1AWviXAAK5xmHBVXvCHypuzjGUjahX1',
  },
  {
    title: '千川代理未变现',
    url: 'https://mmm.bytedance.net/apps/bi/new-analyze?v=5gklF%2F05tHoEtfBmb5MvxzIyoPCYPYJIBygikB6s5tFbIJZrC7J17LHZYdOVjSXQ',
  },
];
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
  const pages = Math.max(1, Math.ceil(filtered.length / 50));
  return (
    <div id="module-content" className="enter">
      <section className="content-section">
        <span className="eyebrow">A · AGENCY PRIORITIES</span>
        <h2>代理商重点</h2>
        <p>静态快照 · 非实时 · 导出于 {snapshot.meta.exportedAt}</p>
        <p>
          原图表「代理P0关注」：保留 p_date 最近有数日（data_days，偏移 0）与{' '}
          {snapshot.meta.whitelistCount.toLocaleString()} 个达人 ID
          白名单。元信息最新分区：{snapshot.meta.partitionMax}。
        </p>
        <p>
          完整导出 {snapshot.meta.rowCount.toLocaleString()} 条 /{' '}
          {snapshot.meta.uniqueIds.toLocaleString()}{' '}
          位达人，未触达上限；白名单中 24 个 ID
          未返回，不补齐、不扩池。粉丝量级直接使用原字段 W
          档位（W=万），不推算精确粉丝数。NULL 单独展示。
        </p>
        <a
          href={snapshot.meta.source}
          target="_blank"
          rel="noreferrer"
          className="text-cyan-300 underline"
        >
          查看风神原图表与限制 ↗
        </a>
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
              {filtered.slice((page - 1) * 50, page * 50).map(r => (
                <tr key={r.id}>
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
        <div className="flex gap-4 items-center mt-6">
          <button disabled={page === 1} onClick={() => setPage(page - 1)}>
            上一页
          </button>
          <span>
            {page} / {pages}
          </span>
          <button disabled={page >= pages} onClick={() => setPage(page + 1)}>
            下一页
          </button>
        </div>
      </section>
      <section id="qianchuan-agencies" className="content-section mt-6">
        <span className="eyebrow">B · QIANCHUAN AGENCIES</span>
        <h2>千川代理商</h2>
        <p>
          仅提供真实分析入口。云端浏览器访问两条链接均跳转字节 SSO
          登录，未能读取业务数据或确认可嵌入接口；不展示虚构统计。请使用有权限的账号在新窗口登录查看。
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          {entries.map(entry => (
            <a
              key={entry.title}
              href={entry.url}
              target="_blank"
              rel="noreferrer"
              className="rounded-2xl border border-slate-600 bg-slate-900 p-6"
            >
              <h3 className="text-xl text-cyan-300">{entry.title} ↗</h3>
              <p className="mt-3">打开 MMM 原始分析页 · 需 SSO 与业务权限</p>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
