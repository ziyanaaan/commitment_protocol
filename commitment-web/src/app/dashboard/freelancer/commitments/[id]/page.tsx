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

export default function FreelancerCommitmentDetailPage() {
    const { id } = useParams<{ id: string }>();
    const router = useRouter();
    const [commitment, setCommitment] = useState<Commitment | null>(null);
    const [settlement, setSettlement] = useState<Settlement | null>(null);
    const [preview, setPreview] = useState<Preview | null>(null);
    const [financialStatus, setFinancialStatus] = useState<FinancialStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Evidence inputs for delivery
    const [githubUrl, setGithubUrl] = useState("");
    const [screenshotUrl, setScreenshotUrl] = useState("");
    const [showDeliveryConfirm, setShowDeliveryConfirm] = useState(false);

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

                // Load financial status for payout tracking
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

    // Handle Lock action
    async function handleLock() {
        setActionLoading("lock");
        setError(null);

        try {
            await api(`/commitments/${id}/lock`, { method: "POST" });
            await load();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to lock commitment");
        } finally {
            setActionLoading(null);
        }
    }

    // Handle Deliver action
    async function handleDeliver() {
        // Build evidences array
        const evidences: { type: string; url: string }[] = [];
        if (githubUrl.trim()) {
            evidences.push({ type: "github", url: githubUrl.trim() });
        }
        if (screenshotUrl.trim()) {
            evidences.push({ type: "screenshot", url: screenshotUrl.trim() });
        }

        if (evidences.length === 0) {
            setError("Please provide at least one evidence (GitHub URL or Screenshot URL)");
            return;
        }

        setActionLoading("deliver");
        setError(null);
        setShowDeliveryConfirm(false);

        try {
            await api(`/commitments/${id}/deliver`, {
                method: "POST",
                body: JSON.stringify({ evidences }),
            });
            // Reload to see new status
            await load();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to deliver commitment");
        } finally {
            setActionLoading(null);
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

    // Status messages for freelancer
    const statusMessages: Record<string, string> = {
        draft: "Waiting for client to fund this commitment.",
        funded: "Payment is being processed...",
        paid: "Ready to lock! Confirm that you will deliver the work.",
        locked: "Work is in progress. Deliver before the deadline.",
        delivered: "Work delivered. Settlement pending.",
        settled: "This commitment has been settled.",
    };
    const statusMessage = statusMessages[commitment.status] || "";
    const showLock = commitment.status === "paid";
    const showDeliver = commitment.status === "locked";

    return (
        <div className="max-w-4xl mx-auto px-4 py-8">
            {/* Back Link */}
            <button
                onClick={() => router.push("/dashboard/freelancer/commitments")}
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
                            <p className="text-xs text-amber-700 mb-1">Your Payout</p>
                            <p className="text-xl font-bold text-green-600">₹{Number(preview.expected_payout).toLocaleString()}</p>
                        </div>
                        <div>
                            <p className="text-xs text-amber-700 mb-1">Client Refund</p>
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

            {/* Lock Button */}
            {showLock && (
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6 mb-6">
                    <h2 className="font-semibold text-[#5C4033] mb-2">Lock This Commitment</h2>
                    <p className="text-sm text-[#8A796E] mb-4">
                        By locking, you confirm you will deliver the work by the deadline.
                    </p>
                    <button
                        onClick={handleLock}
                        disabled={actionLoading === "lock"}
                        className="w-full py-3 px-4 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                    >
                        {actionLoading === "lock" ? "Locking..." : "Lock Commitment"}
                    </button>
                </div>
            )}

            {/* Deliver Section */}
            {showDeliver && (
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6 mb-6">
                    <h2 className="font-semibold text-[#5C4033] mb-2">Deliver Work</h2>
                    <p className="text-sm text-[#8A796E] mb-4">
                        Provide at least one form of evidence to prove your work is complete.
                    </p>

                    {/* Evidence Inputs */}
                    <div className="space-y-4 mb-6">
                        <div>
                            <label className="block text-sm font-medium text-[#5C4033] mb-2">
                                GitHub Repository URL (optional)
                            </label>
                            <input
                                type="url"
                                value={githubUrl}
                                onChange={(e) => setGithubUrl(e.target.value)}
                                placeholder="https://github.com/username/repository"
                                className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-[#5C4033] mb-2">
                                Screenshot URL (optional)
                            </label>
                            <input
                                type="url"
                                value={screenshotUrl}
                                onChange={(e) => setScreenshotUrl(e.target.value)}
                                placeholder="https://example.com/screenshot.png"
                                className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                            />
                            <p className="text-xs text-[#8A796E] mt-1">Supported: PNG, JPG, JPEG, WEBP (max 5MB)</p>
                            <p className="text-xs text-[#8A796E] mt-1">*To get https link for you screenshot. upload it in <a href="https://imgur.com" target="_blank" rel="noopener noreferrer">imgur.com</a>, then copy image address from it</p>
                        </div>
                    </div>

                    <button
                        onClick={() => setShowDeliveryConfirm(true)}
                        disabled={actionLoading === "deliver" || (!githubUrl.trim() && !screenshotUrl.trim())}
                        className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        {actionLoading === "deliver" ? "Delivering..." : "Mark as Delivered"}
                    </button>
                </div>
            )}

            {/* Delivery Confirmation Modal */}
            {showDeliveryConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                        <h3 className="font-semibold text-[#5C4033] text-lg mb-2">Confirm Delivery</h3>
                        <p className="text-sm text-[#8A796E] mb-4">
                            This action cannot be undone. Your evidence will be validated and settlement will be processed.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowDeliveryConfirm(false)}
                                className="flex-1 py-2 px-4 bg-gray-100 text-[#5C4033] font-medium rounded-lg hover:bg-gray-200 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDeliver}
                                disabled={actionLoading === "deliver"}
                                className="flex-1 py-2 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                            >
                                {actionLoading === "deliver" ? "..." : "Confirm"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Settlement Summary - Only show when settled */}
            {commitment.status === "settled" && (
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6">
                    <h2 className="font-semibold text-[#5C4033] mb-4">Settlement Complete</h2>
                    {settlement && (
                        <div className="bg-green-50 rounded-lg p-4 mb-4">
                            <p className="text-sm text-green-700">Your Payout</p>
                            <p className="text-2xl font-semibold text-green-800">₹{settlement.payout_amount.toLocaleString()}</p>
                        </div>
                    )}

                    {/* Financial Status */}
                    {financialStatus && (
                        <div className="border border-[#CCBEB1]/30 rounded-lg p-4 mb-4">
                            <h3 className="text-sm font-medium text-[#5C4033] mb-3">Transfer Status</h3>
                            <div className="space-y-3">
                                {financialStatus.payout_status && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-[#8A796E]">Payout</span>
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${financialStatus.payout_status === "completed"
                                                ? "bg-green-100 text-green-700"
                                                : financialStatus.payout_status === "failed" || financialStatus.payout_status === "manual_review"
                                                    ? "bg-red-100 text-red-700"
                                                    : "bg-amber-100 text-amber-700"
                                            }`}>
                                            {financialStatus.payout_status === "queued" && "Queued"}
                                            {financialStatus.payout_status === "processing" && "Processing..."}
                                            {financialStatus.payout_status === "completed" && "Completed ✓"}
                                            {financialStatus.payout_status === "failed" && "Failed"}
                                            {financialStatus.payout_status === "retrying" && "Retrying..."}
                                            {financialStatus.payout_status === "manual_review" && "Under Review"}
                                        </span>
                                    </div>
                                )}

                                {financialStatus.refund_status && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-[#8A796E]">Client Refund</span>
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${financialStatus.refund_status === "processed"
                                                ? "bg-green-100 text-green-700"
                                                : financialStatus.refund_status === "failed"
                                                    ? "bg-red-100 text-red-700"
                                                    : "bg-amber-100 text-amber-700"
                                            }`}>
                                            {financialStatus.refund_status === "created" && "Pending"}
                                            {financialStatus.refund_status === "pending_gateway" && "Processing..."}
                                            {financialStatus.refund_status === "processed" && "Refunded ✓"}
                                            {financialStatus.refund_status === "failed" && "Failed"}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {(financialStatus.payout_status === "queued" ||
                                financialStatus.payout_status === "processing" ||
                                financialStatus.payout_status === "retrying") && (
                                    <p className="text-xs text-[#8A796E] mt-3 italic">
                                        Payouts typically arrive within 1-3 business days.
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
