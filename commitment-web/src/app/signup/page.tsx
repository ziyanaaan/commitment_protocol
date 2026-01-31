"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signup, validatePassword } from "@/lib/auth";

export default function SignupPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [role, setRole] = useState<"client" | "freelancer">("client");
    const [error, setError] = useState("");
    const [passwordErrors, setPasswordErrors] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [publicId, setPublicId] = useState("");

    const handlePasswordChange = (value: string) => {
        setPassword(value);
        const validation = validatePassword(value);
        setPasswordErrors(validation.errors);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        // Client-side validation
        const validation = validatePassword(password);
        if (!validation.isValid) {
            setPasswordErrors(validation.errors);
            setIsLoading(false);
            return;
        }

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            setIsLoading(false);
            return;
        }

        try {
            const result = await signup({ email, password, role });
            setSuccess(true);
            setPublicId(result.public_id);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Signup failed");
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">
                {/* Navigation */}
                <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
                    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex justify-between h-20">
                            <div className="flex items-center gap-10">
                                <Link href="/" className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-[#997E67]/20">
                                        P
                                    </div>
                                    <span className="text-2xl font-serif font-bold tracking-tight text-[#5C4033]">
                                        PLEDGOS
                                    </span>
                                </Link>
                            </div>
                        </div>
                    </div>
                </nav>

                {/* Success Content */}
                <section className="max-w-md mx-auto px-4 py-20">
                    <div className="bg-white rounded-2xl shadow-xl border border-[#CCBEB1]/40 p-8">
                        <div className="text-center">
                            <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-serif font-bold text-[#5C4033] mb-2">Account Created!</h2>
                            <p className="text-[#8A796E] mb-6">
                                Your account has been created successfully.
                            </p>
                            <div className="bg-[#F9F7F5] rounded-xl p-4 mb-6 border border-[#CCBEB1]/40">
                                <p className="text-sm text-[#8A796E] mb-1">Your Account ID</p>
                                <p className="text-lg font-mono text-[#997E67] tracking-wide">{publicId}</p>
                            </div>
                            <Link
                                href="/login"
                                className="inline-block w-full py-3 px-4 bg-[#997E67] text-white font-medium rounded-xl hover:bg-[#856b56] shadow-lg transition-all duration-200"
                            >
                                Continue to Sign In
                            </Link>
                        </div>
                    </div>
                </section>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-[#F9F7F5] text-[#5C4033]">
            {/* Navigation */}
            <nav className="bg-white/80 backdrop-blur-md border-b border-[#CCBEB1]/40 sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-20">
                        <div className="flex items-center gap-10">
                            <Link href="/" className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-[#997E67] flex items-center justify-center text-white font-serif font-bold text-xl shadow-lg shadow-[#997E67]/20">
                                    P
                                </div>
                                <span className="text-2xl font-serif font-bold tracking-tight text-[#5C4033]">
                                    PLEDGOS
                                </span>
                            </Link>
                        </div>
                        <div className="flex items-center gap-4">
                            <Link
                                href="/login"
                                className="px-4 py-2 text-sm font-medium text-[#5C4033] hover:text-[#997E67] transition-colors"
                            >
                                Sign In
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Signup Form */}
            <section className="max-w-md mx-auto px-4 py-16">
                <div className="bg-white rounded-2xl shadow-xl border border-[#CCBEB1]/40 p-8">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <h1 className="text-3xl font-serif font-bold text-[#5C4033] mb-2">Create Account</h1>
                        <p className="text-[#8A796E]">Join the Commitment Protocol</p>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Email */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Email Address
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full px-4 py-3 bg-white border border-[#CCBEB1] rounded-xl text-[#5C4033] placeholder-[#CCBEB1] focus:outline-none focus:ring-2 focus:ring-[#997E67] focus:border-transparent transition-all"
                                placeholder="you@example.com"
                            />
                        </div>

                        {/* Role Selection */}
                        <div>
                            <label className="block text-sm font-medium text-[#5C4033] mb-2">
                                I am a...
                            </label>
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    type="button"
                                    onClick={() => setRole("client")}
                                    className={`py-3 px-4 rounded-xl border-2 transition-all duration-200 ${role === "client"
                                            ? "border-[#997E67] bg-[#997E67]/10 text-[#5C4033]"
                                            : "border-[#CCBEB1] text-[#8A796E] hover:border-[#997E67]/50"
                                        }`}
                                >
                                    <div className="font-medium">Client</div>
                                    <div className="text-xs opacity-75">I hire freelancers</div>
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setRole("freelancer")}
                                    className={`py-3 px-4 rounded-xl border-2 transition-all duration-200 ${role === "freelancer"
                                            ? "border-[#997E67] bg-[#997E67]/10 text-[#5C4033]"
                                            : "border-[#CCBEB1] text-[#8A796E] hover:border-[#997E67]/50"
                                        }`}
                                >
                                    <div className="font-medium">Freelancer</div>
                                    <div className="text-xs opacity-75">I complete work</div>
                                </button>
                            </div>
                        </div>

                        {/* Password */}
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => handlePasswordChange(e.target.value)}
                                required
                                className="w-full px-4 py-3 bg-white border border-[#CCBEB1] rounded-xl text-[#5C4033] placeholder-[#CCBEB1] focus:outline-none focus:ring-2 focus:ring-[#997E67] focus:border-transparent transition-all"
                                placeholder="••••••••"
                            />
                            {passwordErrors.length > 0 && (
                                <div className="mt-2 space-y-1">
                                    {passwordErrors.map((err, i) => (
                                        <p key={i} className="text-sm text-red-600">{err}</p>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Confirm Password */}
                        <div>
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-[#5C4033] mb-2">
                                Confirm Password
                            </label>
                            <input
                                id="confirmPassword"
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                className="w-full px-4 py-3 bg-white border border-[#CCBEB1] rounded-xl text-[#5C4033] placeholder-[#CCBEB1] focus:outline-none focus:ring-2 focus:ring-[#997E67] focus:border-transparent transition-all"
                                placeholder="••••••••"
                            />
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
                                <p className="text-sm text-red-600">{error}</p>
                            </div>
                        )}

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3 px-4 bg-[#997E67] text-white font-medium rounded-xl hover:bg-[#856b56] focus:outline-none focus:ring-2 focus:ring-[#997E67] focus:ring-offset-2 shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <span className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                    Creating Account...
                                </span>
                            ) : (
                                "Create Account"
                            )}
                        </button>
                    </form>

                    {/* Login Link */}
                    <div className="mt-6 text-center">
                        <p className="text-[#8A796E]">
                            Already have an account?{" "}
                            <Link href="/login" className="text-[#997E67] hover:text-[#856b56] font-medium">
                                Sign in
                            </Link>
                        </p>
                    </div>
                </div>
            </section>
        </main>
    );
}
