import { CardGridSkeleton, KpiSkeleton } from "@/components/Skeletons";

/**
 * The route-level fallback.
 *
 * The page is a client component that fetches after mount, so this covers the
 * gap before its JavaScript arrives — which on a cold Vercel edge hit is the
 * part of the load a user actually waits through. Shaped like the real page,
 * so the first paint after hydration does not jump.
 */
export default function Loading() {
  return (
    <div className="mx-auto w-full max-w-[110rem] space-y-5 px-4 py-6 sm:px-6 lg:px-8">
      <div className="h-10 w-56 animate-pulse rounded-xl bg-raised/50" aria-hidden />
      <KpiSkeleton />
      <CardGridSkeleton />
      <span className="sr-only">Loading the dashboard</span>
    </div>
  );
}
