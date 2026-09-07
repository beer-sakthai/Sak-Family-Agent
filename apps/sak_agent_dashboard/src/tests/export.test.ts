import { describe, expect, it } from "vitest";

import { exportFilename, toCsv } from "@/lib/export";

describe("toCsv", () => {
  it("writes a header from the column list", () => {
    expect(toCsv([], ["a", "b"])).toBe("a,b");
  });

  it("writes one CRLF-separated row per record", () => {
    expect(toCsv([{ a: 1, b: 2 }], ["a", "b"])).toBe("a,b\r\n1,2");
  });

  it("follows the column order, not the object's key order", () => {
    expect(toCsv([{ b: 2, a: 1 }], ["a", "b"])).toBe("a,b\r\n1,2");
  });

  it("keeps columns aligned when a row is missing a field", () => {
    // The bug this guards: deriving columns from the first row's keys lets a
    // sparse later row shift every subsequent column left by one.
    expect(toCsv([{ a: 1 }, { a: 3, b: 4 }], ["a", "b"])).toBe("a,b\r\n1,\r\n3,4");
  });

  it("quotes a field containing a comma", () => {
    expect(toCsv([{ a: "x,y" }], ["a"])).toBe('a\r\n"x,y"');
  });

  it("doubles an embedded quote", () => {
    expect(toCsv([{ a: 'say "hi"' }], ["a"])).toBe('a\r\n"say ""hi"""');
  });

  it("quotes a field containing a newline", () => {
    expect(toCsv([{ a: "one\ntwo" }], ["a"])).toBe('a\r\n"one\ntwo"');
  });

  it("renders null and undefined as empty", () => {
    expect(toCsv([{ a: null, b: undefined }], ["a", "b"])).toBe("a,b\r\n,");
  });

  it("serialises an object field as JSON", () => {
    expect(toCsv([{ a: { k: 1 } }], ["a"])).toBe('a\r\n"{""k"":1}"');
  });

  it("serialises an array field as JSON", () => {
    expect(toCsv([{ a: ["x", "y"] }], ["a"])).toBe('a\r\n"[""x"",""y""]"');
  });

  it("renders a boolean plainly", () => {
    expect(toCsv([{ a: false }], ["a"])).toBe("a\r\nfalse");
  });
});

describe("exportFilename", () => {
  it("names the panel and dates the file", () => {
    expect(exportFilename("sessions", "csv", new Date("2026-08-27T10:00:00Z"))).toBe(
      "sak-sessions-2026-08-27.csv",
    );
  });

  it("uses the given extension", () => {
    expect(exportFilename("audit", "json", new Date("2026-01-02T00:00:00Z"))).toBe(
      "sak-audit-2026-01-02.json",
    );
  });
});
