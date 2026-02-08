"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { statusInfo } from "@/lib/status";

type Commitment = {
    id: number;
    status: string;
    amount: number;
    deadline: string;
    title: string;
    description: string;
    decay_curve: string;
    created_at: string;
};

type Settlement = {
    id: number;
    payout_amount: number;
    refund_amount: number;
    settled_at: string;
};

type Preview = {
    expected_payout: number;
    expected_refund: number;
    delay_minutes: number;
};

type FinancialStatus = {
    payment_status: string;
    payout_status: string | null;
    payout_amount: number | null;
    refund_status: string | null;
    refund_amount: number | null;
};

export default function ClientCommitmentDetailPage() {
    const { id } = useParams<{ id: string }>();
    const router = useRouter();
    const [commitment, setCommitment] = useState<Commitment | null>(null);
    const [settlement, setSettlement] = useState<Settlement | null>(null);
    const [preview, setPreview] = useState<Preview | null>(null);
    const [financialStatus, setFinancialStatus] = useState<FinancialStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        try {
            setLoading(true);
            const data = await api<Commitment>(`/commitments/${id}`);
            setCommitment(data);

            // Load settlement if settled
            if (data.status === "settled") {
                try {
                    const s = await api<Settlement>(`/settlements/${id}`);
                    setSettlement(s);
                } catch {
                    // Settlement might not exist yet
                }

                // Load financial status for refund tracking
                try {
                    const fs = await api<FinancialStatus>(`/settlements/${id}/financial-status`);
                    setFinancialStatus(fs);
                } catch {
                    // Financial status might not exist
                }
            } else {
                // Load live preview for non-settled commitments
                try {
                    const p = await api<Preview>(`/commitments/${id}/preview`);
                    setPreview(p);
                } catch {
                    setPreview(null);
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load commitment");
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        load();
    }, [load]);

    // Handle Fund action
    async function handleFund() {
        if (!commitment) return;
        setActionLoading(true);
        setError(null);

        try {
            // Create Razorpay order
            const res = await api<{
                razorpay_key: string;
                amount: number;
                currency: string;
                order_id: string;
            }>(`/commitments/${id}/fund`, { method: "POST" });

            // Open Razorpay checkout
            const rzpOptions = {
                key: res.razorpay_key,
                amount: res.amount,
                currency: res.currency,
                order_id: res.order_id,
                name: "Pledgos",
                description: `Commitment #${id}: ${commitment.title}`,
                handler: async function (response: {
                    razorpay_order_id: string;
                    razorpay_payment_id: string;
                    razorpay_signature: string;
                }) {
                    try {
                        await api("/payments/verify", {
                            method: "POST",
                            body: JSON.stringify({
                                razorpay_order_id: response.razorpay_order_id,
                                razorpay_payment_id: response.razorpay_payment_id,
                                razorpay_signature: response.razorpay_signature,
                            }),
                        });
                        await load();
                    } catch (e) {
                        setError(e instanceof Error ? e.message : "Payment verification failed");
                    }
                },
            };

            interface RazorpayInstance { open: () => void }
            interface RazorpayWindow { Razorpay: new (options: Record<string, unknown>) => RazorpayInstance }
            const rzp = new (window as unknown as RazorpayWindow).Razorpay(rzpOptions);
            rzp.open();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to initiate payment");
        } finally {
            setActionLoading(false);
        }
    }

    if (loading) {
        return (
            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="flex items-center justify-center py-16">
                    <div className="w-8 h-8 border-2 border-[#997E67] border-t-transparent rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    if (error && !commitment) {
        return (
            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                    <p className="text-red-600">{error}</p>
                </div>
            </div>
        );
    }

    if (!commitment) return null;

    const status = statusInfo[commitment.status] || { label: commitment.status, color: "#6B7280", bgColor: "#F3F4F6" };
    const deadline = new Date(commitment.deadline);

    // Status messages for client
    const statusMessages: Record<string, string> = {
        draft: "This commitment needs to be funded to proceed.",
        funded: "Payment is being processed...",
        paid: "Waiting for freelancer to lock and start work.",
        locked: "Work is in progress.",
        delivered: "Work has been delivered. Settlement pending.",
        settled: "This commitment has been settled.",
    };
    const statusMessage = statusMessages[commitment.status] || "";
    const showFund = commitment.status === "draft";

    return (
        <div className="max-w-4xl mx-auto px-4 py-8">
            {/* Back Link */}
            <button
                onClick={() => router.push("/dashboard/client/commitments")}
                className="flex items-center gap-2 text-[#8A796E] hover:text-[#5C4033] mb-6"
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Commitments
            </button>

            {/* Error */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                    <p className="text-red-600">{error}</p>
                </div>
            )}

            {/* Header Card */}
            <div className="bg-white rounded-xl border border-[#CCBEB1]/30 overflow-hidden mb-6">
                <div className="bg-gradient-to-r from-[#997E67] to-[#5C4634] p-6 text-white">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <p className="text-white/60 text-sm mb-1">Commitment #{commitment.id}</p>
                            <h1 className="text-2xl font-serif font-semibold">
                                {commitment.title || "Untitled Commitment"}
                            </h1>
                        </div>
                        <span
                            className="px-3 py-1 text-sm font-semibold rounded-full"
                            style={{ backgroundColor: status.bgColor, color: status.color }}
                        >
                            {status.label}
                        </span>
                    </div>
                </div>

                <div className="p-6">
                    {commitment.description && (
                        <p className="text-[#8A796E] mb-6">{commitment.description}</p>
                    )}

                    <div className="grid md:grid-cols-3 gap-4">
                        <div className="bg-[#F9F7F5] rounded-lg p-4">
                            <p className="text-sm text-[#8A796E]">Amount</p>
                            <p className="text-xl font-semibold text-[#5C4033]">₹{commitment.amount.toLocaleString()}</p>
                        </div>
                        <div className="bg-[#F9F7F5] rounded-lg p-4">
                            <p className="text-sm text-[#8A796E]">Deadline</p>
                            <p className="text-xl font-semibold text-[#5C4033]">{deadline.toLocaleDateString()}</p>
                        </div>
                        <div className="bg-[#F9F7F5] rounded-lg p-4">
                            <p className="text-sm text-[#8A796E]">Decay Curve</p>
                            <p className="text-xl font-semibold text-[#5C4033] capitalize">{commitment.decay_curve}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Live Payout Preview - Only show for non-settled */}
            {preview && commitment.status !== "settled" && (
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-6 mb-6">
                    <div className="flex items-center gap-2 mb-4">
                        <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h3 className="font-semibold text-amber-800">
                            {commitment.status === "delivered" ? "Settlement Preview" : "If Settled Now"}
                        </h3>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <p className="text-xs text-amber-700 mb-1">Freelancer Payout</p>
                            <p className="text-xl font-bold text-green-600">₹{Number(preview.expected_payout).toLocaleString()}</p>
                        </div>
                        <div>
                            <p className="text-xs text-amber-700 mb-1">Your Refund</p>
                            <p className="text-xl font-bold text-blue-600">₹{Number(preview.expected_refund).toLocaleString()}</p>
                        </div>
                        <div>
                            <p className="text-xs text-amber-700 mb-1">Delay</p>
                            <p className="text-xl font-bold text-[#5C4033]">
                                {preview.delay_minutes > 0 ? `${preview.delay_minutes} min` : "On time"}
                            </p>
                        </div>
                    </div>
                    <p className="text-xs text-amber-600 mt-3 italic">
                        * Live preview from backend. Final settlement may differ based on delivery time.
                    </p>
                </div>
            )}

            {/* Status Message */}
            <div className="bg-[#FFDBBB]/20 border border-[#FFDBBB] rounded-xl p-4 mb-6">
                <p className="text-[#5C4033]">{statusMessage}</p>
            </div>

            {/* Fund Button - Only show for draft status */}
            {showFund && (
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6 mb-6">
                    <h2 className="font-semibold text-[#5C4033] mb-4">Fund This Commitment</h2>
                    <button
                        onClick={handleFund}
                        disabled={actionLoading}
                        className="w-full py-3 px-4 bg-[#997E67] text-white font-medium rounded-lg hover:bg-[#856b56] disabled:opacity-50 transition-colors"
                    >
                        {actionLoading ? "Processing..." : `Pay ₹${commitment.amount.toLocaleString()}`}
                    </button>
                </div>
            )}

            {/* Settlement Summary - Only show when settled */}
            {commitment.status === "settled" && (
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6">
                    <h2 className="font-semibold text-[#5C4033] mb-4">Settlement Complete</h2>
                    {settlement && (
                        <div className="grid md:grid-cols-2 gap-4 mb-4">
                            <div className="bg-green-50 rounded-lg p-4">
                                <p className="text-sm text-green-700">Freelancer Payout</p>
                                <p className="text-xl font-semibold text-green-800">₹{settlement.payout_amount.toLocaleString()}</p>
                            </div>
                            <div className="bg-blue-50 rounded-lg p-4">
                                <p className="text-sm text-blue-700">Your Refund</p>
                                <p className="text-xl font-semibold text-blue-800">₹{settlement.refund_amount.toLocaleString()}</p>
                            </div>
                        </div>
                    )}

                    {/* Refund Status */}
                    {financialStatus && financialStatus.refund_status && settlement && settlement.refund_amount > 0 && (
                        <div className="border border-[#CCBEB1]/30 rounded-lg p-4 mb-4">
                            <div className="flex items-center justify-between">
                                <span className="text-sm text-[#8A796E]">Refund Status</span>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${financialStatus.refund_status === "processed"
                                        ? "bg-green-100 text-green-700"
                                        : financialStatus.refund_status === "failed"
                                            ? "bg-red-100 text-red-700"
                                            : "bg-amber-100 text-amber-700"
                                    }`}>
                                    {financialStatus.refund_status === "created" && "Pending"}
                                    {financialStatus.refund_status === "pending_gateway" && "Processing..."}
                                    {financialStatus.refund_status === "processed" && "Refunded ✓"}
                                    {financialStatus.refund_status === "failed" && "Failed - Contact Support"}
                                </span>
                            </div>

                            {(financialStatus.refund_status === "created" ||
                                financialStatus.refund_status === "pending_gateway") && (
                                    <p className="text-xs text-[#8A796E] mt-2 italic">
                                        Refunds typically appear within 5-7 business days.
                                    </p>
                                )}
                        </div>
                    )}

                    <button
                        onClick={() => router.push(`/result/${id}`)}
                        className="w-full py-3 px-4 bg-[#FFDBBB] text-[#5C4033] font-medium rounded-lg hover:bg-[#ffcfa6] transition-colors flex items-center justify-center gap-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        View Detailed Settlement
                    </button>
                </div>
            )}
        </div>
    );
}
