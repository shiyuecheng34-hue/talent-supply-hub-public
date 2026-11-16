import monetization from '@/data/qianchuan-monetization.json';
import overall from '@/data/qianchuan-overall.json';
import { agencyPagination } from '@/lib/agencyPagination';
import { useFeishuSheetRange } from '@aeolus/feishu-table-sdk';
import { useMemo, useState } from 'react';
import { AgencyAvatar } from './AgencyAvatar';
import { AgencyPager } from './AgencyPager';

function SheetList({
  title,
  bindingId,
  snapshot,
}: { title: string; bindingId: string; snapshot: typeof overall }) {
  const [page, setPage] = useState(1);
  // 请求整个已确认物理范围，而非前100条；不完整或ID类型不安全时不得当成全量。
  const sheet = useFeishuSheetRange({
    bindingId,
    range: `A1:B${snapshot.meta.physicalRows}`,
  });
  const live = useMemo(() => {
    const values = sheet.data?.rawValues;
    if (
      !values ||
      values.length !== snapshot.meta.physicalRows ||
      values[0]?.[0] !== '星图达人id' ||
      values[0]?.[1] !== '达人昵称'
    )
      return null;
    const rows = values.slice(1);
    if (!rows.every(r => typeof r[0] === 'string' && /^\d+$/.test(r[0])))
      return null;
    return rows.map((r, i) => ({
      id: String(r[0]),
      name: String(r[1] ?? ''),
      sourceRow: i + 2,
    }));
  }, [sheet.data]);
  const records = live ?? snapshot.records;
  const pagination = agencyPagination(records.length, page);
  return (
    <section className="min-w-0">
      <h2 className="text-3xl font-semibold text-slate-100 mb-4">{title}</h2>
      <div className="rounded-2xl border border-slate-600 bg-slate-900 p-6">
        <AgencyPager
          total={records.length}
          page={pagination.page}
          onChange={setPage}
        />
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr>
                {['头像', '星图达人 ID', '达人名称'].map(h => (
                  <th className="p-3 border-b border-slate-700" key={h}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {records.slice(pagination.offset, pagination.end).map(r => (
                <tr key={`${r.sourceRow}-${r.id}`}>
                  <td className="p-3">
                    <AgencyAvatar id={r.id} name={r.name} />
                  </td>
                  <td className="p-3">{r.id}</td>
                  <td className="p-3">{r.name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <AgencyPager
          total={records.length}
          page={pagination.page}
          onChange={setPage}
        />
      </div>
    </section>
  );
}

export function QianchuanLists() {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-6">
      <SheetList
        title="整体底池"
        bindingId="qianchuan-overall"
        snapshot={overall}
      />
      <SheetList
        title="千川代理关注变现"
        bindingId="qianchuan-monetization"
        snapshot={monetization}
      />
    </div>
  );
}
