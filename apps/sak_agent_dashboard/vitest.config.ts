import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

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
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
