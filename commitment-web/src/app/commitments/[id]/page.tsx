"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { actionsByStatus, statusInfo } from "@/lib/status";
import Loading from "@/app/components/Loading";
import DecayTooltip from "@/app/components/DecayTooltip";

// Module-level tracking to persist across React Strict Mode remounts
// This tracks which commitment+action combinations are currently in flight
const inflightActions = new Set<string>();

type Commitment = {
  id: number;
  status: string;
  amount: number;
  deadline: string;
  title: string;
  description: string;
  decay_curve: string;
  created_at: string;
};

type Payment = {
  status: string;
  order_id: string;
  payment_id: string | null;
  amount: number;
};

type Preview = {
  commitment_id: number;
  status: string;
  now: string;
  deadline: string;
  delay_minutes: number;
  expected_payout: number;
  expected_refund: number;
};

export default function CommitmentPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [commitment, setCommitment] = useState<Commitment | null>(null);
  const [payment, setPayment] = useState<Payment | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Ref for local component state
  const isMounted = useRef(true);

  // Cleanup on unmount
  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  // Re-fetch commitment data - always get fresh state from server
  const load = useCallback(async () => {
    // Prevent concurrent loads using module-level tracking
    const loadKey = `load-${id}`;
    if (inflightActions.has(loadKey)) return;
    inflightActions.add(loadKey);

    try {
      setLoading(true);
      setError(null);

      const c = await api<Commitment>(`/commitments/${id}`);
      if (!isMounted.current) return;
      setCommitment(c);

      // Try to load payment (may not exist)
      try {
        const p = await api<Payment>(`/payments/${id}`);
        if (isMounted.current) setPayment(p);
      } catch {
        if (isMounted.current) setPayment(null);
      }

      // Try to load preview (only for non-settled commitments)
      if (c.status !== "settled") {
        try {
          const pv = await api<Preview>(`/commitments/${id}/preview`);
          if (isMounted.current) setPreview(pv);
        } catch {
          if (isMounted.current) setPreview(null);
        }
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Failed to load commitment";
      if (isMounted.current) setError(message);
    } finally {
      if (isMounted.current) setLoading(false);
      inflightActions.delete(loadKey);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // SECURITY: Always re-fetch before action to ensure current state
  // Uses module-level Set to prevent double submissions (survives React remounts)
  async function performAction(actionName: string, path: string, method: string = "POST") {
    const actionKey = `${id}-${actionName}`;

    // Prevent double submissions
    if (inflightActions.has(actionKey)) {
      console.warn(`Action ${actionName} already in progress for commitment ${id}, ignoring duplicate call`);
      return;
    }
    inflightActions.add(actionKey);
    setActionLoading(actionName);
    setError(null);

    try {
      // CRITICAL: Re-fetch commitment to get latest state
      const freshCommitment = await api<Commitment>(`/commitments/${id}`);

      // Verify action is still allowed
      const allowed = actionsByStatus[freshCommitment.status] || [];
      if (!allowed.includes(actionName)) {
        // Status already changed - just reload to show current state
        console.log(`Action ${actionName} no longer allowed, status is ${freshCommitment.status}`);
        if (isMounted.current) await load();
        return;
      }

      // Perform the action
      await api(path, { method });

      // For deliver action, navigate to result page (since backend auto-settles)
      if (actionName === "deliver" && isMounted.current) {
        router.push(`/result/${id}`);
        return;
      }

      // Reload all data for other actions
      if (isMounted.current) await load();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Action failed";
      // If it's a 409 conflict, the action already completed - just reload
      if (message.includes("409") || message.toLowerCase().includes("already") || message.toLowerCase().includes("conflict")) {
        console.log(`Action ${actionName} got conflict, reloading`);
        if (isMounted.current) await load();
      } else if (isMounted.current) {
        setError(message);
      }
    } finally {
      if (isMounted.current) setActionLoading(null);
      inflightActions.delete(actionKey);
    }
  }

  // Payment with Razorpay
  async function handlePay() {
    if (!commitment) return;

    const actionKey = `${id}-fund`;

    // Prevent double submissions
    if (inflightActions.has(actionKey)) {
      console.warn("Payment already in progress, ignoring duplicate call");
      return;
    }
    inflightActions.add(actionKey);
    setActionLoading("fund");
    setError(null);

    try {
      // CRITICAL: Re-fetch to verify state
      const freshCommitment = await api<Commitment>(`/commitments/${id}`);
      if (freshCommitment.status !== "draft") {
        console.log("Cannot pay, status changed to", freshCommitment.status);
        if (isMounted.current) await load();
        return;
      }

      // Create Razorpay order
      const res = await api<{
        razorpay_key: string;
        amount: number;
        currency: string;
        order_id: string;
      }>(`/commitments/${id}/fund`, { method: "POST" });

      // Define Razorpay options
      const rzpOptions = {
        key: res.razorpay_key,
        amount: res.amount,
        currency: res.currency,
        order_id: res.order_id,
        name: "Commitment Protocol",
        description: `Commitment #${id}: ${commitment.title}`,
        handler: async function (response: {
          razorpay_order_id: string;
          razorpay_payment_id: string;
          razorpay_signature: string;
        }) {
          try {
            await api("/payments/verify", {
              method: "POST",
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            if (isMounted.current) await load();
          } catch (e: unknown) {
            const message = e instanceof Error ? e.message : "Payment verification failed";
            if (isMounted.current) setError(message);
          }
        },
      };

      // Open Razorpay checkout
      interface RazorpayInstance { open: () => void }
      interface RazorpayWindow { Razorpay: new (options: Record<string, unknown>) => RazorpayInstance }
      const rzp = new (window as unknown as RazorpayWindow).Razorpay(rzpOptions);
      rzp.open();
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Payment initiation failed";
      if (isMounted.current) setError(message);
    } finally {
      if (isMounted.current) setActionLoading(null);
      inflightActions.delete(actionKey);
    }
  }

  // Handle settle action (kept for backwards compatibility but shouldn't be called)
  async function handleSettle() {
    await performAction("settle", `/settlements/${id}/settle`, "POST");
  }

  // Rendering
  if (loading) {
    return (
      <main className="min-h-screen bg-[#F9F7F5] flex items-center justify-center">
        <Loading size="lg" text="Loading commitment..." />
      </main>
    );
  }

  if (error && !commitment) {
    return (
      <main className="min-h-screen bg-[#F9F7F5] flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-serif font-bold text-[#5C4033] mb-2">Error</h2>
          <p className="text-[#8A796E] mb-6">{error}</p>
          <button
            onClick={() => router.push("/")}
            className="px-6 py-3 bg-[#997E67] text-white rounded-xl hover:bg-[#856b56] transition-colors"
          >
            Go Home
          </button>
        </div>
      </main>
    );
  }

  if (!commitment) return null;

  const allowed = actionsByStatus[commitment.status] || [];
  const status = statusInfo[commitment.status] || { label: commitment.status, color: "#6B7280", bgColor: "#F3F4F6" };
  const deadlineDate = new Date(commitment.deadline);
  const isPastDeadline = new Date() > deadlineDate;

  return (
    <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">
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
            <div className="flex items-center gap-4">
              <button
                onClick={load}
                disabled={loading}
                className="p-2 rounded-lg hover:bg-[#F3F4F6] transition-colors"
                aria-label="Refresh"
              >
                <svg className={`w-5 h-5 text-[#8A796E] ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <section className="max-w-4xl mx-auto px-4 py-12">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
            <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-red-700 text-sm flex-1">{error}</p>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {/* Main Card */}
        <div className="bg-white rounded-3xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-[#997E67] to-[#5C4634] p-8 text-white">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-2">
                <p className="text-white/60 text-sm font-medium">Commitment #{commitment.id}</p>
                <h1 className="text-3xl font-serif font-bold">{commitment.title || "Untitled Commitment"}</h1>
                {commitment.description && (
                  <p className="text-white/80 max-w-xl">{commitment.description}</p>
                )}
              </div>
              <div
                className="px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wide"
                style={{ backgroundColor: status.bgColor, color: status.color }}
              >
                {status.label}
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Amount */}
            <div className="bg-[#F9F7F5] rounded-2xl p-6">
              <p className="text-sm text-[#8A796E] mb-1">Staked Amount</p>
              <p className="text-3xl font-bold text-[#5C4033]">₹{commitment.amount.toLocaleString()}</p>
            </div>

            {/* Deadline */}
            <div className={`rounded-2xl p-6 ${isPastDeadline ? 'bg-red-50' : 'bg-[#F9F7F5]'}`}>
              <p className="text-sm text-[#8A796E] mb-1">Deadline</p>
              <p className={`text-xl font-bold ${isPastDeadline ? 'text-red-600' : 'text-[#5C4033]'}`}>
                {deadlineDate.toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
              </p>
              <p className={`text-sm ${isPastDeadline ? 'text-red-500' : 'text-[#8A796E]'}`}>
                {deadlineDate.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                {isPastDeadline && ' (Past deadline)'}
              </p>
            </div>

            {/* Decay Curve */}
            <div className="bg-[#F9F7F5] rounded-2xl p-6">
              <p className="text-sm text-[#8A796E] mb-2">Decay Curve</p>
              <DecayTooltip curve={commitment.decay_curve} />
            </div>

            {/* Payment Status */}
            <div className="bg-[#F9F7F5] rounded-2xl p-6">
              <p className="text-sm text-[#8A796E] mb-1">Payment</p>
              <p className="text-xl font-bold text-[#5C4033]">
                {payment ? (
                  <span className={payment.status === 'paid' ? 'text-green-600' : 'text-yellow-600'}>
                    {payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}
                  </span>
                ) : (
                  <span className="text-[#8A796E]">Not initiated</span>
                )}
              </p>
            </div>
          </div>

          {/* Preview Section (only for non-settled) */}
          {preview && commitment.status !== "settled" && (
            <div className="px-8 pb-6">
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h3 className="font-semibold text-amber-800">
                    {commitment.status === "delivered" ? "Settlement Preview" : "Estimated Outcome (if settled now)"}
                  </h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-amber-700 mb-1">Expected Payout</p>
                    <p className="text-2xl font-bold text-green-600">₹{Number(preview.expected_payout).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-amber-700 mb-1">Expected Refund</p>
                    <p className="text-2xl font-bold text-red-600">₹{Number(preview.expected_refund).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-amber-700 mb-1">Delay</p>
                    <p className="text-2xl font-bold text-[#5C4033]">
                      {preview.delay_minutes > 0 ? `${preview.delay_minutes} min` : 'On time'}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-amber-600 mt-4 italic">
                  * Preview is calculated by backend. Final settlement may differ based on exact delivery time.
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="p-8 border-t border-[#CCBEB1]/30 bg-[#F9F7F5]/50">
            <div className="flex flex-wrap gap-4">
              {/* Fund/Pay Button */}
              {allowed.includes("fund") && (
                <button
                  onClick={handlePay}
                  disabled={actionLoading !== null}
                  className="flex-1 min-w-[200px] py-4 px-6 rounded-2xl font-semibold text-white bg-gradient-to-r from-[#997E67] to-[#5C4634] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center justify-center gap-2"
                >
                  {actionLoading === "fund" ? (
                    <Loading size="sm" />
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                      </svg>
                      Pay ₹{commitment.amount.toLocaleString()}
                    </>
                  )}
                </button>
              )}

              {/* Lock Button */}
              {allowed.includes("lock") && (
                <button
                  onClick={() => performAction("lock", `/commitments/${id}/lock`)}
                  disabled={actionLoading !== null}
                  className="flex-1 min-w-[200px] py-4 px-6 rounded-2xl font-semibold text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center justify-center gap-2"
                >
                  {actionLoading === "lock" ? (
                    <Loading size="sm" />
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      Lock Commitment
                    </>
                  )}
                </button>
              )}

              {/* Deliver Button */}
              {allowed.includes("deliver") && (
                <button
                  onClick={() => performAction("deliver", `/commitments/${id}/deliver`)}
                  disabled={actionLoading !== null}
                  className="flex-1 min-w-[200px] py-4 px-6 rounded-2xl font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center justify-center gap-2"
                >
                  {actionLoading === "deliver" ? (
                    <Loading size="sm" />
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Mark as Delivered
                    </>
                  )}
                </button>
              )}

              {/* Settle Button */}
              {allowed.includes("settle") && (
                <button
                  onClick={handleSettle}
                  disabled={actionLoading !== null}
                  className="flex-1 min-w-[200px] py-4 px-6 rounded-2xl font-semibold text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg flex items-center justify-center gap-2"
                >
                  {actionLoading === "settle" ? (
                    <Loading size="sm" />
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                      Settle Now
                    </>
                  )}
                </button>
              )}

              {/* View Settlement Result */}
              {commitment.status === "settled" && (
                <button
                  onClick={() => router.push(`/result/${id}`)}
                  className="flex-1 min-w-[200px] py-4 px-6 rounded-2xl font-semibold text-[#5C4033] bg-[#FFDBBB] hover:bg-[#ffcfa6] transition-all shadow-lg flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  View Settlement Result
                </button>
              )}
            </div>

            {/* Status message when no actions available */}
            {allowed.length === 0 && commitment.status !== "settled" && (
              <div className="text-center py-4">
                <p className="text-[#8A796E]">
                  {commitment.status === "funded" && "Waiting for payment verification..."}
                  {commitment.status === "expired" && "This commitment has expired."}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Timeline / History */}
        <div className="mt-8 bg-white rounded-2xl shadow-lg p-6">
          <h3 className="font-serif font-bold text-xl text-[#5C4033] mb-4">Commitment Timeline</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-3 h-3 rounded-full bg-[#997E67]" />
              <div>
                <p className="font-medium text-[#5C4033]">Created</p>
                <p className="text-sm text-[#8A796E]">
                  {commitment.created_at
                    ? new Date(commitment.created_at).toLocaleString()
                    : "Date not available"}
                </p>
              </div>
            </div>
            {payment && (
              <div className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${payment.status === 'paid' ? 'bg-green-500' : 'bg-yellow-500'}`} />
                <div>
                  <p className="font-medium text-[#5C4033]">Payment {payment.status}</p>
                  <p className="text-sm text-[#8A796E]">Amount: ₹{payment.amount}</p>
                </div>
              </div>
            )}
            {["locked", "delivered", "settled"].includes(commitment.status) && (
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 rounded-full bg-purple-500" />
                <div>
                  <p className="font-medium text-[#5C4033]">Locked</p>
                  <p className="text-sm text-[#8A796E]">Commitment is now active</p>
                </div>
              </div>
            )}
            {["delivered", "settled"].includes(commitment.status) && (
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <div>
                  <p className="font-medium text-[#5C4033]">Delivered</p>
                  <p className="text-sm text-[#8A796E]">Work marked as complete</p>
                </div>
              </div>
            )}
            {commitment.status === "settled" && (
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 rounded-full bg-green-600" />
                <div>
                  <p className="font-medium text-[#5C4033]">Settled</p>
                  <p className="text-sm text-[#8A796E]">Funds have been distributed</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
