"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Refund = {
    id: string;
    payment_id: string;
    commitment_id: number;
    amount: number;
    currency: string;
    status: string;
    gateway_refund_id: string | null;
    created_at: string | null;
};

type RefundsResult = {
    items: Refund[];
    total: number;
    limit: number;
    offset: number;
    status_counts: Record<string, number>;
};

export default function AdminRefundsPage() {
    const router = useRouter();
    const [results, setResults] = useState<RefundsResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [statusFilter, setStatusFilter] = useState<string>("");

    async function load() {
        try {
            setLoading(true);
            const params = statusFilter ? `?status=${statusFilter}&limit=100` : "?limit=100";
            const data = await api<RefundsResult>(`/admin/refunds/queue${params}`);
            setResults(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        load();
    }, [statusFilter]);

    const getStatusColor = (status: string) => {
        switch (status) {
            case "processed":
                return "bg-green-500/20 text-green-400 border-green-500/30";
            case "created":
                return "bg-blue-500/20 text-blue-400 border-blue-500/30";
            case "pending_gateway":
                return "bg-amber-500/20 text-amber-400 border-amber-500/30";
            case "failed":
                return "bg-red-500/20 text-red-400 border-red-500/30";
            default:
                return "bg-slate-500/20 text-slate-400 border-slate-500/30";
        }
    };

    const formatAmount = (amount: number) => {
        // Amount is in paise, convert to rupees
        return `₹${(amount / 100).toLocaleString()}`;
    };

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Refund Queue</h1>
                <p className="text-slate-400">Monitor and manage client refunds</p>
            </div>

            {error && (
                <div className="mb-6 bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            {/* Status Counts */}
            {results?.status_counts && (
                <div className="mb-6 grid grid-cols-2 md:grid-cols-5 gap-3">
                    <button
                        onClick={() => setStatusFilter("")}
                        className={`p-3 rounded-lg border transition-colors ${statusFilter === "" ? "border-white bg-white/10" : "border-slate-700 bg-slate-800"
                            }`}
                    >
                        <p className="text-xs text-slate-400">All</p>
                        <p className="text-xl font-bold text-white">{results.total}</p>
                    </button>
                    {Object.entries(results.status_counts).map(([status, count]) => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`p-3 rounded-lg border transition-colors ${statusFilter === status ? "border-white bg-white/10" : "border-slate-700 bg-slate-800"
                                }`}
                        >
                            <p className="text-xs text-slate-400 capitalize">{status.replace("_", " ")}</p>
                            <p className="text-xl font-bold text-white">{count}</p>
                        </button>
                    ))}
                </div>
            )}

            {/* Table */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="text-left text-sm text-slate-400 bg-slate-700/50">
                            <th className="px-4 py-3">Refund ID</th>
                            <th className="px-4 py-3">Commitment</th>
                            <th className="px-4 py-3 text-right">Amount</th>
                            <th className="px-4 py-3">Status</th>
                            <th className="px-4 py-3">Gateway ID</th>
                            <th className="px-4 py-3">Created</th>
                            <th className="px-4 py-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                                    Loading...
                                </td>
                            </tr>
                        ) : results?.items.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                                    No refunds found
                                </td>
                            </tr>
                        ) : (
                            results?.items.map((r) => (
                                <tr key={r.id} className="border-t border-slate-700 hover:bg-slate-700/30">
                                    <td className="px-4 py-3 text-white font-mono text-xs">
                                        {r.id.slice(0, 8)}...
                                    </td>
                                    <td className="px-4 py-3 text-blue-400 font-mono">
                                        #{r.commitment_id}
                                    </td>
                                    <td className="px-4 py-3 text-right text-orange-400 font-medium">
                                        {formatAmount(r.amount)}
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(r.status)}`}>
                                            {r.status.replace("_", " ")}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-slate-400 font-mono text-xs">
                                        {r.gateway_refund_id ? r.gateway_refund_id.slice(0, 12) + "..." : "-"}
                                    </td>
                                    <td className="px-4 py-3 text-slate-400 text-sm">
                                        {r.created_at ? new Date(r.created_at).toLocaleString() : "-"}
                                    </td>
                                    <td className="px-4 py-3">
                                        <button
                                            onClick={() => router.push(`/admin/commitments/${r.commitment_id}`)}
                                            className="px-3 py-1 text-sm bg-slate-600 text-white rounded hover:bg-slate-500 transition-colors"
                                        >
                                            View
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {results && (
                <div className="mt-4 text-sm text-slate-400">
                    Showing {results.items.length} of {results.total} refunds
                </div>
            )}
        </div>
    );
}
