"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type AuditLog = {
    id: number;
    admin_user_id: number;
    action_type: string;
    target_type: string | null;
    target_id: number | null;
    details: Record<string, unknown> | null;
    ip_address: string | null;
    created_at: string | null;
};

type AuditResult = {
    items: AuditLog[];
    total: number;
    limit: number;
    offset: number;
};

export default function AdminAuditPage() {
    const [results, setResults] = useState<AuditResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionFilter, setActionFilter] = useState("");

    async function loadAudit() {
        setLoading(true);
        setError(null);
        try {
            let url = "/admin/audit-logs?limit=200";
            if (actionFilter) url += `&action_type=${actionFilter}`;
            const data = await api<AuditResult>(url);
            setResults(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadAudit();
    }, []);

    function handleFilter(e: React.FormEvent) {
        e.preventDefault();
        loadAudit();
    }

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Admin Audit Logs</h1>
                <p className="text-slate-400">Track all admin actions and changes</p>
            </div>

            {/* Filter */}
            <form onSubmit={handleFilter} className="mb-6 flex gap-4">
                <select
                    value={actionFilter}
                    onChange={(e) => setActionFilter(e.target.value)}
                    className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="">All Actions</option>
                    <option value="commitment_view">Commitment View</option>
                    <option value="kill_switch_toggle">Kill Switch Toggle</option>
                    <option value="payout_retry">Payout Retry</option>
                    <option value="refund_manual">Manual Refund</option>
                    <option value="setting_update">Setting Update</option>
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
                            <th className="px-4 py-3">ID</th>
                            <th className="px-4 py-3">Action</th>
                            <th className="px-4 py-3">Admin</th>
                            <th className="px-4 py-3">Target</th>
                            <th className="px-4 py-3">Details</th>
                            <th className="px-4 py-3">IP</th>
                            <th className="px-4 py-3">Time</th>
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
                                    No audit logs found
                                </td>
                            </tr>
                        ) : (
                            results?.items.map((log) => (
                                <tr key={log.id} className="border-t border-slate-700 hover:bg-slate-700/30">
                                    <td className="px-4 py-3 text-white font-mono">#{log.id}</td>
                                    <td className="px-4 py-3">
                                        <ActionBadge action={log.action_type} />
                                    </td>
                                    <td className="px-4 py-3 text-slate-300">User #{log.admin_user_id}</td>
                                    <td className="px-4 py-3 text-slate-400">
                                        {log.target_type ? `${log.target_type}:${log.target_id}` : "-"}
                                    </td>
                                    <td className="px-4 py-3 text-slate-400 text-xs max-w-xs truncate">
                                        {log.details ? JSON.stringify(log.details) : "-"}
                                    </td>
                                    <td className="px-4 py-3 text-slate-400 font-mono text-xs">
                                        {log.ip_address || "-"}
                                    </td>
                                    <td className="px-4 py-3 text-slate-400">
                                        {log.created_at ? new Date(log.created_at).toLocaleString() : "-"}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {results && (
                <div className="mt-4 text-sm text-slate-400">
                    Showing {results.items.length} of {results.total} logs
                </div>
            )}
        </div>
    );
}

function ActionBadge({ action }: { action: string }) {
    const colors: Record<string, string> = {
        commitment_view: "bg-blue-600 text-blue-100",
        kill_switch_toggle: "bg-red-600 text-red-100",
        payout_retry: "bg-orange-600 text-orange-100",
        refund_manual: "bg-yellow-600 text-yellow-100",
        setting_update: "bg-purple-600 text-purple-100",
        ledger_view: "bg-cyan-600 text-cyan-100",
    };

    return (
        <span className={`px-2 py-1 text-xs font-medium rounded ${colors[action] || "bg-slate-600 text-slate-200"}`}>
            {action.replace(/_/g, " ")}
        </span>
    );
}
