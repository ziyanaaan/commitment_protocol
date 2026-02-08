"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getCurrentUser, logout } from "@/lib/auth";
import type { UserProfile } from "@/lib/auth";

const navItems = [
    { href: "/admin", label: "Overview", icon: "📊" },
    { href: "/admin/commitments", label: "Commitments", icon: "📋" },
    { href: "/admin/payouts", label: "Payouts", icon: "💸" },
    { href: "/admin/refunds", label: "Refunds", icon: "↩️" },
    { href: "/admin/ledger", label: "Ledger", icon: "📒" },
    { href: "/admin/failures", label: "Failures", icon: "⚠️" },
    { href: "/admin/settings", label: "Settings", icon: "⚙️" },
    { href: "/admin/audit", label: "Audit Logs", icon: "📜" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [user, setUser] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function checkAuth() {
            const currentUser = await getCurrentUser();

            if (!currentUser) {
                router.push("/login");
                return;
            }

            if (currentUser.role !== "admin") {
                // Not admin - redirect to appropriate dashboard
                if (currentUser.role === "freelancer") {
                    router.push("/dashboard/freelancer");
                } else {
                    router.push("/dashboard/client");
                }
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
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-slate-400">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-900 flex">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
                {/* Logo */}
                <div className="p-4 border-b border-slate-700">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                            P
                        </div>
                        <span className="text-lg font-bold text-white">Admin Panel</span>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4">
                    <ul className="space-y-1">
                        {navItems.map((item) => {
                            const isActive = pathname === item.href ||
                                (item.href !== "/admin" && pathname.startsWith(item.href));
                            return (
                                <li key={item.href}>
                                    <Link
                                        href={item.href}
                                        className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                                ? "bg-blue-600 text-white"
                                                : "text-slate-300 hover:bg-slate-700 hover:text-white"
                                            }`}
                                    >
                                        <span>{item.icon}</span>
                                        {item.label}
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </nav>

                {/* User */}
                <div className="p-4 border-t border-slate-700">
                    <div className="text-sm text-slate-400 mb-2">{user?.email}</div>
                    <button
                        onClick={handleLogout}
                        className="w-full px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-700 rounded-lg transition-colors text-left"
                    >
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                {children}
            </main>
        </div>
    );
}
