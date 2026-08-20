import fs from "fs";
import path from "path";

export interface DocArticle {
  slug: string;
  title: string;
  content: string;
  relativePath: string;
}

export function resolveRepoRoot(): string {
  const override = process.env.SAK_REPO_ROOT;
  if (override && override.trim().length > 0) return override;
  const candidates = [
    path.resolve(process.cwd(), "..", ".."),
    path.resolve(process.cwd(), ".."),
    process.cwd(),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(path.join(c, "docs"))) return c;
    } catch {
      // ignore
    }
  }
  return path.resolve(process.cwd(), "..", "..");
}

export function getAllDocSlugs(): string[] {
  const repoRoot = resolveRepoRoot();
  const docsDir = path.join(repoRoot, "docs");
  if (!fs.existsSync(docsDir)) return [];

  try {
    const entries = fs.readdirSync(docsDir, { withFileTypes: true });
    return entries
      .filter((e) => e.isFile() && e.name.endsWith(".md"))
      .map((e) => e.name.replace(/\.md$/, ""));
  } catch {
    return [];
  }
}

export function getDocBySlug(slug: string): DocArticle | null {
  // Disallow invalid characters, path traversal segments
  if (!/^[a-zA-Z0-9_\-]+$/.test(slug)) {
    return null;
  }

  const repoRoot = resolveRepoRoot();
  const docsDir = path.resolve(repoRoot, "docs");
  const targetFile = path.resolve(docsDir, `${slug}.md`);

  // Defense-in-depth: path traversal containment check
  if (!targetFile.startsWith(docsDir + path.sep)) {
    return null;
  }

  if (!fs.existsSync(targetFile)) {
    return null;
  }

  try {
    const content = fs.readFileSync(targetFile, "utf-8");
    // Extract title from first heading if present
    const firstLine = content.split("\n").find((l) => l.startsWith("# "));
    const title = firstLine ? firstLine.replace(/^#\s+/, "").trim() : slug;

    return {
      slug,
      title,
      content,
      relativePath: `docs/${slug}.md`,
    };
  } catch {
    return null;
  }
}
