import { agencyPagination } from '@/lib/agencyPagination';
import { downloadRowsTable } from '@/lib/tableCsv';
import { Download, LoaderCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { AgencyPager } from './AgencyPager';
import { P0Avatar } from './P0Avatar';

type P0Row = (string | number | null)[];
type P0Data = {
  meta: { total: number; source: string };
  headers: string[];
  rows: P0Row[];
};
type P0ProfileDoc = { profiles: Record<string, string> };
type P0ShortDoc = { shortIds: Record<string, string> };

const NAME = 0;
const ID = 1;
const INDUSTRY = 2;
const SUB_INDUSTRY = 3;
const TAG = 4;
const FANS = 5;
const RATIO_START = 6;
const RATIO_END = 14;
const PRICE_MID = 14;
const PRICE_LONG = 15;

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

// 与代理商重点达人 enrichment 同源的 16 列结构，额外列顺序保持一致。
const EXTRA_HEADERS = [
  '一级行业',
  '二级行业',
  '标签',
  '达人粉段',
  ...RATIO_HEADERS,
] as const;

const EXTRA_COLUMNS = [
  INDUSTRY,
  SUB_INDUSTRY,
  TAG,
  FANS,
  ...Array.from(
    { length: RATIO_END - RATIO_START },
    (_, index) => RATIO_START + index,
  ),
];

const DIMENSION_FILTERS = [
  { key: 'industry', label: '行业', column: INDUSTRY },
  { key: 'fans', label: '粉丝量级', column: FANS },
  { key: 'tag', label: '内容标签', column: TAG },
] as const;

const PRICE_FILTERS = [
  { key: 'priceMid', label: '植入报价', column: PRICE_MID },
  { key: 'priceLong', label: '定制报价', column: PRICE_LONG },
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

const text = (value: string | number | null | undefined) =>
  value === null || value === undefined ? '' : String(value);

// 与代理商模块 display 同口径：源表 NULL 统一展示“未提供（NULL）”，空值兜底为 —。
const display = (value: string | number | null | undefined) =>
  value === null || value === undefined
    ? '未提供（NULL）'
    : text(value) === ''
      ? '—'
      : String(value);

// CSV 保留源表口径：缺省输出 NULL 字面量，0 输出 0，与代理商导出一致。
const rawCell = (value: string | number | null | undefined) =>
  value === null || value === undefined ? 'NULL' : value;

// 与代理商模块同口径：0 是有效报价（展示 ¥0、归入 1万以下），仅 null/空值视为缺省。
const priceAmount = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') return null;
  const amount = Number(value);
  return Number.isFinite(amount) ? amount : null;
};

const priceText = (value: string | number | null | undefined) => {
  const amount = priceAmount(value);
  return amount === null ? '—' : `¥${amount.toLocaleString('zh-CN')}`;
};

const inPriceBucket = (amount: number | null, bucket: string) => {
  if (!bucket) return true;
  if (amount === null) return false;
  const [min, max] = bucket.split('-');
  if (max === '') return amount >= Number(min);
  return amount >= Number(min) && amount < Number(max);
};

const ratioPercent = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') return null;
  const ratio = Number(value);
  return Number.isFinite(ratio) ? ratio * 100 : null;
};

const xingtuProfile = (id: string) =>
  `https://www.xingtu.cn/ad/creator/author/douyin/${id}`;

// profiles 只存 sec_uid，主页 URL 运行时拼接，控制数据产物体积。
const douyinProfile = (secUid: string) =>
  `https://www.douyin.com/user/${secUid}`;

// 当无法获取 sec_uid 时，允许使用 short_id 生成可点击跳转链接。
const douyinShortProfile = (shortId: string) =>
  `https://www.douyin.com/user/${shortId}`;

const TABLE_HEADERS = [
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
  ...EXTRA_HEADERS,
];

const CSV_HEADERS = [
  '达人昵称',
  '达人星图ID',
  '植入报价(元)',
  '定制报价(元)',
  '抖音主页',
  '星图主页',
  '行业',
  '粉丝量级',
  '内容标签',
  ...EXTRA_HEADERS,
];

export function P0AuthorsModule() {
  const [data, setData] = useState<P0Data | null>(null);
  const [profiles, setProfiles] = useState<Record<string, string>>({});
  const [shortIds, setShortIds] = useState<Record<string, string>>({});
  const [loadError, setLoadError] = useState(false);
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      import('@/data/p0Authors.json'),
      import('@/data/p0ProfileUrls.json'),
      import('@/data/p0ShortIds.json'),
    ])
      .then(([dataModule, profileModule, shortModule]) => {
        if (cancelled) return;
        setData(dataModule.default as unknown as P0Data);
        setProfiles(
          (profileModule.default as unknown as P0ProfileDoc).profiles,
        );
        setShortIds((shortModule.default as unknown as P0ShortDoc).shortIds);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const options = useMemo(() => {
    if (!data) return { industry: [], fans: [], tag: [] };
    const distinct = (column: number) =>
      [
        ...new Set(
          data.rows.map(row => text(row[column])).filter(value => value !== ''),
        ),
      ].sort();
    return {
      industry: distinct(INDUSTRY),
      fans: distinct(FANS),
      tag: distinct(TAG),
    };
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.rows.filter(row => {
      const dimensionMatched = DIMENSION_FILTERS.every(
        ({ key, column }) =>
          !filters[key] || text(row[column]) === filters[key],
      );
      if (!dimensionMatched) return false;
      return (
        inPriceBucket(priceAmount(row[PRICE_MID]), filters.priceMid) &&
        inPriceBucket(priceAmount(row[PRICE_LONG]), filters.priceLong)
      );
    });
  }, [data, filters]);

  const pagination = agencyPagination(filtered.length, page);

  const downloadCsv = () => {
    if (!data) return;
    const rows = filtered.map(row => [
      row[NAME],
      row[ID],
      rawCell(row[PRICE_MID]),
      rawCell(row[PRICE_LONG]),
      profiles[text(row[ID])]
        ? douyinProfile(profiles[text(row[ID])])
        : shortIds[text(row[ID])]
          ? douyinShortProfile(shortIds[text(row[ID])])
          : '',
      xingtuProfile(text(row[ID])),
      rawCell(row[INDUSTRY]),
      rawCell(row[FANS]),
      rawCell(row[TAG]),
      ...EXTRA_COLUMNS.map(column => rawCell(row[column])),
    ]);
    const today = new Date().toISOString().slice(0, 10);
    downloadRowsTable(
      `P0作者_${today}_${filtered.length}位.csv`,
      CSV_HEADERS,
      rows,
      '达人星图ID',
    );
  };

  if (loadError) {
    return (
      <section className="content-section p0-section">
        <p className="p-6">P0 作者数据加载失败，请刷新页面重试。</p>
      </section>
    );
  }

  return (
    <section className="content-section p0-section enter">
      <div className="section-heading">
        <div>
          <span className="eyebrow">P0 · QUALITY POTENTIAL</span>
          <h2>P0作者</h2>
          <p>
            Q4 优质潜力 P0 作者池，共
            {data ? ` ${data.meta.total.toLocaleString()} ` : ' '}
            位；支持行业、粉丝量级、内容标签、植入报价、定制报价五项组合筛选，向右滚动查看全维度。
          </p>
        </div>
      </div>

      {!data ? (
        <output className="p0-loading">
          <LoaderCircle size={18} className="spin" />
          <span>正在加载 P0 作者数据…</span>
        </output>
      ) : (
        <>
          <div className="flex flex-wrap gap-4 my-6 agency-filter-bar">
            {DIMENSION_FILTERS.map(({ key, label }) => (
              <label key={key} className="flex flex-col gap-2 text-sm">
                {label}
                <select
                  className="rounded-lg border border-slate-600 bg-slate-900 p-3 text-slate-100"
                  value={filters[key]}
                  onChange={event => {
                    setFilters({ ...filters, [key]: event.target.value });
                    setPage(1);
                  }}
                >
                  <option value="">全部{label}</option>
                  {options[key].map(value => (
                    <option key={value} value={value}>
                      {value}
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
                  onChange={event => {
                    setFilters({ ...filters, [key]: event.target.value });
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
          </div>

          <div
            className="overflow-x-auto agency-table-scroll"
            aria-label="P0 作者全维度表格，可横向滚动"
          >
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead>
                <tr>
                  {TABLE_HEADERS.map(header => (
                    <th
                      className="p-3 border-b border-slate-700"
                      scope="col"
                      key={header}
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.slice(pagination.offset, pagination.end).map(row => {
                  const id = text(row[ID]);
                  const name = text(row[NAME]);
                  const secUid = profiles[id] ?? null;
                  const shortId = shortIds[id] ?? null;
                  const douyinUrl = secUid
                    ? douyinProfile(secUid)
                    : shortId
                      ? douyinShortProfile(shortId)
                      : null;
                  return (
                    <tr key={id}>
                      <td className="p-3">
                        <P0Avatar id={id} name={name} />
                      </td>
                      <td className="p-3">{name}</td>
                      <td className="p-3">{id}</td>
                      <td className="p-3">{priceText(row[PRICE_MID])}</td>
                      <td className="p-3">{priceText(row[PRICE_LONG])}</td>
                      <td className="p-3">
                        {douyinUrl ? (
                          <a
                            className="agency-home-link"
                            href={douyinUrl}
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
                          href={xingtuProfile(id)}
                          target="_blank"
                          rel="noreferrer"
                        >
                          星图主页 ↗
                        </a>
                      </td>
                      <td className="p-3">{display(row[INDUSTRY])}</td>
                      <td className="p-3">{display(row[FANS])}</td>
                      <td className="p-3">{display(row[TAG])}</td>
                      {EXTRA_HEADERS.map((header, index) => {
                        const column = EXTRA_COLUMNS[index];
                        if (index < 4) {
                          return (
                            <td className="p-3" key={header}>
                              {display(row[column])}
                            </td>
                          );
                        }
                        const percent = ratioPercent(row[column]);
                        if (percent === null) {
                          return (
                            <td className="p-3" key={header}>
                              未提供（NULL）
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
                                style={{
                                  width: `${Math.min(percent, 100)}%`,
                                }}
                              />
                            </div>
                            <em>{percent.toFixed(2)}%</em>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
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
            ariaLabel="P0 作者分页"
          />
        </>
      )}
    </section>
  );
}
