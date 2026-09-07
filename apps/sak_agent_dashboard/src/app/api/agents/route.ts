/**
 * `GET /api/agents` — per-persona status and activity.
 *
 * Kept at `/api/agents` rather than `/api/personas` for URL compatibility with
 * the existing frontend; the payload is the contract's `PersonasPayload`.
 */

import { respond } from "@/lib/source";

// Reads the filesystem (and a native SQLite addon) — never the edge runtime,
// and never cached: this is live agent state.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request): Promise<Response> {
  return respond(request, (source) => source.getPersonas());
}
