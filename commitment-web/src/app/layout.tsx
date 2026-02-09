import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Pledgos - Commitment Protocol",
  description: "Time-based commitment escrow for freelancers and clients",
};

function TestModeBanner() {
  return (
    <div className="bg-amber-500 text-amber-950 text-center py-2 px-4 text-sm font-medium sticky top-0 z-[100]">
      <span className="inline-flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <strong>TEST MODE</strong> — All transactions are simulated. No real money is involved.
      </span>
    </div>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <TestModeBanner />
        {children}
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
      </body>
    </html>
  );
}
