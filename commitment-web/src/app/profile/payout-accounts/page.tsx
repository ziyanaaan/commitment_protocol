"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { getCurrentUser, UserProfile } from "@/lib/auth";

type Beneficiary = {
    id: string;
    account_type: string;
    display_name: string;
    is_primary: boolean;
    is_active: boolean;
    created_at: string;
};

type PayoutReadiness = {
    has_beneficiary: boolean;
    has_primary: boolean;
    is_active: boolean;
    ready: boolean;
    message: string;
};

export default function PayoutAccountsPage() {
    const router = useRouter();
    const [user, setUser] = useState<UserProfile | null>(null);
    const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
    const [readiness, setReadiness] = useState<PayoutReadiness | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    // Add beneficiary form
    const [showAddForm, setShowAddForm] = useState(false);
    const [accountType, setAccountType] = useState("bank_account");
    const [displayName, setDisplayName] = useState("");

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        try {
            setIsLoading(true);
            const userData = await getCurrentUser();
            if (!userData) {
                router.push("/login");
                return;
            }
            setUser(userData);

            // Load beneficiaries
            const data = await api<{ beneficiaries: Beneficiary[]; payout_ready: boolean; message?: string }>("/beneficiaries");
            setBeneficiaries(data.beneficiaries);

            // Load readiness status
            const status = await api<PayoutReadiness>("/beneficiaries/status");
            setReadiness(status);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load data");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleAddBeneficiary(e: React.FormEvent) {
        e.preventDefault();
        setActionLoading("add");
        setError(null);
        setSuccess(null);

        try {
            await api("/beneficiaries", {
                method: "POST",
                body: JSON.stringify({
                    account_type: accountType,
                    display_name: displayName,
                }),
            });

            setSuccess("Payout account added successfully.");
            setShowAddForm(false);
            setDisplayName("");
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to add account");
        } finally {
            setActionLoading(null);
        }
    }

    async function handleSetPrimary(id: string) {
        setActionLoading(`primary-${id}`);
        setError(null);
        setSuccess(null);

        try {
            await api(`/beneficiaries/${id}/primary`, { method: "PUT" });
            setSuccess("Primary account updated.");
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update");
        } finally {
            setActionLoading(null);
        }
    }

    async function handleDisable(id: string) {
        if (!confirm("Are you sure you want to disable this account?")) return;

        setActionLoading(`disable-${id}`);
        setError(null);
        setSuccess(null);

        try {
            await api(`/beneficiaries/${id}/disable`, { method: "PUT" });
            setSuccess("Account disabled.");
            await loadData();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to disable");
        } finally {
            setActionLoading(null);
        }
    }

    const getAccountTypeLabel = (type: string) => {
        switch (type) {
            case "bank_account":
                return "Bank Account";
            case "vpa":
                return "UPI";
            case "wallet":
                return "Wallet";
            default:
                return type;
        }
    };

    if (isLoading) {
        return (
            <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">
                <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
                    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex justify-between h-20">
                            <div className="flex items-center gap-10">
                                <Link href="/" className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-[#997E67]/20">
                                        P
                                    </div>
                                    <span className="text-2xl font-serif font-bold tracking-tight text-[#5C4033]">
                                        PLEDGOS
                                    </span>
                                </Link>
                            </div>
                        </div>
                    </div>
                </nav>
                <div className="flex items-center justify-center py-32">
                    <div className="text-center">
                        <div className="w-12 h-12 mx-auto mb-4 border-4 border-[#CCBEB1] border-t-[#997E67] rounded-full animate-spin" />
                        <p className="text-[#8A796E]">Loading payout accounts...</p>
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">
            {/* Navigation */}
            <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-20">
                        <div className="flex items-center gap-10">
                            <Link href="/" className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-[#997E67]/20">
                                    P
                                </div>
                                <span className="text-2xl font-serif font-bold tracking-tight text-[#5C4033]">
                                    PLEDGOS
                                </span>
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            <section className="max-w-2xl mx-auto px-4 py-12">
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-sm text-[#8A796E] mb-6">
                    <Link href="/profile" className="hover:text-[#5C4033]">Profile</Link>
                    <span>→</span>
                    <span className="text-[#5C4033]">Payout Accounts</span>
                </div>

                <h1 className="text-3xl font-serif font-bold mb-2">Payout Accounts</h1>
                <p className="text-[#8A796E] mb-8">
                    Manage your payout accounts to receive funds from completed commitments.
                </p>

                {/* Alerts */}
                {error && (
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl text-green-700">
                        {success}
                    </div>
                )}

                {/* Readiness Status */}
                {readiness && (
                    <div className={`mb-8 p-6 rounded-xl border ${readiness.ready
                        ? "bg-green-50 border-green-200"
                        : "bg-amber-50 border-amber-200"
                        }`}>
                        <div className="flex items-center gap-3 mb-4">
                            {readiness.ready ? (
                                <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                            ) : (
                                <svg className="w-6 h-6 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                            )}
                            <h3 className={`font-semibold ${readiness.ready ? "text-green-700" : "text-amber-700"}`}>
                                {readiness.ready ? "Ready for Payouts" : "Setup Required"}
                            </h3>
                        </div>

                        <p className={readiness.ready ? "text-green-700" : "text-amber-700"}>
                            {readiness.message}
                        </p>

                        <div className="mt-4 flex gap-4 text-sm">
                            <span className={readiness.has_beneficiary ? "text-green-600" : "text-gray-400"}>
                                {readiness.has_beneficiary ? "✓" : "○"} Account Added
                            </span>
                            <span className={readiness.has_primary ? "text-green-600" : "text-gray-400"}>
                                {readiness.has_primary ? "✓" : "○"} Primary Set
                            </span>
                            <span className={readiness.is_active ? "text-green-600" : "text-gray-400"}>
                                {readiness.is_active ? "✓" : "○"} Active
                            </span>
                        </div>
                    </div>
                )}

                {/* Beneficiary List */}
                <div className="bg-white rounded-2xl shadow-xl border border-[#CCBEB1]/40 overflow-hidden mb-6">
                    <div className="p-6 border-b border-[#CCBEB1]/40 flex justify-between items-center">
                        <h2 className="text-lg font-semibold">Your Accounts</h2>
                        <button
                            onClick={() => setShowAddForm(true)}
                            className="px-4 py-2 bg-[#997E67] text-white rounded-lg hover:bg-[#856b56] transition-colors text-sm font-medium"
                        >
                            + Add Account
                        </button>
                    </div>

                    {beneficiaries.length === 0 ? (
                        <div className="p-8 text-center text-[#8A796E]">
                            <p>No payout accounts added yet.</p>
                            <p className="text-sm mt-2">Add an account to receive funds from your commitments.</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-[#CCBEB1]/40">
                            {beneficiaries.map((b) => (
                                <div key={b.id} className="p-6 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${b.is_active ? "bg-[#997E67]/10" : "bg-gray-100"
                                            }`}>
                                            {b.account_type === "bank_account" && (
                                                <svg className="w-5 h-5 text-[#997E67]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                                </svg>
                                            )}
                                            {b.account_type === "vpa" && (
                                                <span className="text-[#997E67] font-bold text-xs">UPI</span>
                                            )}
                                            {b.account_type === "wallet" && (
                                                <svg className="w-5 h-5 text-[#997E67]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                            )}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="font-medium">{b.display_name}</span>
                                                {b.is_primary && (
                                                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                                                        Primary
                                                    </span>
                                                )}
                                                {!b.is_active && (
                                                    <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                                                        Disabled
                                                    </span>
                                                )}
                                            </div>
                                            <span className="text-sm text-[#8A796E]">
                                                {getAccountTypeLabel(b.account_type)}
                                            </span>
                                        </div>
                                    </div>

                                    {b.is_active && (
                                        <div className="flex gap-2">
                                            {!b.is_primary && (
                                                <button
                                                    onClick={() => handleSetPrimary(b.id)}
                                                    disabled={actionLoading !== null}
                                                    className="px-3 py-1.5 text-sm border border-[#997E67] text-[#997E67] rounded-lg hover:bg-[#997E67]/10 disabled:opacity-50"
                                                >
                                                    {actionLoading === `primary-${b.id}` ? "..." : "Set Primary"}
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleDisable(b.id)}
                                                disabled={actionLoading !== null}
                                                className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50"
                                            >
                                                {actionLoading === `disable-${b.id}` ? "..." : "Disable"}
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Add Beneficiary Modal */}
                {showAddForm && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
                            <h2 className="text-xl font-serif font-bold mb-4">Add Payout Account</h2>

                            <form onSubmit={handleAddBeneficiary}>
                                <div className="mb-4">
                                    <label className="block text-sm font-medium text-[#5C4033] mb-2">
                                        Account Type
                                    </label>
                                    <select
                                        value={accountType}
                                        onChange={(e) => setAccountType(e.target.value)}
                                        className="w-full px-4 py-3 border border-[#CCBEB1] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#997E67]/50"
                                    >
                                        <option value="bank_account">Bank Account</option>
                                        <option value="vpa">UPI</option>
                                        <option value="wallet">Wallet</option>
                                    </select>
                                </div>

                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-[#5C4033] mb-2">
                                        Display Name
                                    </label>
                                    <input
                                        type="text"
                                        value={displayName}
                                        onChange={(e) => setDisplayName(e.target.value)}
                                        placeholder="e.g., HDFC ****1234 or yourname@upi"
                                        className="w-full px-4 py-3 border border-[#CCBEB1] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#997E67]/50"
                                        required
                                    />
                                    <p className="text-xs text-[#8A796E] mt-2">
                                        This is for your reference only. Actual account verification happens with the payment gateway.
                                    </p>
                                </div>

                                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl mb-6">
                                    <p className="text-sm text-amber-700">
                                        <strong>Note:</strong> Payouts can only be sent to verified accounts.
                                        Account verification is handled by our payment partner.
                                    </p>
                                </div>

                                <div className="flex gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setShowAddForm(false)}
                                        className="flex-1 px-4 py-3 border border-[#CCBEB1] text-[#5C4033] rounded-xl hover:bg-[#F9F7F5]"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={actionLoading === "add" || !displayName.trim()}
                                        className="flex-1 px-4 py-3 bg-[#997E67] text-white rounded-xl hover:bg-[#856b56] disabled:opacity-50"
                                    >
                                        {actionLoading === "add" ? "Adding..." : "Add Account"}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {/* Info */}
                <div className="text-center text-sm text-[#8A796E]">
                    <p>
                        Payouts are processed securely through our payment partner.
                        <br />
                        Funds typically arrive within 1-3 business days.
                    </p>
                </div>
            </section>
        </main>
    );
}
