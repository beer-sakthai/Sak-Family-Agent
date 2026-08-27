/**
 * Path resolution, the source-selection rule, and query-param clamping.
 *
 * The selection rule is the load-bearing piece of the hybrid design: which of
 * local / api / demo answers a request, and — just as important — that the
 * answer is reported back rather than guessed at by the client.
 */

import { afterEach, beforeEach, describe, expect, it } from "vitest";
import fs from "fs";
import os from "os";
import path from "path";

import { PERSONA_NAMES } from "@/lib/contracts.generated";
import { displayName, runtimeAvailable, runtimeRoots, sakthaiHome } from "@/lib/runtime";
import { envelope, intParam, resolveSource } from "@/lib/source";
import { makeHome, removeHome } from "./fixtures";

const ENV_KEYS = ["SAKTHAI_HOME", "SAKTHAI_DIR", "SAKTHAI_API_URL", "SAKTHAI_API_TOKEN"];
let saved: Record<string, string | undefined>;

beforeEach(() => {
  saved = Object.fromEntries(ENV_KEYS.map((key) => [key, process.env[key]]));
  for (const key of ENV_KEYS) delete process.env[key];
});

afterEach(() => {
  for (const key of ENV_KEYS) {
    if (saved[key] === undefined) delete process.env[key];
    else process.env[key] = saved[key];
  }
});

describe("sakthaiHome", () => {
  it("prefers SAKTHAI_HOME, matching the Python package", () => {
    process.env.SAKTHAI_HOME = "/tmp/from-home";
    expect(sakthaiHome()).toBe("/tmp/from-home");
  });

  it("still accepts the deprecated SAKTHAI_DIR alias", () => {
    process.env.SAKTHAI_DIR = "/tmp/from-dir";
    expect(sakthaiHome()).toBe("/tmp/from-dir");
  });

  it("prefers SAKTHAI_HOME when both are set", () => {
    process.env.SAKTHAI_HOME = "/tmp/wins";
    process.env.SAKTHAI_DIR = "/tmp/loses";
    expect(sakthaiHome()).toBe("/tmp/wins");
  });

  it("falls back to ~/.sakthai", () => {
    expect(sakthaiHome()).toBe(path.join(os.homedir(), ".sakthai"));
  });

  it("treats a blank value as unset", () => {
    process.env.SAKTHAI_HOME = "   ";
    expect(sakthaiHome()).toBe(path.join(os.homedir(), ".sakthai"));
  });
});

describe("runtimeRoots", () => {
  it("puts the unscoped root first, attributed to nobody", () => {
    expect(runtimeRoots("/tmp/x")[0]).toEqual({ persona: null, path: "/tmp/x" });
  });

  it("adds one root per persona", () => {
    expect(runtimeRoots("/tmp/x")).toHaveLength(PERSONA_NAMES.length + 1);
  });
});

describe("runtimeAvailable", () => {
  it("is false for a path that does not exist", () => {
    expect(runtimeAvailable("/nope/definitely/not/here")).toBe(false);
  });

  it("is true for a real directory", () => {
    const home = makeHome();
    try {
      expect(runtimeAvailable(home)).toBe(true);
    } finally {
      removeHome(home);
    }
  });

  it("is false for a file that is not a directory", () => {
    const file = path.join(os.tmpdir(), `not-a-dir-${Date.now()}`);
    fs.writeFileSync(file, "x");
    try {
      expect(runtimeAvailable(file)).toBe(false);
    } finally {
      fs.rmSync(file);
    }
  });
});

describe("displayName", () => {
  it.each(PERSONA_NAMES)("renders %s", (persona) => {
    const rendered = displayName(persona);
    expect(rendered.startsWith("Sak")).toBe(true);
    expect(rendered.toLowerCase()).toBe(persona);
  });
});

describe("intParam", () => {
  it("parses a valid value", () => {
    expect(intParam("7", 20, 1, 100)).toBe(7);
  });

  it("falls back for a missing value", () => {
    expect(intParam(null, 20, 1, 100)).toBe(20);
  });

  it("falls back for a blank value", () => {
    expect(intParam("  ", 20, 1, 100)).toBe(20);
  });

  it("falls back for a non-numeric value rather than producing NaN", () => {
    // `?limit=abc` used to reach `slice(0, NaN)` and silently return an empty
    // page with a 200 status.
    expect(intParam("abc", 20, 1, 100)).toBe(20);
  });

  it("clamps below the minimum", () => {
    expect(intParam("-5", 20, 1, 100)).toBe(1);
  });

  it("clamps above the maximum", () => {
    expect(intParam("100000", 20, 1, 100)).toBe(100);
  });
});

describe("envelope", () => {
  it("carries the source", () => {
    expect(envelope({ x: 1 }, "demo").source).toBe("demo");
  });

  it("stamps an ISO time", () => {
    expect(envelope({}, "local").generated_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });
});

function request(url: string): Request {
  return new Request(url);
}

describe("resolveSource", () => {
  it("returns the demo source when ?demo=1", async () => {
    const source = await resolveSource(request("http://x/api/agents?demo=1"));
    expect(source.kind).toBe("demo");
  });

  it("accepts ?demo=true too", async () => {
    const source = await resolveSource(request("http://x/api/agents?demo=true"));
    expect(source.kind).toBe("demo");
  });

  it("uses the API source when SAKTHAI_API_URL is set", async () => {
    process.env.SAKTHAI_API_URL = "http://127.0.0.1:3001";
    const source = await resolveSource(request("http://x/api/agents"));
    expect(source.kind).toBe("api");
  });

  it("prefers an explicit demo request over the API", async () => {
    process.env.SAKTHAI_API_URL = "http://127.0.0.1:3001";
    const source = await resolveSource(request("http://x/api/agents?demo=1"));
    expect(source.kind).toBe("demo");
  });

  it("uses the local source when a runtime directory exists", async () => {
    const home = makeHome();
    process.env.SAKTHAI_HOME = home;
    try {
      const source = await resolveSource(request("http://x/api/agents"));
      expect(source.kind).toBe("local");
    } finally {
      removeHome(home);
    }
  });

  it("degrades to demo only when the runtime is genuinely absent", async () => {
    process.env.SAKTHAI_HOME = "/nope/not/here";
    const source = await resolveSource(request("http://x/api/agents"));
    expect(source.kind).toBe("demo");
  });

  it("ignores a blank SAKTHAI_API_URL", async () => {
    process.env.SAKTHAI_API_URL = "  ";
    process.env.SAKTHAI_HOME = "/nope/not/here";
    const source = await resolveSource(request("http://x/api/agents"));
    expect(source.kind).toBe("demo");
  });
});
