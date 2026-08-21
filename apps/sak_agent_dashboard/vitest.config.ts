import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    testTimeout: 60000,
    hookTimeout: 60000,
    fileParallelism: false,
    maxWorkers: 1,
    setupFiles: "./vitest.setup.ts",
    // `output: "standalone"` in next.config.mjs copies the traced source tree
    // into .next/standalone, so vitest's default discovery finds a second copy
    // of every test file there. Those copies fail on `next/server` because they
    // sit outside the module resolution root — 16 phantom file failures beside
    // a green real suite. Excluding build output is the fix; the default
    // `include` is deliberately left alone so a test added outside src/ is
    // still discovered.
    exclude: ["**/node_modules/**", "**/dist/**", "**/.next/**"],
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
