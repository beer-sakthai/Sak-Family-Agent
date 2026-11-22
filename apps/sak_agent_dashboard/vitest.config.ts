import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./vitest.setup.ts",
    // better-sqlite3 is a native addon. Serializing files avoids concurrent
    // native handles crashing intermittently while keeping CI deterministic.
    pool: "threads",
    maxWorkers: 1,
    fileParallelism: false,
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@launchdarkly/vercel-server-sdk": fileURLToPath(
        new URL(
          "./node_modules/@launchdarkly/vercel-server-sdk/dist/cjs/src/index.js",
          import.meta.url,
        ),
      ),
    },
  },
});
