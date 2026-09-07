import Link from "next/link";
import { Compass } from "lucide-react";

/**
 * 404.
 *
 * The dashboard is a single page whose sections are URL fragments, so every
 * real destination is `/#section` and any other path is a typo or a stale
 * link. Saying that is more useful than a bare "404".
 */
export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-xl flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-2xl border border-line-strong bg-panel/70">
        <Compass className="h-5 w-5 text-fg-3" aria-hidden />
      </div>
      <h1 className="font-display text-xl font-bold text-fg">No such page</h1>
      <p className="text-sm leading-relaxed text-fg-3">
        The dashboard is one page; its sections are fragments of it — <code>/#overview</code>,{" "}
        <code>/#sessions</code>, <code>/#memory</code>. Its data lives under <code>/api/</code>.
      </p>
      <Link
        href="/"
        className="mt-1 rounded-xl border border-line-strong bg-panel/70 px-4 py-2 text-sm text-fg-2 transition-colors hover:border-line-strong hover:text-fg focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        Back to the dashboard
      </Link>
    </main>
  );
}
