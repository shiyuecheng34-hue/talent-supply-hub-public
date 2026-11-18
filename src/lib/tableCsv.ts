export function csvEscape(value: unknown) {
  const normalized = value === null || value === undefined ? '' : String(value);
  return `"${normalized.replace(/"/g, '""')}"`;
}

export function downloadRowsTable(
  fileLabel: string,
  headers: readonly unknown[],
  rows: readonly (readonly unknown[])[],
  idHeader = '达人星图id',
) {
  const idIndex = headers.indexOf(idHeader);
  const csvLines = [headers, ...rows].map((line, lineIndex) =>
    line
      .map((value, columnIndex) => {
        let normalized =
          value === null || value === undefined ? '' : String(value);
        if (lineIndex > 0 && columnIndex === idIndex && normalized) {
          normalized = `="${normalized.trim().replace(/\.0+$/, '')}"`;
        }
        return csvEscape(normalized);
      })
      .join(','),
  );
  const blob = new Blob([`\uFEFF${csvLines.join('\r\n')}`], {
    type: 'text/csv;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileLabel;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  link.remove();
  // 异步全量读取后，给浏览器足够时间接管 Blob 下载，避免立即释放导致下载取消。
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
