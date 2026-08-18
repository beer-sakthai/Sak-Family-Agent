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
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
