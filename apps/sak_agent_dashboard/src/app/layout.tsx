import type { Metadata, Viewport } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sak-Agent-Family Dashboard",
  description:
    "Read-only analytics over the SakThai agent family: runs, latency, memory shards, workflows, and guardrail events.",
  applicationName: "Sak-Agent-Family Dashboard",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: "#070a12",
  width: "device-width",
  initialScale: 1,
};

/**
 * The document shell only.
 *
 * The application chrome — sidebar, topbar, command palette — lives in
 * `page.tsx`, because all of it is driven by the same client state as the
 * panels it frames. This file previously rendered a *second* header with the
 * same title and a hardcoded "Runtime Active" badge that was true regardless
 * of whether anything was running; both are gone.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable} dark`}>
      <body className="min-h-screen bg-[#070a12] text-slate-100 antialiased">
        {/* Ambient wash. Fixed and inert, so it never scrolls, never catches a
            click, and never shows up in the tab order. */}
        <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full bg-cyan-500/10 blur-[120px]" />
          <div className="absolute -right-40 top-1/3 h-[28rem] w-[28rem] rounded-full bg-violet-500/10 blur-[120px]" />
          <div className="absolute bottom-0 left-1/3 h-[24rem] w-[24rem] rounded-full bg-emerald-500/[0.06] blur-[120px]" />
          <div className="absolute inset-0 bg-grid" />
        </div>
        {children}
      </body>
    </html>
  );
}
