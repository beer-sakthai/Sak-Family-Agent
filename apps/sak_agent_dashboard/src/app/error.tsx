"use client";

import React from "react";
import { AlertTriangle, RotateCw } from "lucide-react";

/**
 * The route error boundary.
 *
 * Without one, an exception in the client tree on a Vercel deploy renders the
 * framework's own blank "Application error" page with the message stripped —
 * which is indistinguishable from the deployment being down. This keeps the
 * digest visible, because that is the string that finds the trace in the
 * Vercel logs.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-xl flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-2xl border border-hue-rose-line/50 bg-hue-rose-tint">
        <AlertTriangle className="h-5 w-5 text-hue-rose" aria-hidden />
      </div>
      <h1 className="font-display text-xl font-bold text-fg">The dashboard stopped rendering</h1>
      <p className="text-sm leading-relaxed text-fg-3">
        This is a fault in the dashboard itself, not in the agent family it reads. Retrying
        re-renders the page without reloading it; if it recurs, the digest below identifies the
        trace in the deployment logs.
      </p>
      {error.digest && (
        <code className="rounded-lg border border-line bg-sunken/70 px-2.5 py-1 font-mono text-[11px] text-fg-4">
          digest {error.digest}
        </code>
      )}
      <button
        onClick={reset}
        className="mt-1 inline-flex items-center gap-2 rounded-xl border border-line-strong bg-panel/70 px-4 py-2 text-sm text-fg-2 transition-colors hover:border-line-strong hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <RotateCw className="h-4 w-4" aria-hidden />
        Try again
      </button>
    </main>
  );
}
