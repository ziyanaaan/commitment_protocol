"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { statusInfo } from "@/lib/status";

type Commitment = {
    id: number;
    status: string;
    amount: number;
    deadline: string;
    title: string;
    description: string;
    created_at: string;
};

export default function ClientCommitmentsPage() {
    const [commitments, setCommitments] = useState<Commitment[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function loadCommitments() {
            try {
                const data = await api<Commitment[]>("/commitments");
                setCommitments(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load commitments");
            } finally {
                setLoading(false);
            }
        }
        loadCommitments();
    }, []);

    if (loading) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-8">
                <div className="flex items-center justify-center py-16">
                    <div className="w-8 h-8 border-2 border-[#997E67] border-t-transparent rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-8">
                <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                    <p className="text-red-600">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto px-4 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-serif font-semibold text-[#5C4033]">
                        Your Commitments
                    </h1>
                    <p className="text-[#8A796E]">
                        {commitments.length} commitment{commitments.length !== 1 ? "s" : ""}
                    </p>
                </div>
                <Link
                    href="/dashboard/client/commitments/new"
                    className="px-4 py-2 bg-[#997E67] text-white font-medium rounded-lg hover:bg-[#856b56] transition-colors"
                >
                    Create New
                </Link>
            </div>

            {/* List */}
            {commitments.length === 0 ? (
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-12 text-center">
                    <p className="text-[#8A796E] mb-4">You haven't created any commitments yet.</p>
                    <Link
                        href="/dashboard/client/commitments/new"
                        className="px-4 py-2 bg-[#997E67] text-white font-medium rounded-lg hover:bg-[#856b56] transition-colors inline-block"
                    >
                        Create Your First Commitment
                    </Link>
                </div>
            ) : (
                <div className="space-y-4">
                    {commitments.map((commitment) => {
                        const status = statusInfo[commitment.status] || {
                            label: commitment.status,
                            color: "#6B7280",
                            bgColor: "#F3F4F6",
                        };
                        const deadline = new Date(commitment.deadline);
                        const isPast = new Date() > deadline;

                        return (
                            <Link
                                key={commitment.id}
                                href={`/dashboard/client/commitments/${commitment.id}`}
                                className="block bg-white rounded-xl border border-[#CCBEB1]/30 p-6 hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h2 className="font-semibold text-[#5C4033] truncate">
                                                {commitment.title || `Commitment #${commitment.id}`}
                                            </h2>
                                            <span
                                                className="px-2 py-1 text-xs font-semibold rounded-full"
                                                style={{ backgroundColor: status.bgColor, color: status.color }}
                                            >
                                                {status.label}
                                            </span>
                                        </div>
                                        {commitment.description && (
                                            <p className="text-sm text-[#8A796E] truncate mb-2">
                                                {commitment.description}
                                            </p>
                                        )}
                                        <div className="flex items-center gap-4 text-sm text-[#8A796E]">
                                            <span>₹{commitment.amount.toLocaleString()}</span>
                                            <span className={isPast ? "text-red-500" : ""}>
                                                Due {deadline.toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                    <svg className="w-5 h-5 text-[#CCBEB1] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </Link>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
