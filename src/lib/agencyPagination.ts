export const AGENCY_PAGE_SIZE = 50;

export function agencyPagination(total: number, requestedPage: number) {
  const totalPages = Math.max(1, Math.ceil(total / AGENCY_PAGE_SIZE));
  const page = Math.min(totalPages, Math.max(1, requestedPage));
  const offset = (page - 1) * AGENCY_PAGE_SIZE;
  const end = Math.min(total, offset + AGENCY_PAGE_SIZE);
  const pageNumbers = Array.from(
    { length: totalPages },
    (_, i) => i + 1,
  ).filter(n => n === 1 || n === totalPages || Math.abs(n - page) <= 2);
  return {
    page,
    totalPages,
    offset,
    end,
    start: total ? offset + 1 : 0,
    pageNumbers,
  };
}
