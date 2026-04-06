"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getCurrentUser, logout } from "@/lib/auth";
import type { UserProfile } from "@/lib/auth";

export default function FreelancerDashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const [user, setUser] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function checkAuth() {
            const currentUser = await getCurrentUser();

            if (!currentUser) {
                // Not authenticated
                router.push("/login");
                return;
            }

            if (currentUser.role !== "freelancer") {
                // Wrong role - redirect to correct dashboard
                router.push("/dashboard/client");
                return;
            }

            setUser(currentUser);
            setLoading(false);
        }

        checkAuth();
    }, [router]);

    const handleLogout = async () => {
        await logout();
        router.push("/login");
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#F9F7F5] flex items-center justify-center">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-[#997E67] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-[#8A796E]">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#F9F7F5]">
            {/* Navigation */}
            <nav className="bg-white border-b border-[#CCBEB1]/30 sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        <div className="flex items-center gap-8">
                            <Link href="/dashboard/freelancer" className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-lg bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-sm">
                                    P
                                </div>
                                <span className="text-lg font-serif font-bold text-[#5C4033]">
                                    Pledgos
                                </span>
                            </Link>
                            <div className="hidden md:flex items-center gap-6">
                                <Link
                                    href="/dashboard/freelancer"
                                    className="text-sm font-medium text-[#5C4033] hover:text-[#997E67] transition-colors"
                                >
                                    Dashboard
                                </Link>
                                <Link
                                    href="/dashboard/freelancer/commitments"
                                    className="text-sm font-medium text-[#8A796E] hover:text-[#997E67] transition-colors"
                                >
                                    Commitments
                                </Link>
                            </div>
                        </div>
                        <div className="flex items-center gap-4">
                            <Link href="/profile" className="text-right hidden sm:block hover:opacity-80 transition-opacity">
                                <p className="text-sm font-medium text-[#5C4033]">{user?.email}</p>
                                <p className="text-xs text-[#8A796E] uppercase">Freelancer</p>
                            </Link>
                            <button
                                onClick={handleLogout}
                                className="px-4 py-2 text-sm font-medium text-[#8A796E] hover:text-[#5C4033] transition-colors"
                            >
                                Sign Out
                            </button>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Content */}
            <main>{children}</main>
        </div>
    );
}
