"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import Loading from "@/app/components/Loading";

type Settlement = {
  commitment_id: number;
  payout_amount: number;
  refund_amount: number;
  Delay_minutes: number;
  decay_applied: number;
  Settled_at: string;
};

type Commitment = {
  id: number;
  title: string;
  amount: number;
  deadline: string;
  decay_curve: string;
};

export default function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [settlement, setSettlement] = useState<Settlement | null>(null);
  const [commitment, setCommitment] = useState<Commitment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);

        // Load both settlement and commitment data
        const [s, c] = await Promise.all([
          api<Settlement>(`/settlements/by-commitment/${id}`),
          api<Commitment>(`/commitments/${id}`),
        ]);

        setSettlement(s);
        setCommitment(c);
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : "Failed to load settlement";
        setError(message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#F9F7F5] flex items-center justify-center">
        <Loading size="lg" text="Loading settlement..." />
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#F9F7F5] flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-serif font-bold text-[#5C4033] mb-2">Settlement Not Found</h2>
          <p className="text-[#8A796E] mb-6">{error}</p>
          <div className="flex flex-col gap-3">
            <button
              onClick={() => router.push(`/dashboard/client/commitments/${id}`)}
              className="px-6 py-3 bg-[#997E67] text-white rounded-xl hover:bg-[#856b56] transition-colors"
            >
              View Commitment
            </button>
            <button
              onClick={() => router.push("/")}
              className="px-6 py-3 text-[#997E67] hover:underline"
            >
              Go Home
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (!settlement || !commitment) return null;

  const payoutPercentage = (settlement.payout_amount / commitment.amount) * 100;
  const refundPercentage = (settlement.refund_amount / commitment.amount) * 100;
  const decayPercentage = (settlement.decay_applied * 100).toFixed(1);
  const settledDate = new Date(settlement.Settled_at);

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#F9F7F5] via-white to-[#F0EBE6] text-[#5C4033]">
      {/* Navigation */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-20">
            <div className="flex items-center gap-10">
              <button
                onClick={() => router.push("/")}
                className="flex items-center gap-3 hover:opacity-80 transition-opacity"
              >
                <div className="w-10 h-10 rounded-xl bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-[#997E67]/20">
                  P
                </div>
                <span className="text-2xl font-serif font-bold tracking-tight text-[#5C4033]">
                  PLEDGOS
                </span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <section className="max-w-3xl mx-auto px-4 py-12">
        {/* Success Banner */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-4">
            <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-4xl font-serif font-bold text-[#5C4033] mb-2">Settlement Complete</h1>
          <p className="text-[#8A796E]">
            Commitment #{commitment.id}: {commitment.title || "Untitled"}
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          {/* Summary Header */}
          <div className="bg-gradient-to-r from-green-600 to-emerald-600 p-6 text-white text-center">
            <p className="text-green-100 text-sm font-medium mb-1">Total Staked Amount</p>
            <p className="text-3xl font-bold">₹{commitment.amount.toLocaleString()}</p>
          </div>

          {/* Payout/Refund Split */}
          <div className="p-8">
            <div className="grid grid-cols-2 gap-6">
              {/* Payout */}
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 text-center border border-green-200">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100 mb-3">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm text-green-700 font-medium mb-1">Freelancer Payout</p>
                <p className="text-4xl font-bold text-green-600">₹{settlement.payout_amount.toLocaleString()}</p>
                <p className="text-xs text-green-600/70 mt-1">{payoutPercentage.toFixed(1)}% of stake</p>
              </div>

              {/* Refund */}
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 text-center border border-amber-200">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-amber-100 mb-3">
                  <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                  </svg>
                </div>
                <p className="text-sm text-amber-700 font-medium mb-1">Client Refund</p>
                <p className="text-4xl font-bold text-amber-600">₹{settlement.refund_amount.toLocaleString()}</p>
                <p className="text-xs text-amber-600/70 mt-1">{refundPercentage.toFixed(1)}% of stake</p>
              </div>
            </div>

            {/* Payout Bar Visualization */}
            <div className="mt-8">
              <div className="flex items-center justify-between text-sm text-[#8A796E] mb-2">
                <span>Fund Distribution</span>
                <span>100%</span>
              </div>
              <div className="h-4 bg-gray-200 rounded-full overflow-hidden flex">
                <div
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
                  style={{ width: `${payoutPercentage}%` }}
                />
                <div
                  className="h-full bg-gradient-to-r from-amber-400 to-orange-400"
                  style={{ width: `${refundPercentage}%` }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span className="text-green-600">Payout ({payoutPercentage.toFixed(1)}%)</span>
                <span className="text-amber-600">Refund ({refundPercentage.toFixed(1)}%)</span>
              </div>
            </div>
          </div>

          {/* Details */}
          <div className="px-8 pb-8">
            <div className="bg-[#F9F7F5] rounded-2xl p-6 space-y-4">
              <h3 className="font-serif font-bold text-lg text-[#5C4033] mb-4">Settlement Details</h3>

              <div className="flex justify-between py-2 border-b border-[#CCBEB1]/30">
                <span className="text-[#8A796E]">Delay</span>
                <span className="font-medium text-[#5C4033]">
                  {settlement.Delay_minutes > 0
                    ? `${settlement.Delay_minutes} minutes late`
                    : 'On time ✓'}
                </span>
              </div>

              <div className="flex justify-between py-2 border-b border-[#CCBEB1]/30">
                <span className="text-[#8A796E]">Decay Applied</span>
                <span className={`font-medium ${settlement.decay_applied > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {decayPercentage}%
                </span>
              </div>

              <div className="flex justify-between py-2 border-b border-[#CCBEB1]/30">
                <span className="text-[#8A796E]">Decay Curve</span>
                <span className="font-medium text-[#5C4033] capitalize">{commitment.decay_curve}</span>
              </div>

              <div className="flex justify-between py-2">
                <span className="text-[#8A796E]">Settled At</span>
                <span className="font-medium text-[#5C4033]">
                  {settledDate.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="px-8 pb-8">
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={() => router.push(`/dashboard/client/commitments/${id}`)}
                className="flex-1 py-4 px-6 rounded-2xl font-semibold text-[#5C4033] bg-[#FFDBBB] hover:bg-[#ffcfa6] transition-all flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                View Commitment
              </button>

              <button
                onClick={() => router.push("/dashboard/client/commitments/new")}
                className="flex-1 py-4 px-6 rounded-2xl font-semibold text-white bg-gradient-to-r from-[#997E67] to-[#5C4634] hover:opacity-90 transition-all flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Commitment
              </button>
            </div>
          </div>
        </div>

        {/* Back to Home */}
        <div className="text-center mt-8">
          <button
            onClick={() => router.push("/")}
            className="text-[#8A796E] hover:text-[#5C4033] hover:underline transition-colors"
          >
            ← Back to Home
          </button>
        </div>
      </section>
    </main>
  );
}
