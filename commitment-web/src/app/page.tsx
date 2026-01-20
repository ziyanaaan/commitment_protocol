"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function Home() {
  const [id, setId] = useState("");
  const router = useRouter();

  return (
    <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">

  {/* Navigation */}
  <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between h-20">
        <div className="flex items-center gap-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-[#997E67]/20">
              P
            </div>
            <span className="text-2xl font-serif font-bold tracking-tight text-[#5C4033]">
              PLEDGOS
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/commitments/new")}
            className="px-5 py-2 text-sm font-medium bg-[#997E67] text-white hover:bg-[#856b56] shadow-md rounded-lg transition-colors"
          >
            Get Started
          </button>
        </div>
      </div>
    </div>
  </nav>

  {/* Hero */}
  <section className="max-w-5xl mx-auto px-4 py-20">
    <div className="flex flex-col items-center justify-center text-center space-y-10">

      <div className="space-y-6 max-w-3xl">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFDBBB]/30 border border-[#FFDBBB] text-[#997E67] text-xs font-bold uppercase tracking-widest">
          <span className="w-2 h-2 rounded-full bg-[#997E67] animate-pulse"></span>
          Live Protocol v1.0
        </div>

        <h1 className="text-5xl md:text-7xl font-serif font-medium tracking-tight text-[#5C4033] leading-[1.1]">
          Commitment Protocol
        </h1>

        <p className="text-xl text-[#8A796E] leading-relaxed font-light max-w-2xl mx-auto">
          A refined registry for time-bounded professional pledges.
          Secure, verifiable, and elegantly simple.
        </p>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-5 w-full max-w-md pt-8">

        {/* Create commitment (existing route) */}
        <button
          onClick={() => router.push("/commitments/new")}
          className="flex-1 inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium bg-[#997E67] text-white hover:bg-[#856b56] shadow-xl rounded-xl transition-all"
        >
          Create Commitment
        </button>

        {/* Open commitment (existing logic, Enter enabled) */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (id) router.push(`/commitments/${id}`);
          }}
          className="flex-1 flex gap-2"
        >
          <input
            placeholder="Commitment ID"
            value={id}
            onChange={(e) => setId(e.target.value)}
            className="flex-1 px-4 py-3 rounded-xl border border-[#CCBEB1] bg-white text-[#5C4033] focus:outline-none focus:ring-2 focus:ring-[#997E67]"
          />

          <button
            type="submit"
            disabled={!id}
            className="px-5 py-3 bg-[#FFDBBB] text-[#5C4033] hover:bg-[#ffcfa6] border border-[#FFDBBB] rounded-xl transition disabled:opacity-40"
          >
            Open
          </button>
        </form>


      </div>

    </div>
  </section>

</main>

  );
}
