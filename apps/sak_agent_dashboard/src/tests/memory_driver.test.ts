import { describe, expect, it, afterEach } from "vitest";

import {
  memoryDriverError,
  probeMemoryDriver,
  _resetMemoryDriverProbe,
} from "@/lib/db";

afterEach(() => {
  _resetMemoryDriverProbe();
});

describe("probeMemoryDriver", () => {
  it("reports no error when the native driver loads", () => {
    // The dashboard's entire live-data path depends on this module being
    // buildable in the deployment environment.
    expect(probeMemoryDriver()).toBeNull();
  });

  it("names the module and the ABI cause when the driver is missing", () => {
    // A deployment that installs cleanly but cannot compile better-sqlite3
    // keeps serving with every shard empty, which reads as "idle" rather than
    // "broken". The message has to say which module failed and why.
    const error = probeMemoryDriver(() => {
      throw new Error("invalid ELF header");
    });

    expect(error).not.toBeNull();
    expect(error).toContain("better-sqlite3");
    expect(error).toContain("Node major");
    expect(error).toContain("invalid ELF header");
  });

  it("survives a loader that throws a non-Error", () => {
    expect(probeMemoryDriver(() => {
      throw "boom";
    })).toContain("boom");
  });
});

describe("memoryDriverError", () => {
  it("caches the probe rather than re-requiring on every shard read", () => {
    const first = memoryDriverError();
    expect(memoryDriverError()).toBe(first);
  });
});
