export function shuffleNodeRows<T>(
  rows: T[],
  seed: number,
  id: (row: T) => string,
  previousFirst: string | null,
): T[] {
  const result = [...rows];
  let state = seed >>> 0;
  const random = () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 4294967296;
  };
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  if (result.length > 1 && id(result[0]) === previousFirst) {
    const next = result.findIndex(row => id(row) !== previousFirst);
    if (next > 0) [result[0], result[next]] = [result[next], result[0]];
  }
  return result;
}
