import { INDUSTRY_OPTIONS, INDUSTRY_TOTAL } from '../data/industryOptions';

const RADIUS = 72;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function IndustryShareDonut() {
  let accumulated = 0;

  return (
    <div
      className="industry-share-donut"
      role="img"
      aria-label={`11 个重点行业供给占比，总供给 ${INDUSTRY_TOTAL.toLocaleString()} 位达人`}
    >
      <svg viewBox="0 0 180 180" aria-hidden="true">
        <circle
          className="industry-share-track"
          cx="90"
          cy="90"
          r={RADIUS}
          fill="none"
          strokeWidth="18"
        />
        {INDUSTRY_OPTIONS.map(industry => {
          const segmentLength =
            (industry.count / INDUSTRY_TOTAL) * CIRCUMFERENCE;
          const offset = -accumulated;
          accumulated += segmentLength;
          const percent = ((industry.count / INDUSTRY_TOTAL) * 100).toFixed(1);

          return (
            <circle
              key={industry.id}
              cx="90"
              cy="90"
              r={RADIUS}
              fill="none"
              stroke={industry.color}
              strokeWidth="18"
              strokeDasharray={`${segmentLength} ${CIRCUMFERENCE - segmentLength}`}
              strokeDashoffset={offset}
            >
              <title>
                {industry.label}：{industry.count.toLocaleString()}（{percent}
                %）
              </title>
            </circle>
          );
        })}
      </svg>
      <div className="industry-share-center">
        <strong>{INDUSTRY_TOTAL.toLocaleString()}</strong>
        <span>总供给</span>
      </div>
    </div>
  );
}
