import { ArrowUpRight, BookOpen, FileText, Megaphone } from 'lucide-react';
import { BOOKLETS } from './AgencyBookletRail';

export function BookletModule() {
  return (
    <div id="module-content" className="enter booklet-module">
      <section className="content-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">FEATURED TALENT · RATE CARDS</span>
            <h2>精选达人推荐刊例</h2>
            <p>双旦、双 11、中秋国庆三期巨量星图精选达人特刊。</p>
          </div>
        </div>
        <div className="booklet-page-grid">
          {BOOKLETS.map(booklet => (
            <article className="booklet-page-card" key={booklet.id}>
              <a
                className="booklet-cover"
                href={booklet.docUrl}
                target="_blank"
                rel="noreferrer"
                style={{ aspectRatio: String(booklet.aspect) }}
                aria-label={`打开文档：${booklet.title}`}
              >
                <img src={booklet.cover} alt={`${booklet.issue}封面`} />
                <span className="booklet-cover-tag">{booklet.issue}</span>
              </a>
              <div className="booklet-page-body">
                <strong>{booklet.title}</strong>
                <p>{booklet.summary}</p>
                <small className="booklet-meta">
                  <BookOpen size={13} />
                  巨量星图营销观察 · {booklet.publishedAt}
                </small>
                <div className="booklet-actions">
                  <a
                    className="booklet-btn booklet-btn-primary"
                    href={booklet.docUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <FileText size={14} />
                    点击进入文档
                    <ArrowUpRight size={14} />
                  </a>
                  {booklet.wechatStatus === 'published' && booklet.wechatUrl ? (
                    <a
                      className="booklet-btn"
                      href={booklet.wechatUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Megaphone size={14} />
                      点击进入公众号
                      <ArrowUpRight size={14} />
                    </a>
                  ) : (
                    <span
                      className="booklet-btn booklet-btn-disabled"
                      title="该期公众号文章尚未发布，链接后续补充"
                      aria-disabled="true"
                    >
                      <Megaphone size={14} />
                      点击进入公众号
                      <em>待发布</em>
                    </span>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
