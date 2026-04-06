"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">
      {/* ========================================== */}
      {/* NAVIGATION */}
      {/* ========================================== */}
      <nav className="bg-white/90 backdrop-blur-md border-b border-[#CCBEB1]/30 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-lg bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-lg">
                  P
                </div>
                <span className="text-xl font-serif font-bold tracking-tight text-[#5C4033]">
                  Pledgos
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium text-[#5C4033] hover:text-[#997E67] transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="px-5 py-2 text-sm font-medium bg-[#997E67] text-white hover:bg-[#856b56] rounded-lg transition-colors"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* ========================================== */}
      {/* HERO SECTION */}
      {/* ========================================== */}
      <section className="max-w-5xl mx-auto px-4 py-24 text-center">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-serif font-semibold text-[#5C4033] leading-tight mb-6">
          Turn Commitments Into<br />Guaranteed Outcomes
        </h1>
        <p className="text-lg md:text-xl text-[#8A796E] max-w-2xl mx-auto mb-10 leading-relaxed">
          Pledgos ensures accountability through structured financial commitments.
          Work gets delivered on time, or funds are automatically returned.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/signup"
            className="px-8 py-4 text-base font-semibold bg-[#997E67] text-white hover:bg-[#856b56] rounded-xl transition-colors shadow-lg"
          >
            Get Started
          </Link>
          <a
            href="#how-it-works"
            className="px-8 py-4 text-base font-semibold text-[#5C4033] bg-white border border-[#CCBEB1] hover:bg-[#F9F7F5] rounded-xl transition-colors"
          >
            Learn More
          </a>
        </div>

      </section>

      {/* ========================================== */}
      {/* PROBLEM SECTION */}
      {/* ========================================== */}
      <section className="bg-white py-20">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-serif font-semibold text-[#5C4033] mb-4">
              The Problem With Promises
            </h2>
            <p className="text-lg text-[#8A796E] max-w-2xl mx-auto">
              Too often, professional agreements fall through without consequence.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: "Missed Deadlines", desc: "Projects drag on with no accountability" },
              { title: "Broken Promises", desc: "Verbal agreements mean nothing" },
              { title: "Payment Risk", desc: "Clients pay upfront with no guarantee" },
              { title: "No Accountability", desc: "Neither party has skin in the game" },
            ].map((item, i) => (
              <div key={i} className="bg-[#F9F7F5] rounded-xl p-6 text-center">
                <h3 className="font-semibold text-[#5C4033] mb-2">{item.title}</h3>
                <p className="text-sm text-[#8A796E]">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* SOLUTION SECTION */}
      {/* ========================================== */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-serif font-semibold text-[#5C4033] mb-4">
              Introducing Pledgos
            </h2>
            <p className="text-lg text-[#8A796E] max-w-2xl mx-auto">
              A platform that enforces commitments through structured financial accountability.
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {[
              { title: "Locked Funds", desc: "Payments are held securely until work is verified." },
              { title: "Verifiable Delivery", desc: "Evidence-based proof that work was completed." },
              { title: "Automated Settlement", desc: "Funds are released automatically when conditions are met." },
              { title: "Transparent Workflow", desc: "Both parties see exactly where things stand." },
            ].map((item, i) => (
              <div key={i} className="flex gap-4">
                <div className="w-10 h-10 rounded-lg bg-[#FFDBBB]/50 flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-[#997E67]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-[#5C4033] mb-1">{item.title}</h3>
                  <p className="text-sm text-[#8A796E]">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* HOW IT WORKS */}
      {/* ========================================== */}
      <section id="how-it-works" className="bg-white py-20">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-serif font-semibold text-[#5C4033] mb-4">
              How It Works
            </h2>
            <p className="text-lg text-[#8A796E] max-w-2xl mx-auto">
              A simple four-step process that ensures accountability.
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Client Funds", desc: "Payment is staked against a deadline" },
              { step: "2", title: "Freelancer Locks", desc: "Commitment to deliver is confirmed" },
              { step: "3", title: "Work Delivered", desc: "Evidence is submitted for verification" },
              { step: "4", title: "Settlement", desc: "Funds are distributed automatically" },
            ].map((item, i) => (
              <div key={i} className="text-center">
                <div className="w-12 h-12 rounded-full bg-[#997E67] text-white font-bold text-lg flex items-center justify-center mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-semibold text-[#5C4033] mb-2">{item.title}</h3>
                <p className="text-sm text-[#8A796E]">{item.desc}</p>
              </div>
            ))}
          </div>
          {/* Flow Arrow */}
          <div className="hidden md:flex justify-center mt-8">
            <div className="flex items-center gap-4 text-[#CCBEB1]">
              <span className="text-sm">Fund</span>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
              <span className="text-sm">Lock</span>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
              <span className="text-sm">Deliver</span>
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
              <span className="text-sm">Settle</span>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* TRUST SIGNALS */}
      {/* ========================================== */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-serif font-semibold text-[#5C4033] mb-4">
              Built for Trust
            </h2>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { icon: "🔒", title: "Secure Payments", desc: "Funds held safely until delivery" },
              { icon: "📋", title: "Transparent Process", desc: "Both parties see every step" },
              { icon: "✅", title: "Evidence-Based", desc: "Delivery requires proof" },
              { icon: "⚡", title: "Automated", desc: "No manual intervention needed" },
            ].map((item, i) => (
              <div key={i} className="bg-white rounded-xl p-6 text-center border border-[#CCBEB1]/30">
                <div className="text-3xl mb-3">{item.icon}</div>
                <h3 className="font-semibold text-[#5C4033] mb-1">{item.title}</h3>
                <p className="text-sm text-[#8A796E]">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* WHO IT'S FOR */}
      {/* ========================================== */}
      <section className="bg-white py-20">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-serif font-semibold text-[#5C4033] mb-4">
              Who It's For
            </h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: "Freelancers", desc: "Get paid fairly for work delivered on time" },
              { title: "Agencies", desc: "Ensure client projects have clear accountability" },
              { title: "Remote Teams", desc: "Build trust across distributed teams" },
              { title: "Clients", desc: "Pay confidently knowing delivery is guaranteed" },
            ].map((item, i) => (
              <div key={i} className="bg-[#F9F7F5] rounded-xl p-6 text-center">
                <h3 className="font-semibold text-[#5C4033] mb-2">{item.title}</h3>
                <p className="text-sm text-[#8A796E]">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* FINAL CTA */}
      {/* ========================================== */}
      <section className="py-24">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-serif font-semibold text-[#5C4033] mb-6">
            Start Building Accountable Commitments
          </h2>
          <p className="text-lg text-[#8A796E] mb-10">
            Join professionals who trust Pledgos to ensure their agreements are honored.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/signup"
              className="px-8 py-4 text-base font-semibold bg-[#997E67] text-white hover:bg-[#856b56] rounded-xl transition-colors shadow-lg"
            >
              Create Account
            </Link>
            <Link
              href="/login"
              className="px-8 py-4 text-base font-semibold text-[#5C4033] bg-white border border-[#CCBEB1] hover:bg-[#F9F7F5] rounded-xl transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* FOOTER */}
      {/* ========================================== */}
      <footer className="bg-[#5C4033] text-white py-12">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center font-serif font-bold text-sm">
                P
              </div>
              <span className="text-lg font-serif font-bold">Pledgos</span>
            </div>
            <p className="text-sm text-white/70 text-center md:text-left">
              Enforcing professional commitments through structured accountability.
            </p>
            <p className="text-sm text-white/50">
              © 2026 Pledgos. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
