import { ImageResponse } from "next/og";

/**
 * The social card, rendered at request time by Next's OG image runtime.
 *
 * Deliberately plain and self-contained: no webfont fetch (the edge runtime
 * would have to load it over the network on every miss), no imported tokens
 * (this renders outside the browser, where CSS variables do not exist). The
 * two hex values here are the dark canvas and accent, which is the one place
 * in the app that duplicating them is unavoidable.
 */
export const runtime = "edge";
export const alt = "Sak-Agent-Family Dashboard";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "linear-gradient(135deg, #070a12 0%, #0f172a 55%, #082f3a 100%)",
          color: "#f8fafc",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "16px",
            fontSize: 26,
            color: "#22d3ee",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          <div
            style={{
              width: 20,
              height: 20,
              borderRadius: 6,
              background: "#22d3ee",
              display: "flex",
            }}
          />
          Sak-Agent-Family
        </div>

        <div style={{ display: "flex", fontSize: 78, fontWeight: 700, marginTop: 24 }}>
          Runtime dashboard
        </div>

        <div
          style={{
            display: "flex",
            fontSize: 30,
            color: "#94a3b8",
            marginTop: 20,
            maxWidth: 900,
            lineHeight: 1.4,
          }}
        >
          Runs, latency, memory shards, workflows and guardrail events across the six-persona
          agent family.
        </div>

        <div
          style={{
            display: "flex",
            gap: "12px",
            marginTop: 48,
            fontSize: 22,
            color: "#64748b",
          }}
        >
          {["SakKing", "SakThai", "SakSee", "SakSit", "SakJules", "SakTan"].map((name) => (
            <div
              key={name}
              style={{
                display: "flex",
                padding: "8px 18px",
                borderRadius: 999,
                border: "1px solid #1e293b",
                background: "#0f172a",
              }}
            >
              {name}
            </div>
          ))}
        </div>
      </div>
    ),
    size,
  );
}
