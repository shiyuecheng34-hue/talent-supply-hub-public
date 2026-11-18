import type {
  FeishuSheetRangeBinding,
  FeishuSheetRangeData,
  JsonValue,
} from '@aeolus/feishu-table-sdk';
import manifest from '../../web-application.json';

const GLUE_ENDPOINT =
  '/aeolus/glue/api/v1/ai_dashboard_util/feishu/sheet/read_range';

/** 单次拉取行数，分段串行请求，避免单次响应过大或网关超时。 */
const PAGE_SIZE = 5000;

/** 与 SDK 内部逻辑保持一致：从 URL query 读取运行时鉴权信息。 */
function getRuntimeAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const params = new URLSearchParams(window.location.search);
  const headers: Record<string, string> = {};
  const token = params.get('token')?.trim();
  const jwtToken = params.get('jwtToken')?.trim();
  const externalHeader = params.get('externalHeader')?.trim();
  if (token) headers['Open-Api-Token'] = token;
  if (jwtToken) {
    headers['Aeolus-Authorization'] = /^Bearer\s+/i.test(jwtToken)
      ? jwtToken
      : `Bearer ${jwtToken}`;
  }
  if (externalHeader) headers['External-Header'] = externalHeader;
  return headers;
}

function findBinding(bindingId: string): FeishuSheetRangeBinding | undefined {
  return manifest.feishuResourceBindings?.find(
    item => item.bindingId === bindingId && item.resourceType === 'sheetRange',
  ) as FeishuSheetRangeBinding | undefined;
}

async function readRange(
  bindingId: string,
  range: string,
  signal?: AbortSignal,
): Promise<FeishuSheetRangeData> {
  const body: Record<string, unknown> = { bindingId, range };
  if (window.__AEOLUS_FEISHU_SEND_BINDING__ === true) {
    const binding = findBinding(bindingId);
    if (binding) body.binding = binding;
  }
  const response = await fetch(GLUE_ENDPOINT, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'content-type': 'application/json',
      ...getRuntimeAuthHeaders(),
    },
    body: JSON.stringify(body),
    signal,
  });
  const payload = await response.json();
  if (!response.ok || payload?.success !== true) {
    throw new Error(
      payload?.error?.message ??
        `飞书表格全量读取失败（HTTP ${response.status}）`,
    );
  }
  return payload.data as FeishuSheetRangeData;
}

function isEmptyRow(row: readonly JsonValue[]): boolean {
  return row.every(
    value =>
      value === null ||
      value === undefined ||
      (typeof value === 'string' && value.trim() === ''),
  );
}

export type FullSheetResult = {
  headers: JsonValue[];
  rows: JsonValue[][];
  source?: 'snapshot';
  capturedAt?: string;
};

/**
 * 分段拉取某张飞书工作表的全量数据。
 * @param bindingId manifest 中的 sheetRange binding id
 * @param columnEnd 数据最后一列的列字母（如行业表 AC、节点表 AN）
 * @param expectedRows 预期数据行数（不含表头），用于估算分段数
 */
export async function fetchFullSheet(
  bindingId: string,
  columnEnd: string,
  expectedRows: number,
  signal?: AbortSignal,
): Promise<FullSheetResult> {
  const maxSegments = Math.max(1, Math.ceil(expectedRows / PAGE_SIZE) + 2);
  const collected: JsonValue[][] = [];
  let headers: JsonValue[] = [];
  let reachedEnd = false;

  for (let segment = 0; segment < maxSegments; segment += 1) {
    const startRow = segment === 0 ? 1 : 2 + segment * PAGE_SIZE;
    const endRow =
      segment === 0 ? PAGE_SIZE + 1 : (segment + 1) * PAGE_SIZE + 1;
    const data = await readRange(
      bindingId,
      `A${startRow}:${columnEnd}${endRow}`,
      signal,
    );
    const rawValues = (data.rawValues ?? []) as JsonValue[][];
    if (rawValues.length === 0) {
      reachedEnd = true;
      break;
    }

    if (segment === 0) {
      headers = rawValues[0] ?? [];
      collected.push(...rawValues.slice(1));
    } else {
      collected.push(...rawValues);
    }

    // 实际返回行数少于请求范围，说明已读到工作表末尾。
    const requestedRows = endRow - startRow + 1;
    if (rawValues.length < requestedRows) {
      reachedEnd = true;
      break;
    }
  }

  const rows = collected.filter(row => !isEmptyRow(row));
  if (!reachedEnd || !headers.length || rows.length < expectedRows) {
    throw new Error(
      `全量校验未通过：预期至少 ${expectedRows} 条，实际 ${rows.length} 条`,
    );
  }
  return { headers, rows };
}

/** 无风神会话或接口失败时使用经过源表行数校验的完整快照，绝不回退100条样本。 */
export async function fetchIndustryDownload(
  bindingId: string,
  expectedRows: number,
): Promise<FullSheetResult> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 30_000);
  try {
    return await fetchFullSheet(
      bindingId,
      'AC',
      expectedRows,
      controller.signal,
    );
  } catch (liveError) {
    console.warn('实时全量读取不可用，尝试完整源表快照', liveError);
    if (!/^industry-[a-z]+$/.test(bindingId)) {
      throw new Error('未知行业下载分组');
    }
    const response = await fetch(`/downloads/${bindingId}.data`);
    if (!response.ok) throw new Error('完整源表快照读取失败');
    const data = (await response.json()) as FullSheetResult;
    if (
      data.source !== 'snapshot' ||
      !data.capturedAt ||
      !Array.isArray(data.headers) ||
      data.headers.length !== 29 ||
      !Array.isArray(data.rows) ||
      data.rows.length !== expectedRows
    ) {
      throw new Error('完整源表快照校验失败，未生成文件');
    }
    return data;
  } finally {
    window.clearTimeout(timer);
  }
}
