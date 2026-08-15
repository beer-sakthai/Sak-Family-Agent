import { describe, it, expect } from "vitest";
import { getAllDocSlugs, getDocBySlug } from "@/lib/docs";
import { GET as getDocsRoute } from "@/app/api/docs/[page]/route";
import { NextRequest } from "next/server";

describe("Docs Dynamic Route & Resolution", () => {
  it("discovers markdown files in docs/ including best-practices", () => {
    const slugs = getAllDocSlugs();
    expect(slugs).toContain("best-practices");
    expect(slugs).toContain("architecture");
  });

  it("resolves /docs/best-practices content correctly", () => {
    const doc = getDocBySlug("best-practices");
    expect(doc).not.toBeNull();
    expect(doc?.slug).toBe("best-practices");
    expect(doc?.title).toContain("Engineering Best Practices");
    expect(doc?.content).toContain("House of Sak");
    expect(doc?.relativePath).toBe("docs/best-practices.md");
  });

  it("returns null for non-existent document slugs", () => {
    const doc = getDocBySlug("non-existent-article-xyz-987");
    expect(doc).toBeNull();
  });

  it("blocks directory traversal attempts safely", () => {
    const doc = getDocBySlug("../../etc/passwd");
    expect(doc).toBeNull();

    const doc2 = getDocBySlug("../package.json");
    expect(doc2).toBeNull();
  });

  it("serves GET /api/docs/:page successfully via API route", async () => {
    const req = new NextRequest("http://localhost:3000/api/docs/best-practices");
    const response = await getDocsRoute(req, {
      params: Promise.resolve({ page: "best-practices" }),
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.doc.slug).toBe("best-practices");
    expect(data.doc.title).toContain("Engineering Best Practices");
  });

  it("returns 404 from API route for unknown doc slug", async () => {
    const req = new NextRequest("http://localhost:3000/api/docs/unknown-slug-404");
    const response = await getDocsRoute(req, {
      params: Promise.resolve({ page: "unknown-slug-404" }),
    });

    expect(response.status).toBe(404);
    const data = await response.json();
    expect(data.success).toBe(false);
  });
});
