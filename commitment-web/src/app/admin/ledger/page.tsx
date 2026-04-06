"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type LedgerEntry = {
    id: number;
    commitment_id: number | null;
    user_id: number | null;
    entry_type: string;
    amount: number;
    running_balance: number;
    reference_type: string | null;
    reference_id: number | null;
    description: string | null;
    created_at: string | null;
};

type LedgerResult = {
    items: LedgerEntry[];
    total: number;
    limit: number;
    offset: number;
};

export default function AdminLedgerPage() {
    const [results, setResults] = useState<LedgerResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [userIdFilter, setUserIdFilter] = useState("");
    const [commitmentIdFilter, setCommitmentIdFilter] = useState("");
    const [typeFilter, setTypeFilter] = useState("");

    async function loadLedger() {
        setLoading(true);
        setError(null);
        try {
            let url = "/admin/ledger?limit=200";
            if (userIdFilter) url += `&user_id=${userIdFilter}`;
            if (commitmentIdFilter) url += `&commitment_id=${commitmentIdFilter}`;
            if (typeFilter) url += `&entry_type=${typeFilter}`;
            const data = await api<LedgerResult>(url);
            setResults(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadLedger();
    }, []);

    function handleFilter(e: React.FormEvent) {
        e.preventDefault();
        loadLedger();
    }

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Ledger Explorer</h1>
                <p className="text-slate-400">Financial audit trail and running balances</p>
            </div>

            {/* Filters */}
            <form onSubmit={handleFilter} className="mb-6 flex gap-4 flex-wrap">
                <input
                    type="text"
                    value={userIdFilter}
                    onChange={(e) => setUserIdFilter(e.target.value)}
                    placeholder="User ID"
                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 w-32"
                />
                <input
                    type="text"
                    value={commitmentIdFilter}
                    onChange={(e) => setCommitmentIdFilter(e.target.value)}
                    placeholder="Commitment ID"
                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 w-40"
                />
                <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">All Types</option>
                    <option value="payment_in">Payment In</option>
                    <option value="payout">Payout</option>
                    <option value="refund">Refund</option>
                    <option value="fee">Fee</option>
                    <option value="adjustment">Adjustment</option>
                </select>
                <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    Filter
                </button>
            </form>

            {error && (
                <div className="mb-6 bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            {/* Table */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-left text-slate-400 bg-slate-700/50">
                            <th className="px-3 py-3">ID</th>
                            <th className="px-3 py-3">Type</th>
                            <th className="px-3 py-3 text-right">Amount</th>
                            <th className="px-3 py-3 text-right">Balance</th>
                            <th className="px-3 py-3">Commitment</th>
                            <th className="px-3 py-3">User</th>
                            <th className="px-3 py-3">Reference</th>
                            <th className="px-3 py-3">Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={8} className="px-3 py-8 text-center text-slate-400">
                                    Loading...
                                </td>
                            </tr>
                        ) : results?.items.length === 0 ? (
                            <tr>
                                <td colSpan={8} className="px-3 py-8 text-center text-slate-400">
                                    No ledger entries found
                                </td>
                            </tr>
                        ) : (
                            results?.items.map((e) => (
                                <tr key={e.id} className="border-t border-slate-700 hover:bg-slate-700/30">
                                    <td className="px-3 py-2 text-white font-mono">#{e.id}</td>
                                    <td className="px-3 py-2">
                                        <TypeBadge type={e.entry_type} />
                                    </td>
                                    <td className={`px-3 py-2 text-right font-medium ${e.amount >= 0 ? "text-green-400" : "text-red-400"}`}>
                                        {e.amount >= 0 ? "+" : ""}₹{e.amount.toLocaleString()}
                                    </td>
                                    <td className="px-3 py-2 text-right text-slate-300">
                                        ₹{e.running_balance.toLocaleString()}
                                    </td>
                                    <td className="px-3 py-2 text-blue-400 font-mono">
                                        {e.commitment_id ? `#${e.commitment_id}` : "-"}
                                    </td>
                                    <td className="px-3 py-2 text-slate-300">
                                        {e.user_id ? `#${e.user_id}` : "-"}
                                    </td>
                                    <td className="px-3 py-2 text-slate-400">
                                        {e.reference_type ? `${e.reference_type}:${e.reference_id}` : "-"}
                                    </td>
                                    <td className="px-3 py-2 text-slate-400">
                                        {e.created_at ? new Date(e.created_at).toLocaleString() : "-"}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {results && (
                <div className="mt-4 text-sm text-slate-400">
                    Showing {results.items.length} of {results.total} entries
                </div>
            )}
        </div>
    );
}

function TypeBadge({ type }: { type: string }) {
    const colors: Record<string, string> = {
        payment_in: "bg-blue-600 text-blue-100",
        payout: "bg-green-600 text-green-100",
        refund: "bg-orange-600 text-orange-100",
        fee: "bg-purple-600 text-purple-100",
        adjustment: "bg-yellow-600 text-yellow-100",
    };

    return (
        <span className={`px-2 py-1 text-xs font-medium rounded ${colors[type] || "bg-slate-600 text-slate-200"}`}>
            {type.replace("_", " ")}
        </span>
    );
}
