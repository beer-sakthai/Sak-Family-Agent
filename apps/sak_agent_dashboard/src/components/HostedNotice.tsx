"use client";

import React from "react";
import { Cloud, Info } from "lucide-react";

import type { DataSource } from "@/lib/contracts.generated";

interface HostedNoticeProps {
  /** What the last response actually came from. */
  activeSource: DataSource | null;
  /** Whether sample data was explicitly asked for. */
  isDemo: boolean;
}

/**
 * Shown when the deploy is serving sample data that nobody asked for.
 *
 * On a hosted deploy — Vercel, say — there is no `~/.sakthai/` to read, so
 * `resolveSource` degrades to the demo dataset. The source pill already says
 * so in three words; this says what to do about it, because "connect it to a
 * running agent" is not obvious from a badge.
 */
export function HostedNotice({ activeSource, isDemo }: HostedNoticeProps) {
  if (activeSource !== "demo" || isDemo) return null;

  return (
    <div
      data-testid="hosted-notice"
      className="flex flex-wrap items-start gap-3 rounded-2xl border border-hue-amber-line/40 bg-hue-amber-tint/20 p-4 text-hue-amber"
    >
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-hue-amber" aria-hidden />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="text-sm font-medium">
          This deployment is showing sample data, not a live agent family.
        </p>
        <p className="text-xs leading-relaxed text-hue-amber/80">
          No SakThai runtime directory is reachable from this host. Point the dashboard at a
          running agent by setting{" "}
          <code className="rounded bg-hue-amber-tint/60 px-1 py-0.5 font-mono text-[11px]">
            SAKTHAI_API_URL
          </code>{" "}
          (and{" "}
          <code className="rounded bg-hue-amber-tint/60 px-1 py-0.5 font-mono text-[11px]">
            SAKTHAI_API_TOKEN
          </code>
          , from <code className="font-mono text-[11px]">sakthai web setup</code>) in the
          deployment&apos;s environment, or run the dashboard locally beside{" "}
          <code className="font-mono text-[11px]">~/.sakthai</code>.
        </p>
      </div>
      <Cloud className="hidden h-4 w-4 shrink-0 text-hue-amber/60 sm:block" aria-hidden />
    </div>
  );
}

export default HostedNotice;
