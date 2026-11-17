import { douyinAvatarMap, douyinAvatarMeta } from '@/data/douyinAvatarMap';
import { industrySamples } from '@/data/industrySamples';
import { nodeSamples } from '@/data/nodeSamples';
import { shuffleNodeRows } from '@/lib/shuffleNodeRows';
import { useFeishuSheetRange } from '@aeolus/feishu-table-sdk';
import {
  ArrowUpRight,
  Bot,
  CalendarDays,
  ChevronRight,
  ExternalLink,
  Globe2,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  UsersRound,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  BookletSidebarEntry,
  FeaturedTalentSidebarEntry,
} from './AgencyBookletRail';
import { AgencyModule } from './AgencyModule';
import { BookletModule } from './BookletModule';
import { DataApplicationProvider } from './DataApplicationProvider';
import { FeaturedTalentIntro } from './FeaturedTalentIntro';
import { IpCampaignModule } from './IpCampaignModule';
import { TeamModule } from './TeamModule';

import { ModuleBanner, type ModuleKey } from './ModuleBanner';

type SourceOption = {
  id: string;
  label: string;
  sheetId: string;
  count: number;
};

const INDUSTRIES: SourceOption[] = [
  { id: 'industry-beauty', label: '美妆', sheetId: '0OYgsp', count: 7389 },
  { id: 'industry-food', label: '食品饮料', sheetId: '1RZNHB', count: 1969 },
  { id: 'industry-fashion', label: '服装配饰', sheetId: '2JBIVb', count: 2761 },
  { id: 'industry-mom', label: '母婴宠物', sheetId: '3UBBZb', count: 1733 },
  { id: 'industry-care', label: '日化', sheetId: '4QiWFQ', count: 5728 },
  { id: 'industry-health', label: '医药健康', sheetId: '5rncze', count: 1801 },
  {
    id: 'industry-digital',
    label: '3C 及电器',
    sheetId: '6aYmtl',
    count: 5204,
  },
  { id: 'industry-auto', label: '汽车', sheetId: '7myfJs', count: 3221 },
  { id: 'industry-game', label: '游戏', sheetId: '8kFWgq', count: 29215 },
  {
    id: 'industry-commerce',
    label: '互联网电商服务',
    sheetId: '9FoKhW',
    count: 9986,
  },
  { id: 'industry-finance', label: '金融业', sheetId: '10chQs', count: 2131 },
];

const NODES: SourceOption[] = [
  { id: 'node-1111', label: '双 11', sheetId: '0iHZMy', count: 16500 },
  { id: 'node-1212', label: '双 12', sheetId: '1tVppi', count: 16500 },
  { id: 'node-newyear', label: '跨年 / 元旦', sheetId: '2pzQvF', count: 16500 },
  {
    id: 'node-christmas',
    label: '平安夜 / 圣诞',
    sheetId: '3PUkix',
    count: 16500,
  },
];

const MODULES = [
  {
    key: 'industry' as const,
    label: '行业',
    desc: '11 个重点行业',
    icon: Globe2,
  },
  {
    key: 'node' as const,
    label: '节点',
    desc: 'Q4 营销节点',
    icon: CalendarDays,
  },
  { key: 'ip' as const, label: 'IP', desc: '特色内容资产', icon: Star },
  {
    key: 'team' as const,
    label: '达人团',
    desc: '组合式供给',
    icon: UsersRound,
  },
  {
    key: 'ai' as const,
    label: '代理商使用模块',
    desc: '重点达人 · 报价与全维度',
    icon: Bot,
  },
];

const INDUSTRY_URL =
  'https://bytedance.larkoffice.com/sheets/ShwKsQe36hxTiTtEF0Dc4W4cnPe';
const NODE_URL =
  'https://bytedance.larkoffice.com/sheets/BfFYsEunBhI0PKtGKzfc6smbnic';

function text(value: unknown) {
  if (value === null || value === undefined || value === '') return '-';
  return String(value);
}

function compactPrice(value: unknown) {
  const raw = text(value).replace(/,/g, '');
  const amount = Number(raw);
  if (!Number.isFinite(amount) || amount <= 0) return '待询价';
  return amount >= 10000
    ? `¥${(amount / 10000).toFixed(amount % 10000 ? 1 : 0)}万`
    : `¥${amount}`;
}

function initials(name: string) {
  return Array.from(name).slice(0, 2).join('');
}

function FeishuErrorPanel({
  error,
  sourceUrl,
}: { error: unknown; sourceUrl: string }) {
  const message =
    error instanceof Error
      ? error.message
      : String(
          (error as { message?: unknown })?.message ?? error ?? '加载失败',
        );
  const unauthorized = /has not authorized Feishu/i.test(message);
  const forbidden = /91403|Forbidden/i.test(message);
  return (
    <div className="state-panel error-panel">
      <ShieldCheck size={22} />
      <div>
        <strong>
          {unauthorized
            ? '需要先授权飞书'
            : forbidden
              ? '暂无数据源权限'
              : '数据加载失败'}
        </strong>
        <p>
          {unauthorized
            ? '请先在 Aime 完成飞书授权，再刷新本页。'
            : forbidden
              ? '请向表格所有者申请访问权限，获批后刷新。'
              : '数据源暂时不可用，请稍后重试。'}
        </p>
      </div>
      <a
        href={unauthorized ? 'https://aime.bytedance.net' : sourceUrl}
        target="_blank"
        rel="noreferrer"
      >
        去处理 <ArrowUpRight size={14} />
      </a>
    </div>
  );
}

function TalentCard({
  row,
  headers,
  mode,
}: { row: unknown[]; headers: string[]; mode: 'industry' | 'node' }) {
  const get = (name: string) => row[headers.indexOf(name)];
  const name = text(get('星图达人抖音昵称'));
  const city = text(get('常驻城市'));
  const talentType = text(get('达人类型'));
  const priority = text(get('推荐优先级'));
  const fans = text(get('达人抖音粉丝量级'));
  const category = text(get(mode === 'node' ? '细分行业' : '推荐行业'));
  const score = mode === 'node' ? text(get('节点推荐分')) : '';
  const middlePrice = compactPrice(get('抖音21-60s长视频报价(元)'));
  const longPrice = compactPrice(get('抖音60s以上视频报价(元)'));
  // 字符串 ID 保留全部精度，仅清理空白及表格常见的 .0 后缀。
  const id = text(get('达人星图id')).trim().replace(/\.0+$/, '');
  const profile =
    id !== '-' ? `https://www.xingtu.cn/ad/creator/author/douyin/${id}` : '#';
  const douyin = douyinAvatarMap[id];
  const spriteSize = douyinAvatarMeta.spriteSize ?? [4000, 3200];
  const douyinUrl = douyin?.profileUrl || profile;
  const subtitle =
    mode === 'node'
      ? [text(get('节点')), category].filter(value => value !== '-').join(' · ')
      : [city, talentType].filter(value => value !== '-').join(' · ');

  return (
    <article className="talent-card industry-card">
      <div className="talent-topline">
        <a
          className="avatar avatar-photo"
          href={douyinUrl}
          target="_blank"
          rel="noreferrer"
          aria-label={`打开 ${name} 的抖音主页`}
        >
          {douyin?.avatarPosition ? (
            <span
              className="avatar-sprite"
              style={{
                backgroundImage: `url(${douyin.avatarUrl})`,
                backgroundPosition: douyin.avatarPosition,
                backgroundSize: `${spriteSize[0]}px ${spriteSize[1]}px`,
              }}
              role="img"
              aria-label={`${name} 头像`}
            />
          ) : douyin?.avatarUrl ? (
            <img src={douyin.avatarUrl} alt={`${name} 头像`} />
          ) : (
            <span>{initials(name)}</span>
          )}
        </a>
        <div className="talent-title">
          <strong>{name}</strong>
          <span>{subtitle || '精选达人'}</span>
          {douyin?.displayId ? <em>抖音号：{douyin.displayId}</em> : null}
        </div>
        {score !== '' && score !== '-' ? (
          <span className="score">{score}</span>
        ) : (
          <span className="priority">{priority.replace('S-', '')}</span>
        )}
      </div>
      <div className="tag-row">
        <span>{category}</span>
        <span>{fans}</span>
        <span>{priority}</span>
      </div>
      <div className="price-board">
        <div>
          <b>{middlePrice}</b>
          <small>21–60s</small>
        </div>
        <div>
          <b>{longPrice}</b>
          <small>60s+</small>
        </div>
      </div>
      <div className="card-actions">
        <a href={douyinUrl} target="_blank" rel="noreferrer">
          抖音主页 <ExternalLink size={13} />
        </a>
        <a href={profile} target="_blank" rel="noreferrer">
          星图主页 <ExternalLink size={13} />
        </a>
      </div>
    </article>
  );
}

function LiveTalentModule({
  mode,
  options,
  selected,
  onSelect,
  onNavigate,
  previousNodeFirst,
}: {
  previousNodeFirst?: { current: string | null };
  onNavigate: (module: ModuleKey) => void;
  mode: 'industry' | 'node';
  options: SourceOption[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const previewSample =
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('preview') === 'sample';
  const [query, setQuery] = useState(() =>
    previewSample
      ? new URLSearchParams(window.location.search).get('q') || ''
      : '',
  );
  const current = options.find(item => item.id === selected) ?? options[0];
  const isNode = mode === 'node';
  const sourceUrl = `${isNode ? NODE_URL : INDUSTRY_URL}?sheet=${current.sheetId}`;
  const sheet = useFeishuSheetRange({
    bindingId: current.id,
    range: isNode ? 'A1:AN101' : 'A1:AC101',
  });
  const sample = isNode ? nodeSamples[current.id] : industrySamples[current.id];
  const shouldUseSample =
    sample && (previewSample || (!sheet.data && sheet.status === 'error'));
  const values = shouldUseSample
    ? [sample.headers, ...sample.rows]
    : sheet.data?.rawValues;
  const hasRenderableData = Boolean(values?.length);
  const headers = useMemo(() => (values?.[0] ?? []).map(text), [values]);
  const [shuffleSeed] = useState(() => Math.floor(Math.random() * 4294967296));
  const [previousFirst] = useState(() => previousNodeFirst?.current ?? null);
  const rows = useMemo(() => {
    const sourceRows = (values?.slice(1) ?? []) as unknown[][];
    if (!isNode) return sourceRows;
    const idIndex = headers.indexOf('达人星图id');
    return shuffleNodeRows(
      sourceRows,
      shuffleSeed,
      row => text(row[idIndex]),
      previousFirst,
    );
  }, [values, isNode, headers, shuffleSeed, previousFirst]);
  useEffect(() => {
    if (isNode && rows.length && previousNodeFirst) {
      previousNodeFirst.current = text(rows[0][headers.indexOf('达人星图id')]);
    }
  }, [isNode, rows, headers, previousNodeFirst]);
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter(row =>
      row.some(value => text(value).toLowerCase().includes(needle)),
    );
  }, [query, rows]);

  return (
    <section className={`content-section enter ${isNode ? 'node-module' : ''}`}>
      <div
        className="section-heading"
        id={isNode ? undefined : 'module-content'}
      >
        <div>
          <span className="eyebrow">MODULE · {isNode ? '02' : '01'}</span>
          <h2>{isNode ? '节点精选达人' : '行业精选达人'}</h2>
          <p>
            {isNode
              ? '按营销节点与行业推荐分，快速定位节点型达人供给。'
              : '覆盖 11 个重点行业，汇总核心推荐达人与商业合作信息。'}
          </p>
        </div>
        <a
          className="source-link"
          href={sourceUrl}
          target="_blank"
          rel="noreferrer"
        >
          原始数据源 <ExternalLink size={14} />
        </a>
      </div>
      <div className="filter-bar">
        <div className="pill-scroll">
          {options.map(item => (
            <button
              key={item.id}
              className={item.id === current.id ? 'pill active' : 'pill'}
              onClick={() => onSelect(item.id)}
            >
              {item.label}
              <span>{item.count.toLocaleString()}</span>
            </button>
          ))}
        </div>
        <div className="search-box">
          <Search size={16} />
          <input
            aria-label="搜索达人"
            value={query}
            onChange={event => setQuery(event.target.value)}
            placeholder="搜索达人 / 城市 / 类型…"
          />
        </div>
      </div>
      <div className="data-summary">
        <div>
          <span>当前分组</span>
          <strong>{current.label}</strong>
        </div>
        <div>
          <span>供给规模</span>
          <strong>{current.count.toLocaleString()}</strong>
        </div>
        <div>
          <span>本页载入</span>
          <strong>{rows.length}</strong>
        </div>
        <button
          onClick={() => sheet.reload()}
          disabled={sheet.status === 'loading'}
        >
          <RefreshCw
            size={15}
            className={sheet.status === 'loading' ? 'spin' : ''}
          />
          刷新数据
        </button>
      </div>
      {isNode && <ModuleBanner module="node" onNavigate={onNavigate} />}
      <div id={isNode ? 'module-content' : undefined}>
        {(sheet.status === 'idle' ||
          (sheet.status === 'loading' && !sheet.data)) && (
          <div className="card-grid">
            {['a', 'b', 'c', 'd', 'e', 'f'].map(id => (
              <div className="talent-card skeleton" key={id} />
            ))}
          </div>
        )}
        {sheet.status === 'error' && !hasRenderableData && (
          <FeishuErrorPanel error={sheet.error} sourceUrl={sourceUrl} />
        )}
        {shouldUseSample && (
          <div className="state-panel preview-panel">
            <ShieldCheck size={18} />
            <div>
              <strong>本地样本预览</strong>
              <p>
                飞书实时数据暂不可用，当前展示前 100 位
                {isNode ? '节点' : '行业'}
                样本，线上授权后会自动切回实时数据。
              </p>
            </div>
          </div>
        )}
        {hasRenderableData && (
          <>
            <div className="result-line">
              <span>优先展示前 100 位供给，当前匹配 {filtered.length} 位</span>
              <span className="live-dot">
                {shouldUseSample ? 'PREVIEW · 样本数据' : 'LIVE · 飞书同步'}
              </span>
            </div>
            <div className="card-grid">
              {filtered.slice(0, 100).map(row => (
                <TalentCard
                  key={`${current.id}-${text(row[headers.indexOf('达人星图id')])}`}
                  row={row}
                  headers={headers}
                  mode={mode}
                />
              ))}
            </div>
            {filtered.length === 0 && (
              <div className="state-panel">
                没有找到匹配的达人，换个关键词试试。
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}

function PendingModule({ module }: { module: ModuleKey }) {
  const info = {
    ip: {
      title: 'IP 精选供给',
      text: '聚合特色内容 IP、栏目资产与可商业化合作方向。',
      icon: Star,
    },
    team: {
      title: '达人团供给',
      text: '按场景组合达人矩阵，支持品牌批量筛选与协同投放。',
      icon: UsersRound,
    },
    ai: {
      title: '代理商使用模块',
      text: '代理商重点与千川代理商供给入口。',
      icon: Bot,
    },
  }[module as 'ip' | 'team' | 'ai'];
  const Icon = info.icon;
  return (
    <section
      id="module-content"
      className="content-section enter pending-module"
    >
      <div className="pending-orb">
        <Icon size={40} />
      </div>
      <span className="eyebrow">MATERIALS · PENDING</span>
      <h2>{info.title}</h2>
      <p>{info.text}</p>
      <div className="pending-card">
        <Sparkles size={22} />
        <div>
          <strong>模块已预留，等待供给材料</strong>
          <span>
            补充对应飞书表格链接后，可直接接入同款实时筛选与达人卡片。
          </span>
        </div>
      </div>
    </section>
  );
}

function App() {
  const [module, setModule] = useState<ModuleKey>(() => {
    if (typeof window === 'undefined') return 'industry';
    const requested = new URLSearchParams(window.location.search).get('module');
    return requested === 'featured' ||
      requested === 'booklet' ||
      MODULES.some(item => item.key === requested)
      ? (requested as ModuleKey)
      : 'industry';
  });
  const [industry, setIndustry] = useState(INDUSTRIES[0].id);
  const previousNodeFirst = useRef<string | null>(null);
  const [node, setNode] = useState(NODES[3].id);
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={20} />
          </div>
          <div>
            <strong>精选达人</strong>
            <span>Talent Supply Hub</span>
          </div>
        </div>
        <FeaturedTalentSidebarEntry
          onOpen={() => setModule('featured')}
          active={module === 'featured'}
        />
        <BookletSidebarEntry
          onOpen={() => setModule('booklet')}
          active={module === 'booklet'}
        />
        <nav>
          {MODULES.map(item => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={module === item.key ? 'nav-item active' : 'nav-item'}
                onClick={() => setModule(item.key)}
              >
                <Icon size={18} />
                <span>
                  <b>{item.label}</b>
                  <small>{item.desc}</small>
                </span>
                <ChevronRight size={15} />
              </button>
            );
          })}
        </nav>
        <div className="sidebar-foot">
          <span>数据源</span>
          <strong>
            {module === 'ai'
              ? '风神底池 · 飞书全维度快照'
              : module === 'featured'
                ? '巨量星图 · 精选达人'
                : module === 'booklet'
                  ? '巨量星图 · 推荐刊例'
                  : '飞书表格 · 实时同步'}
          </strong>
          <small>
            {module === 'ai'
              ? '底池：11-10；新增报价与维度源表：11-16'
              : module === 'featured'
                ? '名单动态更新，以星图平台为准'
                : module === 'booklet'
                  ? '三期精选达人特刊，飞书 Wiki 维护'
                  : '最后刷新以页面载入时间为准'}
          </small>
        </div>
      </aside>
      <main>
        <div className="module-topbar">
          <span>
            精选达人供给 /{' '}
            {module === 'featured'
              ? '精选达人介绍'
              : module === 'booklet'
                ? '精选达人推荐刊例'
                : MODULES.find(item => item.key === module)?.label}
          </span>
          <span>Talent Supply Hub</span>
        </div>
        {module === 'featured' && <FeaturedTalentIntro />}
        {module === 'booklet' && <BookletModule />}
        {module !== 'node' && module !== 'featured' && module !== 'booklet' && (
          <ModuleBanner module={module} onNavigate={setModule} />
        )}
        {module === 'industry' && (
          <LiveTalentModule
            onNavigate={setModule}
            key={industry}
            mode="industry"
            options={INDUSTRIES}
            selected={industry}
            onSelect={setIndustry}
          />
        )}
        {module === 'node' && (
          <LiveTalentModule
            onNavigate={setModule}
            key={node}
            mode="node"
            previousNodeFirst={previousNodeFirst}
            options={NODES}
            selected={node}
            onSelect={setNode}
          />
        )}
        {module === 'ip' && (
          <div id="module-content">
            <IpCampaignModule />
          </div>
        )}
        {module === 'team' && <TeamModule />}
        {module === 'ai' && <AgencyModule />}
        <footer>
          <span>精选达人供给库 v1.0 · Powered by 飞书数据</span>
          <span>© 2026 Talent Supply</span>
        </footer>
      </main>
    </div>
  );
}

export function TalentSupplyApp() {
  return (
    <DataApplicationProvider>
      <App />
    </DataApplicationProvider>
  );
}
