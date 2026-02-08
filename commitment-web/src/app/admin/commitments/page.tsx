"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type Commitment = {
    id: number;
    title: string;
    status: string;
    amount: number;
    deadline: string | null;
    created_at: string | null;
};

type SearchResult = {
    items: Commitment[];
    total: number;
    limit: number;
    offset: number;
};

export default function AdminCommitmentsPage() {
    const router = useRouter();
    const [results, setResults] = useState<SearchResult | null>(null);
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    async function loadCommitments(query?: string, status?: string) {
        setLoading(true);
        setError(null);
        try {
            let url = "/admin/commitments/search?limit=50";
            if (query) url += `&q=${encodeURIComponent(query)}`;
            if (status) url += `&status=${status}`;
            const data = await api<SearchResult>(url);
            setResults(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadCommitments();
    }, []);

    function handleSearch(e: React.FormEvent) {
        e.preventDefault();
        loadCommitments(search, statusFilter);
    }

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Commitment Search</h1>
                <p className="text-slate-400">Search and view commitment financial details</p>
            </div>

            {/* Search */}
            <form onSubmit={handleSearch} className="mb-6 flex gap-4">
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search by ID or title..."
                    className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">All Statuses</option>
                    <option value="draft">Draft</option>
                    <option value="paid">Paid</option>
                    <option value="locked">Locked</option>
                    <option value="delivered">Delivered</option>
                    <option value="settled">Settled</option>
                    <option value="expired">Expired</option>
                </select>
                <button
                    type="submit"
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    Search
                </button>
            </form>

            {error && (
                <div className="mb-6 bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            {/* Results Table */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="text-left text-sm text-slate-400 bg-slate-700/50">
                            <th className="px-4 py-3">ID</th>
                            <th className="px-4 py-3">Title</th>
                            <th className="px-4 py-3">Status</th>
                            <th className="px-4 py-3 text-right">Amount</th>
                            <th className="px-4 py-3">Deadline</th>
                            <th className="px-4 py-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr>
                                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                                    Loading...
                                </td>
                            </tr>
                        ) : results?.items.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                                    No commitments found
                                </td>
                            </tr>
                        ) : (
                            results?.items.map((c) => (
                                <tr key={c.id} className="border-t border-slate-700 hover:bg-slate-700/30">
                                    <td className="px-4 py-3 text-white font-mono">#{c.id}</td>
                                    <td className="px-4 py-3 text-white">{c.title}</td>
                                    <td className="px-4 py-3">
                                        <StatusBadge status={c.status} />
                                    </td>
                                    <td className="px-4 py-3 text-right text-white">
                                        ₹{c.amount.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 text-slate-300">
                                        {c.deadline ? new Date(c.deadline).toLocaleString() : "-"}
                                    </td>
                                    <td className="px-4 py-3">
                                        <button
                                            onClick={() => router.push(`/admin/commitments/${c.id}`)}
                                            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                                        >
                                            View Financial
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
                    Showing {results.items.length} of {results.total} commitments
                </div>
            )}
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
        <span className={`px-2 py-1 text-xs font-medium rounded ${colors[status] || "bg-slate-600 text-slate-200"}`}>
            {status}
        </span>
    );
}
