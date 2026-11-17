import booklet1111 from '../assets/booklet-1111.jpg';
import bookletMidautumn from '../assets/booklet-midautumn.jpg';
import bookletShuangdan from '../assets/booklet-shuangdan.jpg';

export type Booklet = {
  id: string;
  issue: string;
  title: string;
  summary: string;
  cover: string;
  aspect: number;
  docUrl: string;
  wechatUrl: string | null;
  publishedAt: string;
  wechatStatus: 'published' | 'pending';
};

export const BOOKLETS: Booklet[] = [
  {
    id: 'shuangdan',
    issue: '双旦季特别刊',
    title: '把年末的心意，过成一场值得分享的节日｜双旦巨量星图精选达人特刊',
    summary:
      '双旦内容的关键不是「堆产品」，而是「落场景」：双旦妆造、宅家过节、情侣送礼、城市出门、AI 剧情与年末治愈，精选达人把场景拍成故事，让品牌自然入镜。',
    cover: bookletShuangdan,
    aspect: 4512 / 1344,
    docUrl: 'https://bytedance.larkoffice.com/wiki/UaPHwSE3WiHG1RkfQ92cs2sLnFg',
    wechatUrl: null,
    publishedAt: '2026.11 刊期',
    wechatStatus: 'pending',
  },
  {
    id: '1111',
    issue: '双 11 特别刊',
    title: '把想要的生活，提前加入购物车｜双11巨量星图精选达人特刊',
    summary:
      '双 11 像一场关于「想要」的集中提问。精选达人将产品放进测评、剧情、厨房与旅途，让品牌表达不只回答「现在可以买」，也回答「为什么适合此刻的我」。',
    cover: booklet1111,
    aspect: 5488 / 1648,
    docUrl: 'https://bytedance.larkoffice.com/wiki/RCPkwd0ZAipbFGkW9j5cC2Yon0c',
    wechatUrl: 'https://mp.weixin.qq.com/s/r8a6dpYL_wbKhY7cPafgqg',
    publishedAt: '2026.10.26 发布',
    wechatStatus: 'published',
  },
  {
    id: 'midautumn',
    issue: '中秋国庆特别刊',
    title: '超长假期，超级团圆｜中秋+国庆巨量星图精选达人特刊',
    summary:
      '这个秋天，最长情的路线是回家，最心动的路线是出发。时尚、美妆、旅行、音乐、科技、生活记录，精选达人备好一份假期灵感清单。',
    cover: bookletMidautumn,
    aspect: 3168 / 1344,
    docUrl: 'https://bytedance.larkoffice.com/wiki/CkBdw9OyeiDzR9kZm9vcEvgfnvf',
    wechatUrl: 'https://mp.weixin.qq.com/s/3-aG_XJLrWNymrzstpxv7Q',
    publishedAt: '2026.09.15 发布',
    wechatStatus: 'published',
  },
];

export function FeaturedTalentSidebarEntry({
  onOpen,
  active,
}: {
  onOpen: () => void;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      className={
        active
          ? 'sidebar-rail sidebar-feature-entry sidebar-feature-entry-top active'
          : 'sidebar-rail sidebar-feature-entry sidebar-feature-entry-top'
      }
      onClick={onOpen}
    >
      <span className="sidebar-feature-entry-label">精选达人介绍</span>
      <small>首页导览与查询入口</small>
    </button>
  );
}
