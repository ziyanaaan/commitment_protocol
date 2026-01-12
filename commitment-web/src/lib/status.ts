export const actionsByStatus: Record<string, string[]> = {
  draft: ["fund"],
  funded: ["pay"],
  paid: ["lock"],
  locked: ["deliver"],
  delivered: [],
  expired: [],
  settled: [],
};
