"use client";

import { useState } from "react";

interface DecayTooltipProps {
    curve: string;
}

const CURVE_INFO: Record<string, { label: string; description: string; color: string }> = {
    flexible: {
        label: "Flexible",
        description: "Gentle decay curve. Forgiving for minor delays, penalty grows slowly.",
        color: "#4CAF50",
    },
    balanced: {
        label: "Balanced",
        description: "Moderate decay curve. Fair penalty that scales with delay time.",
        color: "#FF9800",
    },
    strict: {
        label: "Strict",
        description: "Aggressive decay curve. Strong enforcement with rapid penalty growth.",
        color: "#F44336",
    },
    linear: {
        label: "Linear",
        description: "Linear decay curve. Penalty grows proportionally with delay.",
        color: "#2196F3",
    },
};

export default function DecayTooltip({ curve }: DecayTooltipProps) {
    const [isOpen, setIsOpen] = useState(false);
    const info = CURVE_INFO[curve] || CURVE_INFO.balanced;

    return (
        <div className="relative inline-block">
            <button
                type="button"
                onMouseEnter={() => setIsOpen(true)}
                onMouseLeave={() => setIsOpen(false)}
                onFocus={() => setIsOpen(true)}
                onBlur={() => setIsOpen(false)}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide transition-all hover:scale-105"
                style={{ backgroundColor: `${info.color}20`, color: info.color }}
                aria-describedby="decay-tooltip"
            >
                <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: info.color }}
                />
                {info.label}
                <svg
                    className="w-3 h-3 opacity-60"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
            </button>

            {isOpen && (
                <div
                    id="decay-tooltip"
                    role="tooltip"
                    className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-white rounded-xl shadow-xl border border-[#CCBEB1]/40 text-sm text-[#5C4033]"
                >
                    <p className="font-medium mb-1" style={{ color: info.color }}>
                        {info.label} Curve
                    </p>
                    <p className="text-[#8A796E] text-xs leading-relaxed">
                        {info.description}
                    </p>
                    <div
                        className="absolute top-full left-1/2 -translate-x-1/2 -mt-px border-8 border-transparent border-t-white"
                    />
                </div>
            )}
        </div>
    );
}
