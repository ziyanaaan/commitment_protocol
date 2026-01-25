"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function NewCommitmentPage() {
  const router = useRouter();
  const [clientId, setClientId] = useState(1);
  const [freelancerId, setFreelancerId] = useState(2);
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [amount, setAmount] = useState(1000);
  const [deadline, setDeadline] = useState("");
  const [deadlineDate, setDeadlineDate] = useState("");
  const [deadlineTime, setDeadlineTime] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [deadlineError, setDeadlineError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [decayCurve, setDecayCurve] = useState<"flexible" | "balanced" | "strict">("balanced");

  // Get today's date in YYYY-MM-DD format for min date attribute
  const today = useMemo(() => {
    const now = new Date();
    return now.toISOString().split('T')[0];
  }, []);

  // Get current time in HH:MM format
  const currentTime = useMemo(() => {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  }, []);

  // Combine date and time, validate that deadline is in the future
  useEffect(() => {
    if (deadlineDate && deadlineTime) {
      const combined = `${deadlineDate}T${deadlineTime}`;
      const selectedDate = new Date(combined);
      const now = new Date();

      if (selectedDate <= now) {
        setDeadlineError("Deadline must be in the future. Please select a valid date and time.");
        setDeadline("");
      } else {
        setDeadlineError(null);
        setDeadline(combined);
      }
    } else {
      setDeadlineError(null);
      setDeadline("");
    }
  }, [deadlineDate, deadlineTime]);

  // Check if form is valid
  const isFormValid = useMemo(() => {
    return (
      title.trim() !== "" &&
      amount > 0 &&
      deadline !== "" &&
      deadlineError === null
    );
  }, [title, amount, deadline, deadlineError]);

  async function create() {
    // Final validation before submit
    if (!isFormValid) {
      setError("Please fill in all required fields with valid values.");
      return;
    }

    const selectedDeadline = new Date(deadline);
    const now = new Date();

    if (selectedDeadline <= now) {
      setDeadlineError("Deadline must be in the future. Please select a valid date and time.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api<{ id: number }>("/commitments", {
        method: "POST",
        body: JSON.stringify({
          client_id: clientId,
          freelancer_id: freelancerId,
          amount,
          title,
          description,
          deadline: selectedDeadline.toISOString(),
          decay_curve: decayCurve,
        }),
      });

      router.push(`/commitments/${res.id}`);
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Failed to create commitment";
      setError(message);
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
      <section className="max-w-3xl mx-auto px-4 py-12">
        <div className="bg-white rounded-3xl shadow-xl p-8 space-y-8">

          {/* Client ID */}
          <div>
            <label className="block text-sm font-medium mb-1">Client ID</label>
            <input
              type="number"
              value={clientId}
              onChange={(e) => setClientId(Number(e.target.value))}
              className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67] focus:outline-none"
            />
          </div>

          {/* Freelancer ID */}
          <div>
            <label className="block text-sm font-medium mb-1">Freelancer ID</label>
            <input
              type="number"
              value={freelancerId}
              onChange={(e) => setFreelancerId(Number(e.target.value))}
              className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67] focus:outline-none"
            />
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Commitment title"
              className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67] focus:outline-none"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your commitment"
              rows={3}
              className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67] focus:outline-none resize-none"
            />
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Amount (₹) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={amount}
              min={1}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67] focus:outline-none"
            />
          </div>

          {/* Deadline (split) */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Deadline <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-[#8A796E] mb-1">Date</label>
                <input
                  type="date"
                  value={deadlineDate}
                  min={today}
                  onChange={(e) => setDeadlineDate(e.target.value)}
                  className={`w-full px-4 py-3 rounded-xl border focus:ring-2 focus:outline-none ${deadlineError
                      ? 'border-red-400 focus:ring-red-300'
                      : 'border-[#CCBEB1] focus:ring-[#997E67]'
                    }`}
                />
              </div>

              <div>
                <label className="block text-xs text-[#8A796E] mb-1">Time</label>
                <input
                  type="time"
                  value={deadlineTime}
                  min={deadlineDate === today ? currentTime : undefined}
                  onChange={(e) => setDeadlineTime(e.target.value)}
                  className={`w-full px-4 py-3 rounded-xl border focus:ring-2 focus:outline-none ${deadlineError
                      ? 'border-red-400 focus:ring-red-300'
                      : 'border-[#CCBEB1] focus:ring-[#997E67]'
                    }`}
                />
              </div>
            </div>

            {/* Deadline Error Message */}
            {deadlineError && (
              <div className="mt-2 flex items-center gap-2 text-red-600 text-sm">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{deadlineError}</span>
              </div>
            )}
          </div>

          {/* Decay curve cards */}
          <div>
            <h3 className="text-lg font-serif font-medium mb-4">Decay Curve</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(["flexible", "balanced", "strict"] as const).map((type) => (
                <label
                  key={type}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all hover:shadow-md ${decayCurve === type
                      ? "border-[#997E67] bg-[#FFDBBB]/40 shadow-sm"
                      : "border-[#CCBEB1] hover:border-[#997E67]/50"
                    }`}
                >
                  <input
                    type="radio"
                    name="decay"
                    value={type}
                    checked={decayCurve === type}
                    onChange={() => setDecayCurve(type)}
                    className="hidden"
                  />
                  <h4 className="font-medium capitalize">{type}</h4>
                  <p className="text-xs text-[#8A796E] mt-1">
                    {type === "flexible" && "Gentle penalty for delays"}
                    {type === "balanced" && "Fair, moderate penalty"}
                    {type === "strict" && "Strong deadline enforcement"}
                  </p>
                </label>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={create}
            disabled={loading || !isFormValid}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#997E67] to-[#5C4634] text-white font-semibold shadow-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Creating..." : "Create Commitment"}
          </button>

          {/* General Error */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}
        </div>
      </section>
    </main>

  );
}
