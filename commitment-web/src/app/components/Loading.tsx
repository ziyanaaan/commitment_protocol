"use client";

interface LoadingProps {
  size?: "sm" | "md" | "lg";
  text?: string;
}

export default function Loading({ size = "md", text }: LoadingProps) {
  const sizeClasses = {
    sm: "w-4 h-4 border-2",
    md: "w-8 h-8 border-3",
    lg: "w-12 h-12 border-4",
  };

  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`${sizeClasses[size]} border-[#997E67] border-t-transparent rounded-full animate-spin`}
      />
      {text && (
        <p className="text-sm text-[#8A796E] font-medium animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
}
