"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";

type CommitmentFinancial = {
    commitment: {
        id: number;
        title: string;
        description: string;
        status: string;
        amount: number;
        deadline: string | null;
        decay_curve: string;
        created_at: string | null;
    };
    payment: {
        id: number;
        order_id: string;
        payment_id: string | null;
        amount: number;
        status: string;
    } | null;
    settlement: {
        id: number;
        payout_amount: number;
        refund_amount: number;
        delay_minutes: number;
        decay_applied: string;
        settled_at: string | null;
    } | null;
    ledger_entries: Array<{
        id: number;
        entry_type: string;
        amount: number;
        running_balance: number;
        reference_type: string | null;
        reference_id: number | null;
        created_at: string | null;
    }>;
};

export default function CommitmentFinancialPage() {
    const { id } = useParams<{ id: string }>();
    const router = useRouter();
    const [data, setData] = useState<CommitmentFinancial | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const result = await api<CommitmentFinancial>(`/admin/commitments/${id}/financial`);
                setData(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [id]);

    if (loading) {
        return (
            <div className="p-8">
                <div className="flex items-center justify-center py-16">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="p-8">
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400">{error || "Not found"}</p>
                </div>
            </div>
        );
    }

    const { commitment, payment, settlement, ledger_entries } = data;

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <button
                        onClick={() => router.back()}
                        className="text-slate-400 hover:text-white mb-2"
                    >
                        ← Back
                    </button>
                    <h1 className="text-2xl font-bold text-white">
                        Commitment #{commitment.id} - Financial Timeline
                    </h1>
                    <p className="text-slate-400">{commitment.title}</p>
                </div>
                <StatusBadge status={commitment.status} />
            </div>

            {/* Commitment Details */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-6">
                <h2 className="text-lg font-semibold text-white mb-4">Commitment Details</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <p className="text-sm text-slate-400">Amount</p>
                        <p className="text-white font-medium">₹{commitment.amount.toLocaleString()}</p>
                    </div>
                    <div>
                        <p className="text-sm text-slate-400">Decay Curve</p>
                        <p className="text-white font-medium capitalize">{commitment.decay_curve}</p>
                    </div>
                    <div>
                        <p className="text-sm text-slate-400">Deadline</p>
                        <p className="text-white font-medium">
                            {commitment.deadline ? new Date(commitment.deadline).toLocaleString() : "-"}
                        </p>
                    </div>
                    <div>
                        <p className="text-sm text-slate-400">Created</p>
                        <p className="text-white font-medium">
                            {commitment.created_at ? new Date(commitment.created_at).toLocaleString() : "-"}
                        </p>
                    </div>
                </div>
                {commitment.description && (
                    <div className="mt-4">
                        <p className="text-sm text-slate-400">Description</p>
                        <p className="text-white">{commitment.description}</p>
                    </div>
                )}
            </div>

            {/* Payment */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-6">
                <h2 className="text-lg font-semibold text-white mb-4">Payment</h2>
                {payment ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <p className="text-sm text-slate-400">Payment ID</p>
                            <p className="text-white font-mono text-sm">{payment.payment_id || "-"}</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Order ID</p>
                            <p className="text-white font-mono text-sm">{payment.order_id}</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Amount</p>
                            <p className="text-white font-medium">₹{payment.amount.toLocaleString()}</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Status</p>
                            <p className="text-white font-medium capitalize">{payment.status}</p>
                        </div>
                    </div>
                ) : (
                    <p className="text-slate-400">No payment recorded</p>
                )}
            </div>

            {/* Settlement */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-6">
                <h2 className="text-lg font-semibold text-white mb-4">Settlement</h2>
                {settlement ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <p className="text-sm text-slate-400">Payout</p>
                            <p className="text-green-400 font-medium">₹{settlement.payout_amount.toLocaleString()}</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Refund</p>
                            <p className="text-orange-400 font-medium">₹{settlement.refund_amount.toLocaleString()}</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Delay</p>
                            <p className="text-white font-medium">{settlement.delay_minutes} min</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-400">Settled At</p>
                            <p className="text-white font-medium">
                                {settlement.settled_at ? new Date(settlement.settled_at).toLocaleString() : "-"}
                            </p>
                        </div>
                    </div>
                ) : (
                    <p className="text-slate-400">Not yet settled</p>
                )}
            </div>

            {/* Ledger Entries */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Ledger Entries</h2>
                {ledger_entries.length > 0 ? (
                    <table className="w-full">
                        <thead>
                            <tr className="text-left text-sm text-slate-400 border-b border-slate-700">
                                <th className="pb-2">Type</th>
                                <th className="pb-2 text-right">Amount</th>
                                <th className="pb-2 text-right">Balance</th>
                                <th className="pb-2">Reference</th>
                                <th className="pb-2">Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ledger_entries.map((entry) => (
                                <tr key={entry.id} className="border-b border-slate-700/50">
                                    <td className="py-2 text-white capitalize">{entry.entry_type.replace("_", " ")}</td>
                                    <td className={`py-2 text-right font-medium ${entry.amount >= 0 ? "text-green-400" : "text-red-400"}`}>
                                        {entry.amount >= 0 ? "+" : ""}₹{entry.amount.toLocaleString()}
                                    </td>
                                    <td className="py-2 text-right text-slate-300">₹{entry.running_balance.toLocaleString()}</td>
                                    <td className="py-2 text-slate-400 text-sm">
                                        {entry.reference_type ? `${entry.reference_type}:${entry.reference_id}` : "-"}
                                    </td>
                                    <td className="py-2 text-slate-400 text-sm">
                                        {entry.created_at ? new Date(entry.created_at).toLocaleString() : "-"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p className="text-slate-400">No ledger entries</p>
                )}
            </div>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const colors: Record<string, string> = {
        draft: "bg-slate-600 text-slate-200",
        paid: "bg-blue-600 text-blue-100",
        locked: "bg-purple-600 text-purple-100",
        delivered: "bg-orange-600 text-orange-100",
        settled: "bg-green-600 text-green-100",
        expired: "bg-red-600 text-red-100",
    };

    return (
        <span className={`px-3 py-1 text-sm font-medium rounded ${colors[status] || "bg-slate-600 text-slate-200"}`}>
            {status}
        </span>
    );
}
