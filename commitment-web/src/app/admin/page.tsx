"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Overview = {
    total_captured: number;
    total_payouts: number;
    total_refunds: number;
    held_funds: number;
    available_balance: number;
    todays_volume: number;
    pending_settlements: number;
};

type Health = {
    status: "GREEN" | "ORANGE" | "RED";
    message: string;
    expected_balance: number;
    ledger_balance: number;
    drift: number;
    total_captured: number;
    total_payouts: number;
    total_refunds: number;
};

type Stats = {
    commitment_counts: Record<string, number>;
    user_counts: {
        clients: number;
        freelancers: number;
        admins: number;
    };
    total_commitments: number;
    total_users: number;
};

export default function AdminOverviewPage() {
    const [overview, setOverview] = useState<Overview | null>(null);
    const [health, setHealth] = useState<Health | null>(null);
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function load() {
            try {
                const [overviewData, healthData, statsData] = await Promise.all([
                    api<Overview>("/admin/overview"),
                    api<Health>("/admin/health"),
                    api<Stats>("/admin/stats"),
                ]);
                setOverview(overviewData);
                setHealth(healthData);
                setStats(statsData);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load data");
            } finally {
                setLoading(false);
            }
        }
        load();
    }, []);

    if (loading) {
        return (
            <div className="p-8">
                <div className="flex items-center justify-center py-16">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8">
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-white">Financial Overview</h1>
                <p className="text-slate-400">Platform financial health and metrics</p>
            </div>

            {/* Health Status */}
            {health && (
                <div className={`mb-8 p-4 rounded-lg border ${health.status === "GREEN"
                        ? "bg-green-900/30 border-green-700"
                        : health.status === "ORANGE"
                            ? "bg-orange-900/30 border-orange-700"
                            : "bg-red-900/30 border-red-700"
                    }`}>
                    <div className="flex items-center gap-3">
                        <div className={`w-4 h-4 rounded-full ${health.status === "GREEN"
                                ? "bg-green-500"
                                : health.status === "ORANGE"
                                    ? "bg-orange-500"
                                    : "bg-red-500"
                            }`}></div>
                        <div>
                            <p className={`font-medium ${health.status === "GREEN"
                                    ? "text-green-400"
                                    : health.status === "ORANGE"
                                        ? "text-orange-400"
                                        : "text-red-400"
                                }`}>
                                Platform Health: {health.status}
                            </p>
                            <p className="text-sm text-slate-400">{health.message}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Financial Metrics */}
            {overview && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <MetricCard
                        label="Total Captured"
                        value={`₹${overview.total_captured.toLocaleString()}`}
                        color="blue"
                    />
                    <MetricCard
                        label="Total Payouts"
                        value={`₹${overview.total_payouts.toLocaleString()}`}
                        color="green"
                    />
                    <MetricCard
                        label="Total Refunds"
                        value={`₹${overview.total_refunds.toLocaleString()}`}
                        color="orange"
                    />
                    <MetricCard
                        label="Available Balance"
                        value={`₹${overview.available_balance.toLocaleString()}`}
                        color="purple"
                    />
                    <MetricCard
                        label="Held Funds"
                        value={`₹${overview.held_funds.toLocaleString()}`}
                        color="yellow"
                    />
                    <MetricCard
                        label="Today's Volume"
                        value={`₹${overview.todays_volume.toLocaleString()}`}
                        color="cyan"
                    />
                    <MetricCard
                        label="Pending Settlements"
                        value={overview.pending_settlements.toString()}
                        color="pink"
                    />
                </div>
            )}

            {/* Stats */}
            {stats && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Commitment Counts */}
                    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                        <h2 className="text-lg font-semibold text-white mb-4">Commitments by Status</h2>
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-slate-400 border-b border-slate-700">
                                    <th className="pb-2">Status</th>
                                    <th className="pb-2 text-right">Count</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(stats.commitment_counts).map(([status, count]) => (
                                    <tr key={status} className="border-b border-slate-700/50">
                                        <td className="py-2 text-white capitalize">{status}</td>
                                        <td className="py-2 text-right text-slate-300">{count}</td>
                                    </tr>
                                ))}
                                <tr className="font-semibold">
                                    <td className="pt-2 text-white">Total</td>
                                    <td className="pt-2 text-right text-white">{stats.total_commitments}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    {/* User Counts */}
                    <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
                        <h2 className="text-lg font-semibold text-white mb-4">Users by Role</h2>
                        <table className="w-full">
                            <thead>
                                <tr className="text-left text-sm text-slate-400 border-b border-slate-700">
                                    <th className="pb-2">Role</th>
                                    <th className="pb-2 text-right">Count</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr className="border-b border-slate-700/50">
                                    <td className="py-2 text-white">Clients</td>
                                    <td className="py-2 text-right text-slate-300">{stats.user_counts.clients}</td>
                                </tr>
                                <tr className="border-b border-slate-700/50">
                                    <td className="py-2 text-white">Freelancers</td>
                                    <td className="py-2 text-right text-slate-300">{stats.user_counts.freelancers}</td>
                                </tr>
                                <tr className="border-b border-slate-700/50">
                                    <td className="py-2 text-white">Admins</td>
                                    <td className="py-2 text-right text-slate-300">{stats.user_counts.admins}</td>
                                </tr>
                                <tr className="font-semibold">
                                    <td className="pt-2 text-white">Total</td>
                                    <td className="pt-2 text-right text-white">{stats.total_users}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
    const colorClasses: Record<string, string> = {
        blue: "bg-blue-900/30 border-blue-700 text-blue-400",
        green: "bg-green-900/30 border-green-700 text-green-400",
        orange: "bg-orange-900/30 border-orange-700 text-orange-400",
        purple: "bg-purple-900/30 border-purple-700 text-purple-400",
        yellow: "bg-yellow-900/30 border-yellow-700 text-yellow-400",
        cyan: "bg-cyan-900/30 border-cyan-700 text-cyan-400",
        pink: "bg-pink-900/30 border-pink-700 text-pink-400",
    };

    return (
        <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
            <p className="text-sm text-slate-400 mb-1">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
        </div>
    );
}
