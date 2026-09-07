import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Outfit } from "next/font/google";
import "./globals.css";

import { THEME_BOOTSTRAP } from "@/lib/theme";

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

/**
 * Ids, models, token counts and timestamps are all tabular here, and the
 * system mono stack varies enough between platforms that columns stopped
 * lining up. One webfont fixes the alignment everywhere `font-mono` is used.
 */
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

/**
 * The origin relative metadata URLs resolve against.
 *
 * Without it Next resolves the OG image against `http://localhost:3000` and
 * says so at build time — which means every social card a deployment serves
 * points at the builder's own machine. `NEXT_PUBLIC_SITE_URL` is the explicit
 * answer (a custom domain); `VERCEL_PROJECT_PRODUCTION_URL` is the stable
 * production hostname Vercel injects, in preference to `VERCEL_URL`, which
 * names the individual deployment and so changes on every push.
 */
function siteUrl(): URL {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL;
  if (explicit) return new URL(explicit);
  const vercel =
    process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
  if (vercel) return new URL(`https://${vercel}`);
  return new URL("http://localhost:3000");
}

export const metadata: Metadata = {
  metadataBase: siteUrl(),
  title: {
    default: "Sak-Agent-Family Dashboard",
    template: "%s · Sak-Agent-Family",
  },
  description:
    "Read-only analytics over the SakThai agent family: runs, latency, memory shards, workflows, and guardrail events.",
  applicationName: "Sak-Agent-Family Dashboard",
  robots: { index: false, follow: false },
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "Sak Dashboard",
    statusBarStyle: "black-translucent",
  },
  openGraph: {
    title: "Sak-Agent-Family Dashboard",
    description:
      "Runs, latency, memory shards, workflows and guardrail events across the six-persona SakThai agent family.",
    type: "website",
  },
};

export const viewport: Viewport = {
  // One entry per scheme: the browser picks the matching one, so the address
  // bar follows the theme instead of staying near-black on a light page.
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#070a12" },
    { media: "(prefers-color-scheme: light)", color: "#f4f6fb" },
  ],
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
    <html
      lang="en"
      className={`${inter.variable} ${outfit.variable} ${jetbrainsMono.variable}`}
      // The bootstrap script writes both attributes before React hydrates, so
      // the server's markup and the client's first read necessarily differ.
      // That is the point of the script; suppress the warning for this node.
      suppressHydrationWarning
    >
      <head>
        {/* Before first paint, not after hydration: see THEME_BOOTSTRAP. */}
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body className="min-h-screen bg-canvas text-fg antialiased">
        {/* The first tab stop on the page. Sighted keyboard users get past the
            sidebar's eight controls in one keystroke; it is off-screen until
            focused. */}
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-xl focus:border focus:border-accent/50 focus:bg-panel focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-fg focus:shadow-glass"
        >
          Skip to content
        </a>

        {/* Ambient wash. Fixed and inert, so it never scrolls, never catches a
            click, and never shows up in the tab order. Opacity is a token, so
            the light theme gets a wash that reads as tint rather than haze. */}
        <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
          <div className="absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full bg-hue-cyan opacity-[var(--wash-alpha)] blur-[120px]" />
          <div className="absolute -right-40 top-1/3 h-[28rem] w-[28rem] rounded-full bg-hue-violet opacity-[var(--wash-alpha)] blur-[120px]" />
          <div className="absolute bottom-0 left-1/3 h-[24rem] w-[24rem] rounded-full bg-hue-emerald opacity-[calc(var(--wash-alpha)*0.6)] blur-[120px]" />
          <div className="absolute inset-0 bg-grid" />
        </div>
        {children}
      </body>
    </html>
  );
}
