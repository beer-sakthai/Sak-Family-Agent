import fs from "fs";
import path from "path";
import { DesignSpec, DesignSpecsData, SpecStatus } from "./types";

function resolveRepoRoot(): string {
  const override = process.env.SAK_REPO_ROOT;
  if (override && override.trim().length > 0) return override;
  // `turbopackIgnore` on the traversals: without it Turbopack's static analysis
  // sees an unbounded `process.cwd()/..` and traces the *entire monorepo* into
  // every serverless function (121 MB locally — `personas/` and the vendored
  // M365 SDK included). The files these readers actually need are declared
  // explicitly by `outputFileTracingIncludes` in `next.config.mjs`.
  const candidates = [
    path.resolve(/* turbopackIgnore: true */ process.cwd(), "..", ".."),
    path.resolve(/* turbopackIgnore: true */ process.cwd(), ".."),
    process.cwd(),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(path.join(c, "docs", "superpowers", "specs"))) return c;
    } catch {
      // ignore
    }
  }
  return path.resolve(/* turbopackIgnore: true */ process.cwd(), "..", "..");
}

/** Hand-written one-liners; the spec files themselves are long design docs. */
const SUMMARIES: Record<string, { summary: string; relatedTab?: string }> = {
  "2026-07-02-phase4-memory-session-search-design.md": {
    summary:
      "Audits the memory/session architecture and closes the 'no way to search across past session content' gap by adding session search as both a CLI command and an agent tool — without changing MemoryStore's schema or scope.",
    relatedTab: "Memory & Security Logs",
  },
  "2026-07-07-sakthai-chat-cli-design.md": {
    summary:
      "Adds `sakthai chat`: an interactive multi-turn REPL with any of the six personas, styled close to the real claude CLI — colored turns, visible tool-call activity, streaming replies, input history. First of two specs toward 'personas at Claude-Code-level capability'.",
    relatedTab: "Session Explorer",
  },
  "2026-07-08-sak-family-auto-cycle-design.md": {
    summary:
      "Two composing skills: one lets a persona sustain multiple Dream→Growth rounds in a single `sakthai run` (capped at 3), the other fans out to all six personas in parallel from a Claude Code session. No changes to the Python package — both deliverables are SKILL.md documents.",
    relatedTab: "Auto-Cycle",
  },
  "2026-08-03-cowork-plugin-design.md": {
    summary:
      "The reverse integration leg: instead of pulling data out of Copilot (structurally blocked for personal M365 accounts), Copilot Cowork calls into MCP servers we host. Covers a memory connector, a Teams connector, and a self-hosted OAuth 2.0 vault — all isolated from sakthai's CI-gated core.",
    relatedTab: "M365 Copilot",
  },
  "2026-08-03-sakthai-web-auth-design.md": {
    summary:
      "Technical shape of Web API Authentication (security Fix #2): bearer token stored as a `web_auth` fact, every path except /health requiring it, and the gaps found on re-read of web/server.py. Since implemented — see the web/server.py notes in CLAUDE.md.",
    relatedTab: "Memory & Security Logs",
  },
  "2026-08-05-m365-copilot-studio-provider-design.md": {
    summary:
      "Adds a sixth chat provider, `--provider copilotstudio`, backed by a Copilot Studio agent via the Bot Framework Connector API with app-only Entra auth. Deliberately msal-only — no bot-framework or M365 Agents SDK dependency, matching the repo's thin-httpx provider pattern.",
    relatedTab: "M365 Copilot",
  },
  "2026-08-05-onedrive-contacts-graph-tools-design.md": {
    summary:
      "Extends the existing four Graph tools' plumbing (_graph_access_token / _graph_request / _graph_safe) with two more surfaces: OneDrive read+write (sandboxed) and Contacts lookup. Teams was explicitly deferred to its own follow-up design.",
    relatedTab: "MCP Servers",
  },
};

function classifyStatus(raw: string): SpecStatus {
  const s = raw.toLowerCase();
  if (s.includes("implemented")) return "implemented";
  if (s.includes("approved")) return "approved";
  if (s.includes("draft")) return "draft";
  return "unknown";
}

function parseTitle(text: string, fallback: string): string {
  const m = text.match(/^#\s+(.+)$/m);
  return m ? m[1].trim() : fallback;
}

function parseStatusRaw(text: string): string {
  const m = text.match(/^\*\*Status:\*\*\s*(.+)$/m);
  return m ? m[1].trim() : "";
}

function parseDateFromFilename(file: string): string {
  const m = file.match(/^(\d{4}-\d{2}-\d{2})-/);
  return m ? m[1] : "";
}

function findPlanFile(repoRoot: string, specFile: string): string | undefined {
  // A spec `<date>-<slug>-design.md` pairs with a plan `<date>-<slug>.md`.
  const planName = specFile.replace(/-design\.md$/, ".md");
  const planPath = path.join(repoRoot, "docs", "superpowers", "plans", planName);
  try {
    if (fs.existsSync(planPath)) return `docs/superpowers/plans/${planName}`;
  } catch {
    // ignore
  }
  return undefined;
}

export function getDesignSpecsData(): DesignSpecsData {
  const repoRoot = resolveRepoRoot();
  const specsDir = path.join(repoRoot, "docs", "superpowers", "specs");
  const plansDir = path.join(repoRoot, "docs", "superpowers", "plans");

  let entries: string[];
  try {
    entries = fs.readdirSync(specsDir).filter((f) => f.endsWith(".md"));
  } catch {
    return {
      present: false,
      specsDir: "docs/superpowers/specs",
      plansDir: "docs/superpowers/plans",
      specs: [],
    };
  }

  const specs: DesignSpec[] = [];
  for (const file of entries) {
    const full = path.join(specsDir, file);
    let text = "";
    let bytes = 0;
    try {
      text = fs.readFileSync(full, "utf8");
      bytes = fs.statSync(full).size;
    } catch {
      continue;
    }
    const statusRaw = parseStatusRaw(text);
    const meta = SUMMARIES[file];
    specs.push({
      id: file.replace(/\.md$/, ""),
      file: `docs/superpowers/specs/${file}`,
      title: parseTitle(text, file),
      date: parseDateFromFilename(file),
      status: classifyStatus(statusRaw),
      statusRaw: statusRaw || "(no status line)",
      summary: meta?.summary ?? "",
      planFile: findPlanFile(repoRoot, file),
      relatedTab: meta?.relatedTab,
      bytes,
    });
  }

  // Newest first.
  specs.sort((a, b) => b.date.localeCompare(a.date) || a.file.localeCompare(b.file));

  return {
    present: true,
    specsDir: "docs/superpowers/specs",
    plansDir: "docs/superpowers/plans",
    specs,
  };
}
