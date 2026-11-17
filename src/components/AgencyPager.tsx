import { agencyPagination } from '@/lib/agencyPagination';

export function AgencyPager({
  total,
  page,
  onChange,
  ariaLabel = '代理商重点分页',
}: {
  total: number;
  page: number;
  onChange: (page: number) => void;
  ariaLabel?: string;
}) {
  const data = agencyPagination(total, page);
  const buttonClass =
    'rounded-lg border border-slate-600 px-3 py-2 text-sm disabled:opacity-40 disabled:cursor-not-allowed';
  return (
    <nav
      aria-label={ariaLabel}
      className="flex flex-wrap gap-2 items-center my-4"
    >
      <span className="text-sm mr-2" aria-live="polite">
        共 {total.toLocaleString()} 条 · 第 {data.page} / {data.totalPages} 页 ·
        展示 {data.start}–{data.end} 条
      </span>
      <button
        className={buttonClass}
        disabled={data.page === 1 || !total}
        onClick={() => onChange(data.page - 1)}
      >
        上一页
      </button>
      {data.pageNumbers.map((n, i) => (
        <span key={n} className="flex gap-2 items-center">
          {i > 0 && n - data.pageNumbers[i - 1] > 1 && (
            <span aria-hidden="true">…</span>
          )}
          <button
            className={`${buttonClass} ${n === data.page ? 'bg-cyan-900 text-cyan-200' : ''}`}
            aria-label={`第 ${n} 页`}
            aria-current={n === data.page ? 'page' : undefined}
            disabled={!total}
            onClick={() => onChange(n)}
          >
            {n}
          </button>
        </span>
      ))}
      <button
        className={buttonClass}
        disabled={data.page >= data.totalPages || !total}
        onClick={() => onChange(data.page + 1)}
      >
        下一页
      </button>
    </nav>
  );
}
