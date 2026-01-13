export const actionsByStatus: Record<string, string[]> = {
  draft: ["fund"],   // Pay button
  funded: [],        // waiting for payment verification
  paid: ["lock"],
  locked: ["deliver"],
  delivered: [],
  expired: [],
  settled: [],
};
