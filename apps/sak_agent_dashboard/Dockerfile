# Runtime image for the Sak Agent dashboard.
#
# BUILD FROM THE REPOSITORY ROOT, not from this directory:
#
#     docker build -f apps/sak_agent_dashboard/Dockerfile -t sak-dashboard .
#
# The app is not self-contained. `src/lib/docs.ts`, `designSpecs.ts` and
# `mcpSdk.ts` all resolve the monorepo root as `process.cwd()/../..` and read
# `docs/`, `personas/` and `services/` from there *at request time*, so the
# image has to preserve the apps/<name> directory depth and carry those trees.
# `Dockerfile.dockerignore` beside this file scopes that context — BuildKit
# prefers it over the repository root `.dockerignore`, which excludes `apps/`
# and `docs/` because the agent image does not want them.
#
# Pinned to an exact patch version and by digest, matching Dockerfile.sandbox
# and the agent Dockerfile. The digest below is the manifest list digest of
# node:22.22.2-slim, verified against the Docker Hub registry API:
#     docker buildx imagetools inspect node:22.22.2-slim --format '{{.Manifest.Digest}}'
FROM node:22.22.2-slim@sha256:9f6d5975c7dca860947d3915877f85607946403fc55349f39b4bc3688448bb6e AS builder

# better-sqlite3 is a native module. It ships prebuilt binaries, but keep the
# toolchain here so a platform without a matching prebuild still builds rather
# than failing the image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

# The pnpm version is pinned by `packageManager` in package.json; corepack
# honours it, so the image resolves the same tree the lockfile was made with.
RUN corepack enable

WORKDIR /repo/apps/sak_agent_dashboard

# Dependencies first, so a source-only change does not re-resolve the tree.
COPY apps/sak_agent_dashboard/package.json \
     apps/sak_agent_dashboard/pnpm-lock.yaml \
     apps/sak_agent_dashboard/pnpm-workspace.yaml \
     ./
RUN pnpm install --frozen-lockfile

# The monorepo trees the build traces and the runtime reads.
COPY docs/ /repo/docs/
COPY personas/ /repo/personas/
COPY services/ /repo/services/
COPY apps/sak_agent_dashboard/ ./

# `output: "standalone"` in next.config.mjs produces .next/standalone, mirroring
# the monorepo layout beneath it.
RUN pnpm build

# Repair the traced bundle before it is copied into the runtime stage.
#
# Next's tracer copies only `@swc/helpers/cjs`, but `next/dist/server/
# require-hook.js` resolves `@swc/helpers/esm/_interop_require_default.js`
# through the package's exports map at startup. The emitted server.js therefore
# dies with MODULE_NOT_FOUND before serving a single request. An
# `outputFileTracingIncludes` entry does not fix it — the glob does not reach
# into pnpm's content-addressed store — so overwrite the traced copy with the
# real installed package, which has both `cjs/` and `esm/`.
RUN set -eu; \
    src="$(find node_modules/.pnpm -maxdepth 4 -type d \
              -path '*@swc+helpers*/node_modules/@swc/helpers' | head -1)"; \
    dest="$(find .next/standalone -maxdepth 6 -type d \
              -path '*@swc+helpers*/node_modules/@swc/helpers' | head -1)"; \
    test -n "$src" && test -n "$dest"; \
    test -f "$src/esm/_interop_require_default.js"; \
    rm -rf "$dest"; cp -a "$src" "$dest"; \
    test -f "$dest/esm/_interop_require_default.js"; \
    echo "repaired @swc/helpers in the standalone bundle"

# Assert the SQLite driver really is in the bundle, with a Linux binary.
#
# Unlike @swc/helpers, better-sqlite3 IS traced correctly — into pnpm's store at
# node_modules/.pnpm/better-sqlite3@*/, with prebuilt N-API binaries, which is
# why no compile or extra install is needed in the runtime stage. What it does
# NOT get is the convenience symlink at node_modules/better-sqlite3, so plain
# `require.resolve` fails while Next's own resolution succeeds. Assert on the
# files, not on require(): an image that ships without this driver starts
# cleanly, serves every page, and reports zero rows for every persona.
RUN set -eu; \
    pkg="$(find .next/standalone -maxdepth 9 -type d \
             -path '*better-sqlite3@*/node_modules/better-sqlite3' | head -1)"; \
    test -n "$pkg" || { echo "better-sqlite3 missing from standalone bundle"; exit 1; }; \
    test -f "$pkg/prebuilds/linux-x64.node" || { echo "no linux-x64 prebuild"; exit 1; }; \
    echo "better-sqlite3 present with a linux-x64 prebuild"


FROM node:22.22.2-slim@sha256:9f6d5975c7dca860947d3915877f85607946403fc55349f39b4bc3688448bb6e AS runner

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app/apps/sak_agent_dashboard

# The standalone bundle carries the traced monorepo layout: /app/apps/... plus
# /app/docs, /app/personas, /app/services. With WORKDIR two levels down,
# `process.cwd()/../..` resolves to /app, which is what the lib modules expect.
COPY --from=builder /repo/apps/sak_agent_dashboard/.next/standalone/ /app/
COPY --from=builder /repo/apps/sak_agent_dashboard/.next/static/ \
     /app/apps/sak_agent_dashboard/.next/static/
COPY --from=builder /repo/apps/sak_agent_dashboard/public/ \
     /app/apps/sak_agent_dashboard/public/

# Drop privileges. The node image ships an unprivileged `node` user (UID 1000);
# the memory volume is mounted read-only, so this user never needs to write it.
RUN chown -R node:node /app
USER node

EXPOSE 3000

# The dashboard serves personal memory and 47 of its 48 API routes have no
# authentication of any kind. Publish this port to 127.0.0.1 only and put an
# authenticating reverse proxy in front — see infra/vm-agents/docker-compose.yml.
CMD ["node", "apps/sak_agent_dashboard/server.js"]
