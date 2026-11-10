import {
  ArrowUpRight,
  CalendarDays,
  Gift,
  Sparkles,
  UsersRound,
} from 'lucide-react';
import autumnEmotionsImage from '../assets/autumn-emotions.png';

type CampaignLink = {
  label: string;
  url: string;
  primary?: boolean;
};

type IpCampaign = {
  index: string;
  industry: string;
  title: string;
  period: string;
  quota: string;
  summary: string;
  benefits: string[];
  links: CampaignLink[];
  tone: string;
};

const CAMPAIGNS: IpCampaign[] = [
  {
    index: '01',
    industry: '日化行业',
    title: '入秋情绪图鉴',
    period: '2026.09.01 — 10.15',
    quota: '500万 / 200万 / 100万 / 30万',
    summary: '从发丝到指尖，用四大入秋情绪人群图鉴连接品牌与消费者的秋日情绪。',
    benefits: [
      '精选达人服务费抵扣',
      '搜索组件 2.0 / 1.0',
      '电商联投与流量激励',
    ],
    links: [
      {
        label: '查看活动方案',
        url: 'https://bytedance.larkoffice.com/wiki/UA8Bwp5yniC0eFkfUHdcBp5anAm?from=from_copylink',
        primary: true,
      },
    ],
    tone: 'amber',
  },
  {
    index: '02',
    industry: '游戏行业',
    title: 'Q3「精选达人」合作企划',
    period: '2026.08.27 — 09.30',
    quota: '报名行业：中国广告销售平台-直客业务-互动娱乐',
    summary:
      '以优质内容承接破圈、种草与转化，帮助游戏厂商把营销话术变成玩家愿意看的内容。',
    benefits: ['精选达人服务费抵扣', '六类特色营销官', '完整达人刊例'],
    links: [
      {
        label: '查看企划案',
        url: 'https://bytedance.larkoffice.com/docx/Tl6bdDg6eoBAbTxJTdNcCWmen2b?from=from_copylink',
        primary: true,
      },
      {
        label: '达人刊例',
        url: 'https://bytedance.larkoffice.com/sheets/G8A9s1saShCTJpt6ACFcJRYqnxe?sheet=b54148',
      },
    ],
    tone: 'violet',
  },
  {
    index: '03',
    industry: '家居行业',
    title: 'Star 超会装 · 家的秋季灵感',
    period: '2026.09.01 — 11.15',
    quota: '500万 / 200万 / 50万',
    summary:
      '聚焦家装改造、家纺焕新与日用百货三大秋季消费场景，串联种草到进店转化。',
    benefits: ['精选达人合作企划', '流量与服务费激励', '秋季场景达人清单'],
    links: [
      {
        label: '查看活动方案',
        url: 'https://bytedance.larkoffice.com/docx/H1nzdr08PonANixmF22cw8KRnZe?from=from_copylink',
        primary: true,
      },
      {
        label: '合作文档',
        url: 'https://bytedance.larkoffice.com/wiki/PtCVwjle8iLrREkLS4uc6Errncf',
      },
      {
        label: '推荐达人',
        url: 'https://bytedance.larkoffice.com/sheets/KvKtsmZIJhsn6rtHXvJcy6eln1E?from=from_copylink&sheet=83d343',
      },
    ],
    tone: 'copper',
  },
  {
    index: '04',
    industry: '婴宠行业',
    title: 'Q4 内容洞察与星图激励',
    period: '2026.10.01 — 12.31',
    quota: '500万 / 200万 / 50万',
    summary:
      '围绕换季、大促、出行与年终陪伴场景，以内容策略和星图激励提升种草确定性。',
    benefits: [
      '限定客户：中国广告销售平台-直客业务-时尚婴宠-C组/D组/E组',
      '四大精选内容场景',
      'OA 锁席报名',
    ],
    links: [
      {
        label: '查看活动方案',
        url: 'https://bytedance.larkoffice.com/wiki/GDwlwsXZyicAwikEmjocrEvwnfh?from=from_copylink',
        primary: true,
      },
      {
        label: '场景达人推荐',
        url: 'https://bytedance.larkoffice.com/wiki/LmzuwIPHsijgNbkbdhlcAZrmnDd',
      },
    ],
    tone: 'mint',
  },
  {
    index: '05',
    industry: '美妆行业',
    title: '秋日好状态加载中',
    period: '2026.09.11 — 10.25',
    quota: '500万 / 200万 / 100万 / 50万',
    summary:
      '围绕换季敏感、秋冬保湿、中式妆容与出游持妆，构建秋日好状态种草图鉴。',
    benefits: ['服务费抵扣与流量激励', '搜索组件多词权益', '电商联投达人配赠'],
    links: [
      {
        label: '查看活动方案',
        url: 'https://bytedance.larkoffice.com/wiki/TBXuwynSuioNnGkcZXVceoFnnrd?from=from_copylink',
        primary: true,
      },
    ],
    tone: 'rose',
  },
];

export function IpCampaignModule() {
  return (
    <section className="content-section enter ip-module">
      <div className="section-heading ip-heading">
        <div>
          <span className="eyebrow">CURATED · IP CAMPAIGNS</span>
          <h2>IP 精选合作企划</h2>
          <p>汇总重点行业内容 IP、直充活动与精选达人合作入口。</p>
        </div>
        <div className="ip-summary">
          <Sparkles size={18} />
          <span>5 个行业企划</span>
          <b>2026 秋冬档</b>
        </div>
      </div>
      <div className="ip-grid">
        {CAMPAIGNS.map(campaign => (
          <article className={`ip-card ${campaign.tone}`} key={campaign.index}>
            <div className="ip-card-head">
              <span className="ip-index">{campaign.index}</span>
              <span className="ip-industry">{campaign.industry}</span>
            </div>
            <h3>{campaign.title}</h3>
            {campaign.index === '01' && (
              <a
                href={autumnEmotionsImage}
                target="_blank"
                rel="noreferrer"
                aria-label="查看入秋情绪图鉴完整展示图"
              >
                <img
                  src={autumnEmotionsImage}
                  alt="日化行业入秋情绪图鉴活动展示图"
                  style={{
                    width: '100%',
                    height: 'auto',
                    display: 'block',
                    borderRadius: 12,
                    marginBottom: 16,
                  }}
                />
              </a>
            )}
            <p className="ip-summary-copy">{campaign.summary}</p>
            <div className="ip-facts">
              <div>
                <CalendarDays size={16} />
                <span>
                  <small>活动周期</small>
                  <b>{campaign.period}</b>
                </span>
              </div>
              <div>
                <UsersRound size={16} />
                <span>
                  <small>席位 / 范围</small>
                  <b>{campaign.quota}</b>
                </span>
              </div>
            </div>
            <div className="ip-benefits">
              <span>
                <Gift size={15} /> 核心权益
              </span>
              <ul>
                {campaign.benefits.map(benefit => (
                  <li key={benefit}>{benefit}</li>
                ))}
              </ul>
            </div>
            <div className="ip-links">
              {campaign.links.map(link => (
                <a
                  className={link.primary ? 'primary' : ''}
                  href={link.url}
                  key={link.label}
                  target="_blank"
                  rel="noreferrer"
                >
                  {link.label} <ArrowUpRight size={13} />
                </a>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
