"use client";

import Link from "next/link";

export default function ForgotPasswordPage() {
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
                                href="/login"
                                className="px-4 py-2 text-sm font-medium text-[#5C4033] hover:text-[#997E67] transition-colors"
                            >
                                Sign In
                            </Link>
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

            {/* Content */}
            <section className="max-w-md mx-auto px-4 py-16">
                <div className="bg-white rounded-2xl shadow-xl border border-[#CCBEB1]/40 p-8">
                    <div className="text-center">
                        <div className="w-16 h-16 mx-auto mb-4 bg-[#FFDBBB]/30 rounded-full flex items-center justify-center border border-[#FFDBBB]">
                            <svg className="w-8 h-8 text-[#997E67]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <h1 className="text-2xl font-serif font-bold text-[#5C4033] mb-4">Password Recovery</h1>
                        <p className="text-[#8A796E] mb-6">
                            Password recovery is coming soon. For now, please contact support to reset your password.
                        </p>
                        <div className="bg-[#F9F7F5] rounded-xl p-4 mb-6 border border-[#CCBEB1]/40">
                            <p className="text-sm text-[#8A796E] mb-2">Contact Support</p>
                            <p className="text-[#997E67] font-medium">support@pledgos.com</p>
                        </div>
                        <Link
                            href="/login"
                            className="inline-block w-full py-3 px-4 bg-[#997E67] text-white font-medium rounded-xl hover:bg-[#856b56] shadow-lg transition-all duration-200"
                        >
                            Back to Sign In
                        </Link>
                    </div>
                </div>
            </section>
        </main>
    );
}
