"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useEffect } from "react";

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
  const [loading, setLoading] = useState(false);
  const [decayCurve, setDecayCurve] = useState<"flexible" | "balanced" | "strict">("balanced");
  useEffect(() => {
    if (deadlineDate && deadlineTime) {
     setDeadline(`${deadlineDate}T${deadlineTime}`);
   }
  }, [deadlineDate, deadlineTime]);


  async function create() {
    setLoading(true);
    setError(null);
    
    try {
      const res = await api<any>("/commitments", {
        method: "POST",
        body: JSON.stringify({
          client_id: clientId,               // temporary
          freelancer_id: freelancerId,
          amount,
          title,
          description,
          deadline: new Date(deadline).toISOString(),
          decay_curve: decayCurve,     
        }),
      });

      router.push(`/commitments/${res.id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
  <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">

    {/* Top bar */}
    <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-20 flex items-center">
        <h1 className="text-2xl font-serif font-bold">Create Commitment</h1>
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
            className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67]"
          />
        </div>

        {/* Freelancer ID */}
        <div>
          <label className="block text-sm font-medium mb-1">Freelancer ID</label>
          <input
            type="number"
            value={freelancerId}
            onChange={(e) => setFreelancerId(Number(e.target.value))}
            className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67]"
          />
        </div>

        {/* Title */}
        <div>
          <label className="block text-sm font-medium mb-1">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Commitment title"
            className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67]"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe your commitment"
            className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67]"
          />
        </div>

        {/* Amount */}
        <div>
          <label className="block text-sm font-medium mb-1">Amount</label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67]"
          />
        </div>

        {/* Deadline (split) */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Deadline date</label>
            <input
              type="date"
              value={deadlineDate}
              onChange={(e) => setDeadlineDate(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Deadline time</label>
            <input
              type="time"
              value={deadlineTime}
              onChange={(e) => setDeadlineTime(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-[#CCBEB1] focus:ring-2 focus:ring-[#997E67]"
            />
          </div>
        </div>

        {/* Decay curve cards (UNCHANGED LOGIC) */}
        <div>
          <h3 className="text-lg font-serif font-medium mb-4">Decay Curve</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {["flexible", "balanced", "strict"].map((type) => (
              <label
                key={type}
                className={`p-4 rounded-2xl border cursor-pointer ${
                  decayCurve === type
                    ? "border-[#997E67] bg-[#FFDBBB]/40"
                    : "border-[#CCBEB1]"
                }`}
              >
                <input
                  type="radio"
                  name="decay"
                  value={type}
                  checked={decayCurve === type}
                  onChange={() => setDecayCurve(type as any)}
                  className="hidden"
                />
                <h4 className="font-medium capitalize">{type}</h4>
              </label>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={create}
          disabled={loading}
          className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#997E67] to-[#5C4634] text-white font-semibold shadow-lg hover:opacity-90 transition"
        >
          {loading ? "Creating..." : "Create Commitment"}
        </button>

        {error && <p className="text-red-600 text-sm">{error}</p>}
      </div>
    </section>
  </main>

  );
}
