export const actionsByStatus: Record<string, string[]> = {
  draft: ["fund"],   // Pay button
  funded: [],        // waiting for payment verification
  paid: ["lock"],
  locked: ["deliver"],
  delivered: [],     // settlement happens automatically on delivery (backend)
  expired: [],
  settled: [],
};

// Status display info for UI
export const statusInfo: Record<string, { label: string; color: string; bgColor: string }> = {
  draft: { label: "Draft", color: "#6B7280", bgColor: "#F3F4F6" },
  funded: { label: "Funded", color: "#D97706", bgColor: "#FEF3C7" },
  paid: { label: "Paid", color: "#059669", bgColor: "#D1FAE5" },
  locked: { label: "Locked", color: "#7C3AED", bgColor: "#EDE9FE" },
  delivered: { label: "Delivered", color: "#2563EB", bgColor: "#DBEAFE" },
  expired: { label: "Expired", color: "#DC2626", bgColor: "#FEE2E2" },
  settled: { label: "Settled", color: "#047857", bgColor: "#A7F3D0" },
};
