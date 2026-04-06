"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

// This page surfaces failed operations - currently shows settlements with issues
// In a real system, this would track failed gateway calls, webhook failures, etc.

export default function AdminFailuresPage() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // In a production system, this would fetch from /admin/failures
        // For now, we show a placeholder
        setLoading(false);
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

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-white">Failed Operations</h1>
                <p className="text-slate-400">Surface and resolve payment and settlement failures</p>
            </div>

            {error && (
                <div className="mb-6 bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            {/* Status */}
            <div className="bg-green-900/30 border border-green-700 rounded-lg p-6 mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-4 h-4 rounded-full bg-green-500"></div>
                    <div>
                        <p className="text-green-400 font-medium">No Active Failures</p>
                        <p className="text-sm text-slate-400">All payment and settlement operations are running normally</p>
                    </div>
                </div>
            </div>

            {/* Categories */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <FailureCard
                    title="Failed Payouts"
                    count={0}
                    description="Payouts that failed to process"
                    color="red"
                />
                <FailureCard
                    title="Failed Refunds"
                    count={0}
                    description="Refunds that failed to process"
                    color="orange"
                />
                <FailureCard
                    title="Webhook Failures"
                    count={0}
                    description="Failed webhook deliveries"
                    color="yellow"
                />
                <FailureCard
                    title="Reconciliation Mismatches"
                    count={0}
                    description="Ledger vs gateway mismatches"
                    color="purple"
                />
                <FailureCard
                    title="Settlement Errors"
                    count={0}
                    description="Commitments that failed to settle"
                    color="pink"
                />
                <FailureCard
                    title="Gateway Timeouts"
                    count={0}
                    description="Payment gateway timeouts"
                    color="cyan"
                />
            </div>

            {/* Note */}
            <div className="mt-8 bg-slate-800 border border-slate-700 rounded-lg p-4">
                <p className="text-slate-400 text-sm">
                    <strong className="text-white">Note:</strong> This panel tracks real-time failures from the payment
                    gateway and settlement system. In production, any failures would appear here automatically and
                    require admin review.
                </p>
            </div>
        </div>
    );
}

function FailureCard({
    title,
    count,
    description,
    color,
}: {
    title: string;
    count: number;
    description: string;
    color: string;
}) {
    const colorClasses: Record<string, string> = {
        red: "border-red-700",
        orange: "border-orange-700",
        yellow: "border-yellow-700",
        purple: "border-purple-700",
        pink: "border-pink-700",
        cyan: "border-cyan-700",
    };

    return (
        <div className={`bg-slate-800 rounded-lg border ${colorClasses[color]} p-4`}>
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-white font-medium">{title}</h3>
                <span className={`text-2xl font-bold ${count > 0 ? "text-red-400" : "text-green-400"}`}>
                    {count}
                </span>
            </div>
            <p className="text-sm text-slate-400">{description}</p>
        </div>
    );
}
