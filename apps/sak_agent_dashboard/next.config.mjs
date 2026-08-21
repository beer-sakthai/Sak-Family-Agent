import path from "node:path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit .next/standalone: a self-contained server carrying only the traced
  // dependencies. This is what infra/vm-agents/docker-compose.yml deploys —
  // without it the runtime image has to carry the entire node_modules tree.
  output: "standalone",
  // The repo root is the pnpm workspace above this app, and Next's file tracing
  // walks up to find it. Pinning it keeps the standalone trace deterministic
  // and silences the multiple-lockfile inference warning.
  outputFileTracingRoot: path.join(import.meta.dirname, "../../"),
  // NOTE: @swc/helpers is traced incompletely — only its `cjs/` directory
  // arrives, while `next/dist/server/require-hook.js` resolves
  // `@swc/helpers/esm/_interop_require_default.js` through the package's
  // exports map at startup, so the emitted server.js throws MODULE_NOT_FOUND
  // before serving a single request. An `outputFileTracingIncludes` entry for
  // it was tried and did NOT fix it (the glob does not reach into pnpm's
  // content-addressed store), so the Dockerfile copies the package over the
  // traced one instead. Verified by running the emitted server.js directly.
  // `swcMinify` was removed as a valid option in Next 15 (SWC minification is
  // always on) and Next 16 warns about it, so it is deliberately absent here.
  //
  // `src/instrumentation.ts` needs no config either: the instrumentation hook
  // graduated from `experimental.instrumentationHook` to stable in Next 15, and
  // re-adding that flag would raise the same kind of unrecognized-option warning.
};

export default nextConfig;
