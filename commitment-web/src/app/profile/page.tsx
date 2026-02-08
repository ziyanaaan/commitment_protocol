"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getCurrentUser, logout, UserProfile } from "@/lib/auth";

export default function ProfilePage() {
    const router = useRouter();
    const [user, setUser] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoggingOut, setIsLoggingOut] = useState(false);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const loadUser = async () => {
            try {
                const userData = await getCurrentUser();
                if (!userData) {
                    router.push("/login");
                    return;
                }
                setUser(userData);
            } catch {
                router.push("/login");
            } finally {
                setIsLoading(false);
            }
        };

        loadUser();
    }, [router]);

    const handleLogout = async () => {
        setIsLoggingOut(true);
        try {
            await logout();
            router.push("/login");
        } catch {
            // Still redirect on error
            router.push("/login");
        }
    };

    const copyToClipboard = () => {
        if (user) {
            navigator.clipboard.writeText(user.public_id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
        });
    };

    const getRoleColor = (role: string) => {
        switch (role) {
            case "client":
                return "bg-blue-100 text-blue-700 border-blue-200";
            case "freelancer":
                return "bg-green-100 text-green-700 border-green-200";
            case "admin":
                return "bg-red-100 text-red-700 border-red-200";
            default:
                return "bg-gray-100 text-gray-700 border-gray-200";
        }
    };

    const getRoleLabel = (role: string) => {
        return role.charAt(0).toUpperCase() + role.slice(1);
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
                        <p className="text-[#8A796E]">Loading profile...</p>
                    </div>
                </div>
            </main>
        );
    }

    if (!user) {
        return null;
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
                        <div className="flex items-center gap-4">
                            <button
                                onClick={handleLogout}
                                disabled={isLoggingOut}
                                className="px-4 py-2 text-sm font-medium text-[#997E67] hover:text-[#856b56] transition-colors disabled:opacity-50"
                            >
                                {isLoggingOut ? "Logging out..." : "Logout"}
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Profile Content */}
            <section className="max-w-2xl mx-auto px-4 py-12">
                {/* Back Link */}
                <Link href="/" className="inline-flex items-center text-[#8A796E] hover:text-[#5C4033] mb-6">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Back to Home
                </Link>

                {/* Profile Card */}
                <div className="bg-white rounded-2xl shadow-xl border border-[#CCBEB1]/40 overflow-hidden">
                    {/* Profile Header */}
                    <div className="bg-gradient-to-r from-[#997E67] to-[#856b56] p-8">
                        <div className="flex items-center">
                            <div className="w-20 h-20 bg-white/20 backdrop-blur rounded-2xl flex items-center justify-center shadow-lg mr-6">
                                <span className="text-3xl font-serif font-bold text-white">
                                    {user.email.charAt(0).toUpperCase()}
                                </span>
                            </div>
                            <div>
                                <h1 className="text-2xl font-serif font-bold text-white mb-2">{user.email}</h1>
                                <div className="flex items-center space-x-3">
                                    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getRoleColor(user.role)}`}>
                                        {getRoleLabel(user.role)}
                                    </span>
                                    {user.is_verified ? (
                                        <span className="flex items-center text-green-200 text-sm">
                                            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                            </svg>
                                            Verified
                                        </span>
                                    ) : (
                                        <span className="flex items-center text-yellow-200 text-sm">
                                            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                            </svg>
                                            Unverified
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Profile Details */}
                    <div className="p-8 space-y-6">
                        {/* Account ID - Prominently displayed */}
                        <div className="bg-[#F9F7F5] rounded-xl p-6 border border-[#CCBEB1]/40">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="text-sm font-medium text-[#8A796E] mb-1">Account ID</h3>
                                    <p className="text-xl font-mono text-[#997E67] tracking-wide">{user.public_id}</p>
                                </div>
                                <button
                                    onClick={copyToClipboard}
                                    className="p-2 text-[#8A796E] hover:text-[#5C4033] hover:bg-[#FFDBBB]/30 rounded-lg transition-all"
                                    title="Copy to clipboard"
                                >
                                    {copied ? (
                                        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                        </svg>
                                    )}
                                </button>
                            </div>
                            <p className="text-xs text-[#CCBEB1] mt-2">
                                This is your unique identifier. Share it with clients or freelancers to connect.
                            </p>
                        </div>

                        {/* Other Details Grid */}
                        <div className="grid grid-cols-2 gap-6">
                            <div>
                                <h3 className="text-sm font-medium text-[#8A796E] mb-1">Email</h3>
                                <p className="text-[#5C4033]">{user.email}</p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-[#8A796E] mb-1">Role</h3>
                                <p className="text-[#5C4033]">{getRoleLabel(user.role)}</p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-[#8A796E] mb-1">Account Status</h3>
                                <p className={user.is_active ? "text-green-600" : "text-red-600"}>
                                    {user.is_active ? "Active" : "Inactive"}
                                </p>
                            </div>
                            <div>
                                <h3 className="text-sm font-medium text-[#8A796E] mb-1">Member Since</h3>
                                <p className="text-[#5C4033]">{formatDate(user.created_at)}</p>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="pt-6 border-t border-[#CCBEB1]/40 flex flex-wrap gap-4">
                            <Link
                                href={user.role === "client" ? "/dashboard/client/commitments/new" : "/dashboard/freelancer/commitments"}
                                className="flex-1 text-center py-3 px-4 bg-[#997E67] text-white font-medium rounded-xl hover:bg-[#856b56] shadow-lg transition-all"
                            >
                                {user.role === "client" ? "Create Commitment" : "View Commitments"}
                            </Link>
                            {user.role === "freelancer" && (
                                <Link
                                    href="/profile/payout-accounts"
                                    className="flex-1 text-center py-3 px-4 border border-[#997E67] text-[#997E67] font-medium rounded-xl hover:bg-[#997E67]/10 transition-all"
                                >
                                    Payout Accounts
                                </Link>
                            )}
                            <button
                                className="px-6 py-3 border border-[#CCBEB1] text-[#5C4033] rounded-xl hover:bg-[#F9F7F5] transition-all"
                                onClick={() => alert("Settings coming soon!")}
                            >
                                Settings
                            </button>
                        </div>
                    </div>
                </div>

                {/* Security Info */}
                <div className="mt-6 text-center">
                    <p className="text-xs text-[#CCBEB1]">
                        <svg className="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Your session is secured with JWT tokens
                    </p>
                </div>
            </section>
        </main>
    );
}
