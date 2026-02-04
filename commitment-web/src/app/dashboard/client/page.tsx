"use client";

import Link from "next/link";

export default function ClientDashboardPage() {
    return (
        <div className="max-w-6xl mx-auto px-4 py-8">
            {/* Welcome Section */}
            <div className="mb-8">
                <h1 className="text-3xl font-serif font-semibold text-[#5C4033] mb-2">
                    Welcome back
                </h1>
                <p className="text-[#8A796E]">
                    Manage your commitments and track project progress.
                </p>
            </div>


            {/* Quick Actions */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
                <Link
                    href="/dashboard/client/commitments/new"
                    className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6 hover:shadow-md transition-shadow"
                >
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-lg bg-[#997E67] flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="font-semibold text-[#5C4033]">Create Commitment</h2>
                            <p className="text-sm text-[#8A796E]">Start a new project with accountability</p>
                        </div>
                    </div>
                </Link>

                <Link
                    href="/dashboard/client/commitments"
                    className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6 hover:shadow-md transition-shadow"
                >
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-lg bg-[#FFDBBB]/50 flex items-center justify-center">
                            <svg className="w-6 h-6 text-[#997E67]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="font-semibold text-[#5C4033]">View Commitments</h2>
                            <p className="text-sm text-[#8A796E]">See all your active and past projects</p>
                        </div>
                    </div>
                </Link>
            </div>

            {/* Quick Search */}
            <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6 mb-8">
                <h3 className="text-sm font-medium text-[#8A796E] mb-3">Find a Commitment</h3>
                <div className="flex gap-3">
                    <input
                        type="number"
                        placeholder="Enter Commitment ID"
                        id="commitmentIdSearch"
                        className="flex-1 px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                const input = e.target as HTMLInputElement;
                                if (input.value) {
                                    window.location.href = `/dashboard/client/commitments/${input.value}`;
                                }
                            }
                        }}
                    />
                    <button
                        onClick={() => {
                            const input = document.getElementById('commitmentIdSearch') as HTMLInputElement;
                            if (input?.value) {
                                window.location.href = `/dashboard/client/commitments/${input.value}`;
                            }
                        }}
                        className="px-6 py-3 bg-[#997E67] text-white font-medium rounded-lg hover:bg-[#856b56] transition-colors"
                    >
                        View
                    </button>
                </div>
            </div>


            {/* Info Cards */}
            <div className="grid md:grid-cols-3 gap-6">
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6">
                    <h3 className="text-sm font-medium text-[#8A796E] mb-1">How It Works</h3>
                    <p className="text-sm text-[#5C4033]">
                        Create a commitment, fund it, and the freelancer will lock and deliver the work.
                    </p>
                </div>
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6">
                    <h3 className="text-sm font-medium text-[#8A796E] mb-1">Your Funds</h3>
                    <p className="text-sm text-[#5C4033]">
                        Payments are held securely until work is verified and delivered.
                    </p>
                </div>
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6">
                    <h3 className="text-sm font-medium text-[#8A796E] mb-1">Settlement</h3>
                    <p className="text-sm text-[#5C4033]">
                        Funds are automatically distributed when work is delivered on time.
                    </p>
                </div>
            </div>
        </div>
    );
}
