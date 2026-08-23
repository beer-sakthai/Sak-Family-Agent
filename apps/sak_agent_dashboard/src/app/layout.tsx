import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "Sak-Agent-Family | Runtime Command Center",
  description: "Real-time intelligence, evaluation, and operations dashboard for Sak-Agent-Family personas.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable} dark`}>
      <body className="bg-[#080b12] text-slate-100 antialiased">
        <header className="sticky top-0 z-50 border-b border-white/[0.07] bg-[#080b12]/85 px-5 py-3 backdrop-blur-xl md:px-7">
          <div className="mx-auto flex max-w-[1600px] items-center justify-between">
            <div className="flex items-center gap-2 text-[11px] font-medium tracking-wide text-slate-500">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,.8)]" />
              <span>PRODUCTION RUNTIME</span>
              <span className="text-slate-700">•</span>
              <span className="hidden sm:inline">HOUSE OF SAK / MAIN</span>
            </div>
            <div className="flex items-center gap-4 text-[11px] text-slate-500">
              <span className="hidden sm:inline">Last sync: just now</span>
              <span className="rounded-md border border-white/[0.08] bg-white/[0.03] px-2 py-1 font-mono text-slate-400">v2.4.0</span>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-[1600px]">{children}</main>
      </body>
    </html>
  );
}
