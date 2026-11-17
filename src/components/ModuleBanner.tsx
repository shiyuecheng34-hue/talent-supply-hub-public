import {
  ArrowDown,
  Bot,
  CalendarDays,
  Globe2,
  Star,
  UsersRound,
} from 'lucide-react';
import { IndustryShareDonut } from './IndustryShareDonut';

export type ModuleKey =
  | 'industry'
  | 'node'
  | 'ip'
  | 'team'
  | 'ai'
  | 'featured'
  | 'booklet';

export type BannerModuleKey = Exclude<ModuleKey, 'featured' | 'booklet'>;

const introductions = {
  industry: {
    kicker: 'INDUSTRY · 精准发现',
    title: '行业精选达人供给',
    description:
      '覆盖 11 个重点行业，从细分领域、达人类型到商业报价，发现适合品牌的合作人选。',
    action: '浏览行业达人',
    secondary: '查看营销节点',
    target: 'node',
    icon: Globe2,
    detail: '11 个重点行业',
  },
  node: {
    kicker: 'MOMENTS · 节点营销',
    title: '把握节点，找到对的人',
    description:
      '围绕双 11、双 12、跨年与圣诞四大营销节点，以行业推荐分定位更契合营销时机的达人。',
    action: '浏览节点达人',
    secondary: '探索行业供给',
    target: 'industry',
    icon: CalendarDays,
    detail: '4 大营销节点',
  },
  ip: {
    kicker: 'CONTENT IP · 合作灵感',
    title: '特色 IP，让内容连接品牌',
    description:
      '聚合 6 个秋冬重点合作企划，探索特色内容资产、达人权益与品牌共创机会。',
    action: '查看 IP 合作企划',
    secondary: '发现行业达人',
    target: 'industry',
    icon: Star,
    detail: '6 个合作企划',
  },
  team: {
    kicker: 'CREATOR TEAMS · 协同供给',
    title: '达人组团，放大品牌声量',
    description:
      '按营销场景组合达人矩阵，当前共 13 个达人团，潜力宝藏达人团标注 NEW，其余保持「敬请期待」；已补充可查看的真实资料将提供文档入口。',
    action: '查看 13 个达人团',
    secondary: '先浏览行业达人',
    target: 'industry',
    icon: UsersRound,
    detail: '13 个达人团',
  },
  ai: {
    kicker: 'AGENCY · 代理商供给',
    title: '代理商使用模块',
    description:
      '在原底池限定达人范围内筛选，按星图 ID 关联真实报价、细分行业与八类粉丝人群比例，并提供精选达人推荐刊例。',
    action: '查看代理商重点',
    secondary: '浏览现有供给',
    target: 'industry',
    icon: Bot,
    detail: '重点达人 · 真实报价',
  },
} as const;

export function ModuleBanner({
  module,
  onNavigate,
}: {
  module: BannerModuleKey;
  onNavigate: (module: ModuleKey) => void;
}) {
  const info = introductions[module];
  const Icon = info.icon;
  return (
    <section
      className={`hero module-banner banner-${module} enter`}
      aria-label={`${module} 模块介绍`}
    >
      <div className="hero-grid" />
      <div className="hero-copy">
        <span className="hero-kicker">{info.kicker}</span>
        <h1>{info.title}</h1>
        <p>{info.description}</p>
        <div className="hero-actions">
          <button
            onClick={() =>
              document
                .getElementById('module-content')
                ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
            }
          >
            <ArrowDown size={17} />
            {info.action}
          </button>
          {module !== 'ip' && module !== 'ai' && (
            <button className="ghost" onClick={() => onNavigate(info.target)}>
              {info.secondary}
            </button>
          )}
        </div>
      </div>
      {module === 'industry' ? (
        <div className="module-decoration industry-share-decoration">
          <IndustryShareDonut />
          <span>11 个行业供给占比</span>
        </div>
      ) : (
        <div className="module-decoration" aria-hidden="true">
          <Icon size={76} strokeWidth={1.2} />
          <span>{info.detail}</span>
        </div>
      )}
    </section>
  );
}
