"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type KillSwitches = {
    payouts_paused: boolean;
    refunds_paused: boolean;
    all_transfers_paused: boolean;
};

export default function AdminSettingsPage() {
    const [switches, setSwitches] = useState<KillSwitches | null>(null);
    const [loading, setLoading] = useState(true);
    const [updating, setUpdating] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function loadSwitches() {
        try {
            const data = await api<KillSwitches>("/admin/settings/kill-switch");
            setSwitches(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadSwitches();
    }, []);

    async function toggleSwitch(key: keyof KillSwitches, value: boolean) {
        setUpdating(key);
        setError(null);
        try {
            await api(`/admin/settings/kill-switch?key=${key}&value=${value}`, {
                method: "POST",
            });
            setSwitches((prev) => prev ? { ...prev, [key]: value } : null);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update");
        } finally {
            setUpdating(null);
        }
    }

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
                <h1 className="text-2xl font-bold text-white">System Settings</h1>
                <p className="text-slate-400">Kill switches and platform controls</p>
            </div>

            {error && (
                <div className="mb-6 bg-red-900/30 border border-red-700 rounded-lg p-4">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            {/* Warning */}
            <div className="mb-6 bg-yellow-900/30 border border-yellow-700 rounded-lg p-4">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">⚠️</span>
                    <div>
                        <p className="text-yellow-400 font-medium">Critical Controls</p>
                        <p className="text-sm text-slate-400">
                            These switches control live financial operations. Use with caution.
                        </p>
                    </div>
                </div>
            </div>

            {/* Kill Switches */}
            <div className="space-y-4">
                <KillSwitchCard
                    title="Pause All Transfers"
                    description="Emergency stop for all money movement (payouts + refunds)"
                    enabled={switches?.all_transfers_paused || false}
                    loading={updating === "all_transfers_paused"}
                    onToggle={(value) => toggleSwitch("all_transfers_paused", value)}
                    severity="critical"
                />
                <KillSwitchCard
                    title="Pause Payouts"
                    description="Stop all freelancer payouts while allowing refunds"
                    enabled={switches?.payouts_paused || false}
                    loading={updating === "payouts_paused"}
                    onToggle={(value) => toggleSwitch("payouts_paused", value)}
                    severity="warning"
                />
                <KillSwitchCard
                    title="Pause Refunds"
                    description="Stop all client refunds while allowing payouts"
                    enabled={switches?.refunds_paused || false}
                    loading={updating === "refunds_paused"}
                    onToggle={(value) => toggleSwitch("refunds_paused", value)}
                    severity="warning"
                />
            </div>

            {/* Note */}
            <div className="mt-8 bg-slate-800 border border-slate-700 rounded-lg p-4">
                <p className="text-slate-400 text-sm">
                    <strong className="text-white">Note:</strong> All kill switch changes are logged in the audit log
                    with admin ID, IP address, and timestamp.
                </p>
            </div>
        </div>
    );
}

function KillSwitchCard({
    title,
    description,
    enabled,
    loading,
    onToggle,
    severity,
}: {
    title: string;
    description: string;
    enabled: boolean;
    loading: boolean;
    onToggle: (value: boolean) => void;
    severity: "critical" | "warning";
}) {
    const borderColor = enabled
        ? severity === "critical"
            ? "border-red-600"
            : "border-orange-600"
        : "border-slate-700";

    return (
        <div className={`bg-slate-800 rounded-lg border ${borderColor} p-6`}>
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-white font-medium text-lg">{title}</h3>
                    <p className="text-sm text-slate-400 mt-1">{description}</p>
                </div>
                <button
                    onClick={() => onToggle(!enabled)}
                    disabled={loading}
                    className={`relative w-14 h-7 rounded-full transition-colors ${enabled ? "bg-red-600" : "bg-slate-600"
                        } ${loading ? "opacity-50" : ""}`}
                >
                    <div
                        className={`absolute top-1 w-5 h-5 rounded-full bg-white transition-transform ${enabled ? "left-8" : "left-1"
                            }`}
                    ></div>
                </button>
            </div>
            {enabled && (
                <div className={`mt-4 px-3 py-2 rounded ${severity === "critical" ? "bg-red-900/50" : "bg-orange-900/50"
                    }`}>
                    <p className={`text-sm font-medium ${severity === "critical" ? "text-red-400" : "text-orange-400"
                        }`}>
                        ⚠️ {severity === "critical" ? "CRITICAL" : "WARNING"}: This switch is currently ACTIVE
                    </p>
                </div>
            )}
        </div>
    );
}
