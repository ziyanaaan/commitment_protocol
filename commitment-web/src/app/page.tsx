"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Home() {
  const [id, setId] = useState("");
  const router = useRouter();

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#FFDBBB] via-[#CCBEB1] to-[#997E67]">
      <div className="w-full max-w-lg bg-[#F7F2ED] rounded-3xl shadow-xl p-8">
        
        {/* Title */}
        <h1 className="text-3xl font-bold text-[#5C4634] text-center mb-2">
          Commitment Protocol
        </h1>

        <p className="text-center text-[#7A6656] mb-8">
          Lock your promise. Prove delivery. Earn your stake.
        </p>

        {/* Create commitment */}
        <button
          onClick={() => router.push("/commitments/new")}
          className="w-full mb-6 py-3 rounded-2xl bg-gradient-to-r from-[#997E67] to-[#5C4634] text-white font-semibold hover:opacity-90 transition"
        >
          Create New Commitment
        </button>

        <div className="flex items-center my-6">
          <div className="flex-1 h-px bg-[#CCBEB1]" />
          <span className="px-3 text-sm text-[#7A6656]">OR</span>
          <div className="flex-1 h-px bg-[#CCBEB1]" />
        </div>

        {/* Open commitment */}
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Enter Commitment ID"
            value={id}
            onChange={(e) => setId(e.target.value)}
            className="w-full px-4 py-3 rounded-2xl border border-[#CCBEB1] focus:outline-none focus:ring-2 focus:ring-[#997E67] bg-white text-[#5C4634]"
          />

          <button
            onClick={() => router.push(`/commitments/${id}`)}
            disabled={!id}
            className="w-full py-3 rounded-2xl bg-[#997E67] text-white font-semibold disabled:opacity-40 hover:bg-[#5C4634] transition"
          >
            Open Commitment
          </button>
        </div>

        {/* Footer */}
        <p className="text-xs text-center text-[#8B7766] mt-8">
          Discipline enforced by code, not motivation.
        </p>
      </div>
    </main>
  );
}
