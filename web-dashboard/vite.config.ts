import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Served as a GitHub Pages *project* site at /sakthai-agent-v2/, so all asset
// URLs must be prefixed with that base. Override with VITE_BASE for other hosts
// (e.g. set VITE_BASE=/ for a user/org site or local static serving).
const base = process.env.VITE_BASE ?? "/sakthai-agent-v2/";

export default defineConfig({
  base,
  plugins: [react()],
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
