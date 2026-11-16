import { ArrowUpRight, BookOpen, Sparkles } from 'lucide-react';

const BOOKLETS = [
  {
    title: '把年末的心意，过成一场值得分享的节日｜双旦巨量星图精选达人特刊',
    url: 'https://bytedance.larkoffice.com/wiki/UaPHwSE3WiHG1RkfQ92cs2sLnFg',
  },
  {
    title: '把想要的生活，提前加入购物车｜双11巨量星图精选达人特刊',
    url: 'https://bytedance.larkoffice.com/wiki/RCPkwd0ZAipbFGkW9j5cC2Yon0c',
  },
  {
    title: '超长假期，超级团圆｜中秋+国庆巨量星图精选达人特刊',
    url: 'https://bytedance.larkoffice.com/wiki/CkBdw9OyeiDzR9kZm9vcEvgfnvf',
  },
] as const;

export function AgencyBookletRail() {
  return (
    <section
      id="agency-booklets"
      className="sidebar-rail sidebar-booklets"
      aria-label="精选达人推荐刊例"
    >
      <div className="sidebar-rail-head">
        <Sparkles size={16} />
        <div>
          <strong>精选达人推荐刊例</strong>
          <span>代理模块下方快捷入口</span>
        </div>
      </div>
      <div className="sidebar-booklet-list">
        {BOOKLETS.map((booklet, index) => (
          <a
            href={booklet.url}
            target="_blank"
            rel="noreferrer"
            key={booklet.url}
          >
            <span className="sidebar-booklet-index">0{index + 1}</span>
            <span className="sidebar-booklet-copy">
              <b>{booklet.title}</b>
              <small>
                <BookOpen size={12} /> 飞书 Wiki
              </small>
            </span>
            <ArrowUpRight size={14} />
          </a>
        ))}
      </div>
    </section>
  );
}

export function FeaturedTalentSidebarEntry() {
  return (
    <a
      className="sidebar-rail sidebar-feature-entry"
      href="#featured-talent-intro"
    >
      <span className="sidebar-feature-entry-label">精选达人介绍</span>
      <small>首页导览与查询入口</small>
    </a>
  );
}
