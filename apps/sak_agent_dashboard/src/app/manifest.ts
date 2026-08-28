import type { MetadataRoute } from "next";

/**
 * The web manifest, so the dashboard installs as a standalone app.
 *
 * A wall-mounted ops dashboard is the obvious case: `display: "standalone"`
 * drops the browser chrome, and the dark background matches the canvas token
 * so the splash does not flash white on the way in.
 *
 * Generated rather than a static file so the icon reference cannot drift from
 * `icon.svg`, which Next serves from the same route group.
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Sak-Agent-Family Dashboard",
    short_name: "Sak Dashboard",
    description:
      "Read-only analytics over the SakThai agent family: runs, latency, memory shards, workflows, and guardrail events.",
    start_url: "/",
    display: "standalone",
    background_color: "#070a12",
    theme_color: "#070a12",
    icons: [
      {
        src: "/icon.svg",
        // "any" so the browser will also use it as a maskable-ish app icon;
        // the SVG is a rounded square that already fills its own viewBox.
        sizes: "any",
        type: "image/svg+xml",
      },
    ],
  };
}
