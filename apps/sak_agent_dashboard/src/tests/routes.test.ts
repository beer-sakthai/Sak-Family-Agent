/**
 * The real route handlers, imported directly and called.
 *
 * No escape hatch. The previous suite wrapped every assertion in
 * `if (module loaded) … else assert-on-an-inline-literal`, so it reported green
 * when the import failed — testing its own fixtures rather than the routes.
 * Here an import failure is a test failure, which is the point.
 */

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { GET as agentsGET } from "@/app/api/agents/route";
import { GET as healthGET } from "@/app/api/health/route";
import { GET as auditGET } from "@/app/api/audit/route";
import { GET as memoryGET } from "@/app/api/memory/route";
import { GET as metricsGET } from "@/app/api/metrics/route";
import { GET as sessionsGET } from "@/app/api/sessions/route";
import { GET as workflowsGET } from "@/app/api/workflows/route";
import type { ApiEnvelope } from "@/lib/contracts.generated";
import { clearSessionCache } from "@/lib/sources/local";
import { makeHome, removeHome, seedHome, NOW } from "./fixtures";

type Handler = (request: Request) => Promise<Response>;

const ROUTES: [string, Handler][] = [
  ["agents", agentsGET],
  ["metrics", metricsGET],
  ["sessions", sessionsGET],
  ["memory", memoryGET],
  ["audit", auditGET],
  ["workflows", workflowsGET],
];

let home: string;
let savedHome: string | undefined;

beforeEach(() => {
  savedHome = process.env.SAKTHAI_HOME;
  home = makeHome();
  seedHome(home);
  process.env.SAKTHAI_HOME = home;
  delete process.env.SAKTHAI_API_URL;
  clearSessionCache();
});

afterEach(() => {
  removeHome(home);
  if (savedHome === undefined) delete process.env.SAKTHAI_HOME;
  else process.env.SAKTHAI_HOME = savedHome;
});

async function call<T>(handler: Handler, url: string): Promise<ApiEnvelope<T>> {
  const response = await handler(new Request(url));
  expect(response.status).toBe(200);
  return (await response.json()) as ApiEnvelope<T>;
}

describe("every route", () => {
  it.each(ROUTES)("%s returns a well-formed envelope", async (_name, handler) => {
    const body = await call(handler, "http://x/api/route");
    expect(body.ok).toBe(true);
    expect(body.generated_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(body).toHaveProperty("data");
  });

  it.each(ROUTES)("%s reports the local source against a real runtime", async (_n, handler) => {
    expect((await call(handler, "http://x/api/route")).source).toBe("local");
  });

  it.each(ROUTES)("%s reports the demo source when asked", async (_n, handler) => {
    expect((await call(handler, "http://x/api/route?demo=1")).source).toBe("demo");
  });
});

describe("/api/agents", () => {
  it("lists all six personas", async () => {
    const body = await call<{ personas: unknown[] }>(agentsGET, "http://x/api/agents");
    expect(body.data.personas).toHaveLength(6);
  });

  it("reports unattributed runs separately", async () => {
    const body = await call<{ unattributed_runs: number }>(agentsGET, "http://x/api/agents");
    expect(body.data.unattributed_runs).toBe(1);
  });
});

describe("/api/sessions", () => {
  it("returns the seeded session", async () => {
    const body = await call<{ total: number }>(sessionsGET, "http://x/api/sessions");
    expect(body.data.total).toBe(1);
  });

  it("does not 500 or empty out on a non-numeric limit", async () => {
    const body = await call<{ sessions: unknown[] }>(
      sessionsGET,
      "http://x/api/sessions?limit=abc",
    );
    expect(body.data.sessions).toHaveLength(1);
  });

  it("honours ?id= with a transcript", async () => {
    const body = await call<{ detail: { result_text: string } | null }>(
      sessionsGET,
      `http://x/api/sessions?id=${NOW}_abc`,
    );
    expect(body.data.detail?.result_text).toBe("done");
  });

  it("returns a null detail for a traversal id", async () => {
    const body = await call<{ detail: unknown }>(
      sessionsGET,
      "http://x/api/sessions?id=../../etc/passwd",
    );
    expect(body.data.detail).toBeNull();
  });

  it("accepts the legacy ?query= alias", async () => {
    const body = await call<{ total: number }>(sessionsGET, "http://x/api/sessions?query=thing");
    expect(body.data.total).toBe(1);
  });
});

describe("/api/audit", () => {
  it("applies the severity filter server-side", async () => {
    const body = await call<{ total: number }>(auditGET, "http://x/api/audit?severity=high");
    expect(body.data.total).toBe(1);
  });

  it("narrows an unknown severity to nothing", async () => {
    const body = await call<{ total: number }>(auditGET, "http://x/api/audit?severity=bogus");
    expect(body.data.total).toBe(0);
  });
});

describe("/api/memory", () => {
  it("returns facts from the seeded shard", async () => {
    const body = await call<{ total_facts: number }>(memoryGET, "http://x/api/memory");
    expect(body.data.total_facts).toBe(1);
  });

  it("applies a query", async () => {
    const body = await call<{ facts: unknown[] }>(memoryGET, "http://x/api/memory?query=nomatch");
    expect(body.data.facts).toHaveLength(0);
  });
});

describe("/api/workflows", () => {
  it("lists runs", async () => {
    const body = await call<{ runs: unknown[] }>(workflowsGET, "http://x/api/workflows");
    expect(body.data.runs).toHaveLength(1);
  });

  it("switches to detail with ?id=", async () => {
    const body = await call<{ steps: unknown[] } | null>(
      workflowsGET,
      "http://x/api/workflows?id=run-1",
    );
    expect(body.data?.steps).toHaveLength(2);
  });

  it("returns null for an unknown run", async () => {
    const body = await call<unknown>(workflowsGET, "http://x/api/workflows?id=nope");
    expect(body.data).toBeNull();
  });
});

describe("failure handling", () => {
  it("returns 500 rather than substituting demo data", async () => {
    // A runtime root that exists but whose contents cannot be read: the route
    // must report the failure, not quietly serve fiction.
    process.env.SAKTHAI_API_URL = "http://127.0.0.1:1"; // nothing listening
    const response = await agentsGET(new Request("http://x/api/agents"));
    expect(response.status).toBe(500);
    const body = (await response.json()) as { ok: boolean };
    expect(body.ok).toBe(false);
  });
});

describe("GET /api/health", () => {
  async function health(url = "http://localhost/api/health") {
    const response = await healthGET(new Request(url));
    return { response, body: await response.json() };
  }

  it("answers 200 with the source that would serve a data request", async () => {
    const { response, body } = await health();
    expect(response.status).toBe(200);
    expect(body.ok).toBe(true);
    expect(body.source).toBe("local");
    expect(body.configuration.live).toBe(true);
  });

  it("reports a demo fallback as up but not live", async () => {
    // The hosted case: no runtime directory, no API URL configured. A working
    // deployment showing sample data is not a failure, so it is still a 200.
    process.env.SAKTHAI_HOME = `${home}-does-not-exist`;
    const { response, body } = await health();
    expect(response.status).toBe(200);
    expect(body.source).toBe("demo");
    expect(body.configuration.live).toBe(false);
    expect(body.configuration.api_url_configured).toBe(false);
  });

  it("says an API is configured without disclosing it", async () => {
    process.env.SAKTHAI_API_URL = "https://agents.example.com";
    process.env.SAKTHAI_API_TOKEN = "s3cret";
    try {
      const { body } = await health();
      expect(body.configuration.api_url_configured).toBe(true);
      expect(body.configuration.api_token_configured).toBe(true);
      // The probe is readable by anyone who can reach the deployment.
      expect(JSON.stringify(body)).not.toContain("agents.example.com");
      expect(JSON.stringify(body)).not.toContain("s3cret");
    } finally {
      delete process.env.SAKTHAI_API_URL;
      delete process.env.SAKTHAI_API_TOKEN;
    }
  });

  it("carries a timestamp, so a cached answer is visible as one", async () => {
    const { body } = await health();
    expect(Number.isNaN(Date.parse(body.generated_at))).toBe(false);
  });
});
