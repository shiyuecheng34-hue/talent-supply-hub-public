import type { JsonValue } from '@aeolus/feishu-table-sdk';

export type PublicSheetResult = {
  headers: JsonValue[];
  rows: JsonValue[][];
  source?: 'snapshot';
  capturedAt?: string;
};

const cache = new Map<string, Promise<PublicSheetResult>>();

export function clearPublicSheetCache(bindingId?: string) {
  if (bindingId) {
    cache.delete(bindingId);
    return;
  }
  cache.clear();
}

export function fetchPublicSheet(
  bindingId: string,
): Promise<PublicSheetResult> {
  const cached = cache.get(bindingId);
  if (cached) return cached;
  const request = fetch(`./downloads/${bindingId}.data`).then(
    async response => {
      if (!response.ok) {
        throw new Error(`快照读取失败（HTTP ${response.status}）`);
      }
      const data = (await response.json()) as PublicSheetResult;
      if (
        !Array.isArray(data.headers) ||
        !data.headers.length ||
        !Array.isArray(data.rows)
      ) {
        throw new Error('快照结构无效');
      }
      return data;
    },
  );
  cache.set(bindingId, request);
  return request;
}
