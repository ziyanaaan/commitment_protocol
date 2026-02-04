"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function NewCommitmentPage() {
    const router = useRouter();
    const [clientId, setClientId] = useState(1);
    const [freelancerId, setFreelancerId] = useState(2);
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [amount, setAmount] = useState("");
    const [deadlineDate, setDeadlineDate] = useState("");
    const [deadlineTime, setDeadlineTime] = useState("");
    const [decayCurve, setDecayCurve] = useState("balanced");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Calculate minimum deadline (tomorrow)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const minDeadline = tomorrow.toISOString().split("T")[0];

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const result = await api<{ id: number }>("/commitments", {
                method: "POST",
                body: JSON.stringify({
                    client_id: clientId,
                    freelancer_id: freelancerId,
                    title,
                    description,
                    amount: parseInt(amount),
                    deadline: new Date(`${deadlineDate}T${deadlineTime}`).toISOString(),
                    decay_curve: decayCurve,
                }),
            });

            // Redirect to the new commitment
            router.push(`/dashboard/client/commitments/${result.id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create commitment");
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">
            {/* Top bar */}
            <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-4 h-20 flex items-center justify-between">
                    <h1 className="text-2xl font-serif font-bold">Create Commitment</h1>
                    <button
                        onClick={() => router.push("/")}
                        className="text-[#8A796E] hover:text-[#5C4033] transition-colors"
                    >
                        ← Back
                    </button>
                </div>
            </nav>

            {/* Card */}
            <section className="max-w-2xl mx-auto px-4 py-12">
                <div className="bg-white rounded-xl border border-[#CCBEB1]/30 p-6">
                    {/* Error */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                            <p className="text-red-600">{error}</p>
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Client ID */}
                        <div>
                            <label htmlFor="clientId" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Client ID
                            </label>
                            <input
                                id="clientId"
                                type="number"
                                value={clientId}
                                onChange={(e) => setClientId(Number(e.target.value))}
                                className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                            />
                        </div>

                        {/* Freelancer ID */}
                        <div>
                            <label htmlFor="freelancerId" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Freelancer ID
                            </label>
                            <input
                                id="freelancerId"
                                type="number"
                                value={freelancerId}
                                onChange={(e) => setFreelancerId(Number(e.target.value))}
                                className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                            />
                        </div>

                        {/* Title */}
                        <div>
                            <label htmlFor="title" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Title <span className="text-red-500">*</span>
                            </label>
                            <input
                                id="title"
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                placeholder="e.g., Build landing page"
                                className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                            />
                        </div>

                        {/* Description */}
                        <div>
                            <label htmlFor="description" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Description (optional)
                            </label>
                            <textarea
                                id="description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                rows={3}
                                placeholder="Describe the work to be done..."
                                className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033] resize-none"
                            />
                        </div>

                        {/* Amount */}
                        <div>
                            <label htmlFor="amount" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Amount (₹) <span className="text-red-500">*</span>
                            </label>
                            <input
                                id="amount"
                                type="number"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                required
                                min="100"
                                placeholder="5000"
                                className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                            />
                            <p className="text-xs text-[#8A796E] mt-1">Minimum ₹100</p>
                        </div>

                        {/* Deadline */}
                        <div>
                            <label className="block text-sm font-medium text-[#5C4033] mb-2">
                                Deadline <span className="text-red-500">*</span>
                            </label>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label htmlFor="deadlineDate" className="block text-xs text-[#8A796E] mb-1">Date</label>
                                    <input
                                        id="deadlineDate"
                                        type="date"
                                        value={deadlineDate}
                                        onChange={(e) => setDeadlineDate(e.target.value)}
                                        required
                                        min={minDeadline}
                                        className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                                    />
                                </div>
                                <div>
                                    <label htmlFor="deadlineTime" className="block text-xs text-[#8A796E] mb-1">Time</label>
                                    <input
                                        id="deadlineTime"
                                        type="time"
                                        value={deadlineTime}
                                        onChange={(e) => setDeadlineTime(e.target.value)}
                                        required
                                        className="w-full px-4 py-3 border border-[#CCBEB1] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#997E67] text-[#5C4033]"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Decay Curve */}
                        <div>
                            <label className="block text-sm font-medium text-[#5C4033] mb-2">
                                Decay Curve
                            </label>
                            <div className="grid grid-cols-3 gap-3">
                                {(["flexible", "balanced", "strict"] as const).map((curve) => (
                                    <button
                                        key={curve}
                                        type="button"
                                        onClick={() => setDecayCurve(curve)}
                                        className={`py-3 px-4 rounded-lg border-2 transition-all capitalize ${decayCurve === curve
                                            ? "border-[#997E67] bg-[#997E67]/10 text-[#5C4033]"
                                            : "border-[#CCBEB1] text-[#8A796E] hover:border-[#997E67]/50"
                                            }`}
                                    >
                                        {curve}
                                    </button>
                                ))}
                            </div>
                            <p className="text-xs text-[#8A796E] mt-2">
                                Determines how refund decreases after deadline passes.
                            </p>
                        </div>

                        {/* Submit */}
                        <div className="pt-4">
                            <button
                                type="submit"
                                disabled={loading || !title || !amount || !deadlineDate || !deadlineTime}
                                className="w-full py-4 px-4 bg-gradient-to-r from-[#997E67] to-[#5C4634] text-white font-semibold rounded-xl shadow-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {loading ? "Creating..." : "Create Commitment"}
                            </button>
                        </div>
                    </form>
                </div>
            </section>
        </main>
    );
}
