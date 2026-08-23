import path from "node:path";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit .next/standalone: a self-contained server carrying only the traced
  // dependencies. This is what infra/vm-agents/docker-compose.yml deploys —
  // without it the runtime image has to carry the entire node_modules tree.
  //
  // Vercel is the exception. It builds its own serverless output from the
  // trace and never runs `.next/standalone/server.js`, so emitting it there
  // only duplicates ~77 MB of traced files into the build artifact for nothing.
  // `VERCEL` is set on every Vercel build (system env var), so Docker and local
  // builds are unaffected.
  output: process.env.VERCEL ? undefined : "standalone",
  // The repo root is the pnpm workspace above this app, and Next's file tracing
  // walks up to find it. Pinning it keeps the standalone trace deterministic
  // and silences the multiple-lockfile inference warning.
  outputFileTracingRoot: path.join(import.meta.dirname, "../../"),
  // The monorepo files these routes read *at request time*. `docs.ts`,
  // `designSpecs.ts`, `mcpSdk.ts` and `mcpServers.ts` resolve the repo root by
  // walking up from `process.cwd()`, which no bundler can follow — so the files
  // have to be named here or the serverless function ships without them and
  // every one of these panels reports "unavailable" in production.
  //
  // These globs are deliberately narrow. The alternative is what the build used
  // to do before the `turbopackIgnore` comments in those modules: give up and
  // trace the whole project, which pulled `personas/` (2,980 files) and the
  // vendored M365 SDK into every function and took the trace from 77 MB to
  // 121 MB, heading for Vercel's 250 MB uncompressed function limit.
  outputFileTracingIncludes: {
    // Keys are matched as globs, so a literal "/docs/[page]" silently matches
    // nothing — "[page]" is a character class, not the dynamic segment. Use
    // "/**" instead; a bracketed key traces zero files and fails silently.
    "/docs/**": ["../../docs/*.md", "../../docs/superpowers/specs/*.md"],
    "/api/docs/**": ["../../docs/*.md"],
    "/api/design-specs": ["../../docs/superpowers/specs/*.md"],
    "/api/mcp-sdk": ["../../personas/sakthai/sakthai/mcp/*.py"],
  },
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
