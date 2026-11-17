import { ArrowUpRight, ExternalLink, Sparkles } from 'lucide-react';
import featuredTalentAiBadgeImage from '../assets/featured-talent-ai-badge.png';
import featuredTalentAiFilterImage from '../assets/featured-talent-ai-filter.png';
import featuredTalentOverviewImage from '../assets/featured-talent-overview.png';
import featuredTalentSquareImage from '../assets/featured-talent-square.png';

const RULES_URL =
  'https://bytedance.larkoffice.com/wiki/OMgYwDukCi9t3Qkdve0c04qhnFc';
const RATECARD_URL =
  'https://bytedance.larkoffice.com/sheets/RLIKsumwwh3Dz4tVmiicVyxgnqf';
const QUERY_URL = 'https://www.xingtu.cn/';

const INTRO_LINES = [
  '品牌达人营销不只是在“买流量”，更是在买“优质营销内容”。巨量星图为持续助力品牌营销，满足客户对优质营销内容的诉求，聚焦持续发掘「精选达人」。「精选达人」是能持续创作出抖音优质营销内容的达人。优质营销是指创作者通过真实的体验，充分的信息表达，出众的创作力，为用户带来更多有共鸣、有收获、有惊喜的营销内容。',
  '👍🏻「达人供给丰富」：平台供给近 4 万不同类型精选达人，包含多垂类、多人设、多内容类型，帮助品牌找到符合要求的达人；',
  '👍🏻「达人内容优质」：以专业、有深度的叙事展示品牌卖点，分享真实经历的使用体验，同时结合作者独特的营销创意让用户感受到品牌传递的价值，为用户和品牌负责；',
  '👍🏻「达人数据更优」：CPM、A3、看后搜、泛进店成本均优于大盘；',
  '👍🏻「项目激励可观」：重磅推出精选达人合作流量激励、赠款返还等支持，助力品牌合作效果提升。',
] as const;

type QueryCard = {
  title: string;
  image: string;
  alt: string;
  description: string;
  href?: string;
  cta?: string;
};

const QUERY_CARDS: QueryCard[] = [
  {
    title: '达人广场',
    image: featuredTalentSquareImage,
    alt: '巨量星图达人广场筛选页，左侧平台筛选中高亮展示“精选达人”标签。',
    description:
      '官方达人广场筛选位示意，登录后可在找达人页按「精选达人」标签快速查询。',
    href: QUERY_URL,
    cta: '点击进入查询',
  },
  {
    title: '小星ai · 精选达人标识',
    image: featuredTalentAiBadgeImage,
    alt: '小星 ai 推荐报告页中，多位达人卡片上标记了“精选达人”标签。',
    description: '小星 ai 推荐名单中已展示精选达人标识，便于快速识别优质供给。',
  },
  {
    title: '小星ai · 精选达人筛选',
    image: featuredTalentAiFilterImage,
    alt: '小星 ai 达人推荐列表中，优选达人筛选下拉框勾选“精选达人”。',
    description: '小星 ai 也已支持通过优选达人筛选项勾选「精选达人」进行缩圈。',
  },
];

export function FeaturedTalentIntro() {
  return (
    <section
      id="featured-talent-intro"
      className="featured-intro-section content-section enter"
    >
      <a
        className="featured-intro-rules-banner"
        href={RULES_URL}
        target="_blank"
        rel="noreferrer"
      >
        <span>点击进入-巨量星图｜2026Q4精选达人合作激励规则</span>
        <ArrowUpRight size={16} />
      </a>
      <div className="featured-intro-hero">
        <div className="featured-intro-copy">
          <span className="eyebrow featured-intro-eyebrow">
            HOME · FEATURED TALENT
          </span>
          <div className="featured-intro-title">
            <Sparkles size={18} />
            <span>精选达人介绍</span>
          </div>
          <div className="featured-intro-text">
            {INTRO_LINES.map(line => (
              <p key={line}>{line}</p>
            ))}
          </div>
          <p className="featured-intro-linkline">
            全量达人刊例可参考：
            <a href={RATECARD_URL} target="_blank" rel="noreferrer">
              Q4 精选达人刊例 <ExternalLink size={13} />
            </a>
          </p>
        </div>
        <figure className="featured-intro-visual">
          <img
            src={featuredTalentOverviewImage}
            alt="巨量星图精选达人介绍信息图，包含近4w达人供给、优质内容创作与效果优势。"
          />
        </figure>
      </div>
      <p className="featured-intro-note">
        *基于达人近日内容质量、活跃度等表现综合评估，名单动态更新，查询当日最新名单可登陆巨量星图平台官网，选择【精选达人】标签。巨量星图达人广场、小星ai均上线抖音「精选达人」标签，可快速一键筛选～
      </p>
      <div className="featured-query-grid">
        {QUERY_CARDS.map(card => (
          <article className="featured-query-card" key={card.title}>
            <div className="featured-query-card-media">
              <img src={card.image} alt={card.alt} />
            </div>
            <div className="featured-query-card-body">
              <strong>{card.title}</strong>
              <p>{card.description}</p>
            </div>
            {card.href ? (
              <a
                className="featured-query-link"
                href={card.href}
                target="_blank"
                rel="noreferrer"
              >
                {card.cta} <ArrowUpRight size={13} />
              </a>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
