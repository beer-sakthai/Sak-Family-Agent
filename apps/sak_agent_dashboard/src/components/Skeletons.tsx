"use client";

import React from "react";

/**
 * Loading placeholders shaped like what is coming.
 *
 * A centred "Loading…" gives no sense of what will appear and reflows the
 * whole page when it does; these hold the layout so the first paint after a
 * fetch does not jump.
 */

function Shimmer({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-lg bg-raised/60 ${className}`} aria-hidden />;
}

export function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6" data-testid="kpi-skeleton">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="rounded-2xl border border-line/80 bg-panel/50 p-4 backdrop-blur-xl"
        >
          <Shimmer className="h-2.5 w-20" />
          <Shimmer className="mt-3 h-7 w-16" />
          <Shimmer className="mt-2 h-2.5 w-24" />
        </div>
      ))}
    </div>
  );
}

export function CardGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6"
      data-testid="card-grid-skeleton"
    >
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="space-y-3 rounded-2xl border border-line/80 bg-panel/50 p-5 backdrop-blur-xl"
        >
          <div className="flex items-center gap-2.5">
            <Shimmer className="h-9 w-9 rounded-xl" />
            <div className="flex-1 space-y-2">
              <Shimmer className="h-3.5 w-24" />
              <Shimmer className="h-2.5 w-32" />
            </div>
          </div>
          <Shimmer className="h-14 w-full rounded-xl" />
          <Shimmer className="h-2 w-full rounded-full" />
        </div>
      ))}
    </div>
  );
}

export function PanelSkeleton({ label }: { label: string }) {
  return (
    <div
      role="status"
      aria-label={label}
      className="space-y-4 rounded-2xl border border-line/80 bg-panel/50 p-5 backdrop-blur-xl"
    >
      <Shimmer className="h-4 w-40" />
      <Shimmer className="h-3 w-64" />
      <div className="space-y-2 pt-2">
        {Array.from({ length: 6 }).map((_, index) => (
          <Shimmer key={index} className="h-9 w-full" />
        ))}
      </div>
      <span className="sr-only">{label}</span>
    </div>
  );
}
