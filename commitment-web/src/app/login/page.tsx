"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, getCurrentUser } from "@/lib/auth";
import { getDashboardPath } from "@/lib/roles";
import type { Role } from "@/lib/roles";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            await login({ email, password });

            // Fetch user profile to get role
            const user = await getCurrentUser();
            if (!user) {
                throw new Error("Failed to get user profile");
            }

            // Redirect based on role
            const dashboardPath = getDashboardPath(user.role as Role);
            router.push(dashboardPath);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
        } finally {
            setIsLoading(false);
        }
    };

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
                            <Link
                                href="/signup"
                                className="px-5 py-2 text-sm font-medium bg-[#997E67] text-white hover:bg-[#856b56] shadow-md rounded-lg transition-colors"
                            >
                                Sign Up
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Login Form */}
            <section className="max-w-md mx-auto px-4 py-16">
                <div className="bg-white rounded-2xl shadow-xl border border-[#CCBEB1]/40 p-8">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <div className="w-16 h-16 mx-auto mb-4 bg-[#FFDBBB]/30 rounded-2xl flex items-center justify-center shadow-lg border border-[#FFDBBB]">
                            <svg className="w-8 h-8 text-[#997E67]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-serif font-bold text-[#5C4033] mb-2">Welcome Back</h1>
                        <p className="text-[#8A796E]">Sign in to your account</p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Email */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Email Address
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                autoComplete="email"
                                className="w-full px-4 py-3 bg-white border border-[#CCBEB1] rounded-xl text-[#5C4033] placeholder-[#CCBEB1] focus:outline-none focus:ring-2 focus:ring-[#997E67] focus:border-transparent transition-all"
                                placeholder="you@example.com"
                            />
                        </div>

                        {/* Password */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label htmlFor="password" className="block text-sm font-medium text-[#5C4033]">
                                    Password
                                </label>
                                <Link href="/forgot-password" className="text-sm text-[#997E67] hover:text-[#856b56]">
                                    Forgot password?
                                </Link>
                            </div>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                autoComplete="current-password"
                                className="w-full px-4 py-3 bg-white border border-[#CCBEB1] rounded-xl text-[#5C4033] placeholder-[#CCBEB1] focus:outline-none focus:ring-2 focus:ring-[#997E67] focus:border-transparent transition-all"
                                placeholder="••••••••"
                            />
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
                                <p className="text-sm text-red-600">{error}</p>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3 px-4 bg-[#997E67] text-white font-medium rounded-xl hover:bg-[#856b56] focus:outline-none focus:ring-2 focus:ring-[#997E67] focus:ring-offset-2 shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <span className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                    Signing in...
                                </span>
                            ) : (
                                "Sign In"
                            )}
                        </button>
                    </form>

                    {/* Signup Link */}
                    <div className="mt-6 text-center">
                        <p className="text-[#8A796E]">
                            Don&apos;t have an account?{" "}
                            <Link href="/signup" className="text-[#997E67] hover:text-[#856b56] font-medium">
                                Sign up
                            </Link>
                        </p>
                    </div>
                </div>

                {/* Security Notice */}
                <div className="mt-6 text-center">
                    <p className="text-xs text-[#CCBEB1]">
                        <svg className="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                        Secured with end-to-end encryption
                    </p>
                </div>
            </section>
        </main>
    );
}
