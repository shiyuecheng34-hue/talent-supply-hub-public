import enrichment from '@/data/agencyEnrichment.json';
import profileUrls from '@/data/agencyProfileUrls.json';
import snapshot from '@/data/agencySnapshot.json';
import { douyinAvatarMap } from '@/data/douyinAvatarMap';
import { agencyPagination } from '@/lib/agencyPagination';
import { Download } from 'lucide-react';
import { useMemo, useState } from 'react';
import { AgencyAvatar } from './AgencyAvatar';
import { AgencyPager } from './AgencyPager';

const fields = [
  { key: 'industry', label: '行业' },
  { key: 'fans', label: '粉丝量级' },
  { key: 'tag', label: '内容标签' },
] as const;

const RATIO_HEADERS = [
  '达人粉丝小镇青年比例',
  '达人粉丝小镇中老年比例',
  '达人粉丝资深中产比例',
  '达人粉丝新锐白领比例',
  '达人粉丝都市银发比例',
  '达人粉丝Z世代比例',
  '达人粉丝精致妈妈比例',
  '达人粉丝都市蓝领比例',
] as const;

const PRICE_FILTERS = [
  { key: 'priceMid', label: '植入报价', source: '植入视频报价' },
  { key: 'priceLong', label: '定制报价', source: '定制视频报价' },
] as const;

const PRICE_BUCKETS = [
  { value: '', label: '全部区间' },
  { value: '0-10000', label: '1万以下' },
  { value: '10000-50000', label: '1–5万' },
  { value: '50000-100000', label: '5–10万' },
  { value: '100000-200000', label: '10–20万' },
  { value: '200000-', label: '20万以上' },
] as const;

type FilterState = {
  industry: string;
  fans: string;
  tag: string;
  priceMid: string;
  priceLong: string;
};

const EMPTY_FILTERS: FilterState = {
  industry: '',
  fans: '',
  tag: '',
  priceMid: '',
  priceLong: '',
};
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
// 「星图达人抖音昵称」与第二列达人昵称重复，不再展示。
const extraHeaders = enrichment.headers.filter(
  header =>
    ![
      '达人星图id',
      '植入视频报价',
      '定制视频报价',
      '星图达人抖音昵称',
    ].includes(header),
);
const xingtuProfile = (id: string) =>
  `https://www.xingtu.cn/ad/creator/author/douyin/${id}`;
const douyinProfile = (id: string) =>
  (profileUrls.profiles as Record<string, string>)[id] ??
  douyinAvatarMap[id]?.profileUrl ??
  null;
const priceAmount = (id: string, header: string) => {
  const raw = sourceValue(id, header);
  if (raw == null || raw === '' || raw === 'NULL') return null;
  const amount = Number(raw);
  return Number.isFinite(amount) ? amount : null;
};
const inPriceBucket = (amount: number | null, bucket: string) => {
  if (!bucket) return true;
  if (amount == null) return false;
  const [min, max] = bucket.split('-');
  if (max === '') return amount >= Number(min);
  return amount >= Number(min) && amount < Number(max);
};
const ratioPercent = (value: string | null | undefined) => {
  if (value == null || value === '' || value === 'NULL') return null;
  const ratio = Number(value);
  return Number.isFinite(ratio) ? ratio * 100 : null;
};
const csvEscape = (value: string | null | undefined) => {
  const text = value ?? '';
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

export function AgencyModule() {
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);
  const filtered = useMemo(
    () =>
      snapshot.records.filter(r => {
        const dimensionMatched = fields.every(
          ({ key }) => !filters[key] || r[key] === filters[key],
        );
        if (!dimensionMatched) return false;
        return (
          inPriceBucket(priceAmount(r.id, '植入视频报价'), filters.priceMid) &&
          inPriceBucket(priceAmount(r.id, '定制视频报价'), filters.priceLong)
        );
      }),
    [filters],
  );
  const pagination = agencyPagination(filtered.length, page);
  const downloadCsv = () => {
    const headers = [
      '达人昵称',
      '达人星图ID',
      '植入报价(元)',
      '定制报价(元)',
      '抖音主页',
      '星图主页',
      '行业',
      '粉丝量级',
      '内容标签',
      ...extraHeaders,
    ];
    const lines = filtered.map(r => {
      const id = r.id;
      const cells = [
        r.name,
        `="${id}"`,
        sourceValue(id, '植入视频报价') ?? '',
        sourceValue(id, '定制视频报价') ?? '',
        douyinProfile(id) ?? '',
        xingtuProfile(id),
        r.industry,
        r.fans,
        r.tag,
        ...extraHeaders.map(header => sourceValue(id, header) ?? ''),
      ];
      return cells.map(cell => csvEscape(String(cell))).join(',');
    });
    const csv = `\ufeff${[headers.join(','), ...lines].join('\r\n')}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `代理商重点达人_${new Date()
      .toISOString()
      .slice(0, 10)}_${filtered.length}位.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div id="module-content" className="enter agency-module">
      <section className="content-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">AGENCY · PRIORITY TALENTS</span>
            <h2>代理商重点达人</h2>
            <p>
              保留原底池；支持行业、粉丝量级、内容标签、植入报价、定制报价五项组合筛选，向右滚动查看全维度。
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
        <div className="flex flex-wrap gap-4 my-6 agency-filter-bar">
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
          {PRICE_FILTERS.map(({ key, label }) => (
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
                {PRICE_BUCKETS.map(bucket => (
                  <option key={bucket.value} value={bucket.value}>
                    {bucket.label}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <button
            type="button"
            className="text-cyan-300 self-end p-3"
            onClick={() => {
              setFilters(EMPTY_FILTERS);
              setPage(1);
            }}
          >
            重置筛选
          </button>
          <button
            type="button"
            className="agency-download-btn"
            onClick={downloadCsv}
          >
            <Download size={15} />
            点击下载表格
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
                  '抖音主页',
                  '星图主页',
                  '行业',
                  '粉丝量级',
                  '内容标签',
                  ...extraHeaders,
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
                  <td className="p-3">
                    {douyinProfile(r.id) ? (
                      <a
                        className="agency-home-link"
                        href={douyinProfile(r.id) ?? undefined}
                        target="_blank"
                        rel="noreferrer"
                      >
                        抖音主页 ↗
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="p-3">
                    <a
                      className="agency-home-link"
                      href={xingtuProfile(r.id)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      星图主页 ↗
                    </a>
                  </td>
                  <td className="p-3">{display(r.industry)}</td>
                  <td className="p-3">{r.fans}</td>
                  <td className="p-3">{display(r.tag)}</td>
                  {extraHeaders.map(header => {
                    const percent = ratioPercent(sourceValue(r.id, header));
                    if (
                      percent === null ||
                      !RATIO_HEADERS.includes(
                        header as (typeof RATIO_HEADERS)[number],
                      )
                    ) {
                      return (
                        <td className="p-3" key={header}>
                          {display(sourceValue(r.id, header))}
                        </td>
                      );
                    }
                    return (
                      <td className="p-3 ratio-cell" key={header}>
                        <div
                          className="ratio-bar"
                          aria-label={`${percent.toFixed(2)}%`}
                        >
                          <span
                            style={{ width: `${Math.min(percent, 100)}%` }}
                          />
                        </div>
                        <em>{percent.toFixed(2)}%</em>
                      </td>
                    );
                  })}
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
    </div>
  );
}
