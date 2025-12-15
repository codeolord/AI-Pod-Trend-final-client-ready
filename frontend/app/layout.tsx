import "./globals.css";
import type { Metadata } from "next";

const BRAND_NAME = process.env.NEXT_PUBLIC_BRAND_NAME || "POD Trend Dashboard";
const BRAND_TAGLINE =
  process.env.NEXT_PUBLIC_BRAND_TAGLINE ||
  "AI-driven print-on-demand trend ingestion, scoring, and idea generation.";

export const metadata: Metadata = {
  title: BRAND_NAME,
  description: BRAND_TAGLINE,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-50">
        <div className="max-w-6xl mx-auto p-6">
          <header className="mb-8">
            <h1 className="text-3xl font-bold tracking-tight">{BRAND_NAME}</h1>
            <p className="text-slate-300 mt-1 text-sm">{BRAND_TAGLINE}</p>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
