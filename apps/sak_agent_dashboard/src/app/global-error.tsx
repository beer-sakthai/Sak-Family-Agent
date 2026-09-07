"use client";

import React from "react";

/**
 * The last-resort boundary: an error thrown in the root layout itself, where
 * `error.tsx` never mounts because there is no layout left to render it in.
 *
 * It must render its own `<html>` and `<body>`, and it cannot rely on the
 * stylesheet the layout imports, the theme bootstrap, or the token layer —
 * hence the inline `<style>`, which carries just enough of both palettes to
 * honour `prefers-color-scheme`. Everything here is deliberately
 * dependency-free: this is the page that renders when nothing else can.
 */
const STYLE = `
  :root { color-scheme: light dark; --bg:#ffffff; --fg:#0f172a; --dim:#475569; --edge:#cbd5e1; --btn:#f8fafc }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#070a12; --fg:#f8fafc; --dim:#94a3b8; --edge:#334155; --btn:#0f172a }
  }
  body { margin:0; min-height:100vh; display:grid; place-items:center; padding:1.5rem;
         background:var(--bg); color:var(--fg); font-family:system-ui,sans-serif; text-align:center }
  main { max-width:32rem }
  h1 { font-size:1.25rem; font-weight:700 }
  p { color:var(--dim); font-size:0.875rem; line-height:1.6 }
  button { margin-top:0.75rem; padding:0.5rem 1rem; border-radius:0.75rem; border:1px solid var(--edge);
           background:var(--btn); color:var(--fg); font-size:0.875rem; cursor:pointer }
`;

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <head>
        <style>{STYLE}</style>
      </head>
      <body>
        <main>
          <h1>The dashboard failed to start</h1>
          <p>
            The error happened in the root layout, before any of the application shell existed.
            {error.digest ? ` Digest ${error.digest}.` : ""}
          </p>
          <button onClick={reset} type="button">
            Try again
          </button>
        </main>
      </body>
    </html>
  );
}
