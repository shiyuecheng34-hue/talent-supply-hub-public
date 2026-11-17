import { ArrowUpRight, BookOpen } from 'lucide-react';
import { BOOKLETS } from './AgencyBookletRail';

export function BookletModule() {
  return (
    <div id="module-content" className="enter booklet-module">
      <section className="content-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">FEATURED TALENT · RATE CARDS</span>
            <h2>精选达人推荐刊例</h2>
            <p>
              双旦、双
              11、中秋国庆三期巨量星图精选达人特刊，点击卡片在飞书中查看完整刊例。
            </p>
          </div>
        </div>
        <div className="booklet-page-grid">
          {BOOKLETS.map((booklet, index) => (
            <a
              key={booklet.url}
              className="booklet-page-card"
              href={booklet.url}
              target="_blank"
              rel="noreferrer"
            >
              <span className="booklet-page-index">0{index + 1}</span>
              <div className="booklet-page-body">
                <strong>{booklet.title}</strong>
                <small>
                  <BookOpen size={13} /> 飞书 Wiki · 点击查看完整刊例
                </small>
              </div>
              <ArrowUpRight size={20} className="booklet-page-arrow" />
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
