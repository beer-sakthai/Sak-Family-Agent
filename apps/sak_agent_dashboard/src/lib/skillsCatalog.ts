import { SkillSpec, ToolGuardrailSpec, SkillsCatalogData } from "./types";

export const GUARDRAIL_RULES: ToolGuardrailSpec[] = [
  {
    name: "Credential & Secret Shield",
    category: "credentials",
    level: "deny",
    ruleDescription: "Blocks access to .ssh, .aws/credentials, .env, and API token environment variables.",
    blockedPatterns: ["*id_rsa*", "*.env", "*aws_access_key*", "*TOKEN*"],
  },
  {
    name: "Filesystem Isolation Guard",
    category: "filesystem",
    level: "deny",
    ruleDescription: "Restricts file writing strictly within the active workspace repository boundaries.",
    blockedPatterns: ["/etc/*", "/var/*", "/usr/*", "~/.ssh/*"],
  },
  {
    name: "Shell Command AST Gate",
    category: "ast",
    level: "allow",
    ruleDescription: "Enforces safe execution flags: checks `uv run`, `pnpm run`, `pytest`, and blocks `rm -rf /` or background fork bombs.",
    blockedPatterns: ["rm -rf /", ":(){ :|:& };:", "dd if="],
  },
  {
    name: "Network & Outbound Filter",
    category: "network",
    level: "prompt",
    ruleDescription: "Monitors outgoing web scraping requests and validates authorized Hugging Face/GitHub API endpoints.",
    blockedPatterns: ["*.onion", "*unverified-proxy*"],
  },
];

export const SKILLS_CATALOG: SkillSpec[] = [
  {
    slug: "repo-ops-pipeline",
    name: "Repo Ops & CI/CD Pipeline",
    description: "Standardized QA, typecheck, linting, and build preflight automation before submitting Pull Requests.",
    category: "automation",
    authorPersona: "SakJules",
    commandSnippet: "uv run pytest tests/ && pnpm run typecheck",
    requiredTools: ["run_command", "replace_file_content", "git_commit"],
    guardrailCount: 4,
  },
  {
    slug: "speckit.specify",
    name: "SpecKit Specification Authoring",
    description: "Creates structured, executable system architecture and requirements specifications.",
    category: "system",
    authorPersona: "SakThai",
    commandSnippet: "/speckit.specify <feature_name>",
    requiredTools: ["write_to_file", "view_file"],
    guardrailCount: 2,
  },
  {
    slug: "sentinel-guardrails",
    name: "Sentinel AST Guardrail Audit",
    description: "Deep AST parsing of Python and TypeScript code changes to prevent security regressions.",
    category: "system",
    authorPersona: "SakKing",
    commandSnippet: "python -m sakthai.agent.guardrails --audit",
    requiredTools: ["run_command", "view_file"],
    guardrailCount: 4,
  },
  {
    slug: "social-synthesis",
    name: "Multi-Persona Social Drafting",
    description: "Generates high-engagement documentation and release announcements across bilingual Thai-English channels.",
    category: "creative",
    authorPersona: "SakSit",
    commandSnippet: "sakthai run social-draft --persona saksit",
    requiredTools: ["write_to_file"],
    guardrailCount: 1,
  },
  {
    slug: "web-scout-eval",
    name: "Web Intelligence & Multimodal Scout",
    description: "Crawls upstream API documentation, inspects screenshot layouts, and flags broken UI links.",
    category: "research",
    authorPersona: "SakSee",
    commandSnippet: "sakthai run web-scout --url <target>",
    requiredTools: ["read_url_content", "browser_snapshot"],
    guardrailCount: 3,
  },
  {
    slug: "memory-sync-journal",
    name: "SQLite Memory Sync & Shard Journal",
    description: "Persists daily interaction facts into ~/.sakthai/memory.db with cross-persona consensus.",
    category: "system",
    authorPersona: "SakTan",
    commandSnippet: "sakthai memory sync --shard saktan",
    requiredTools: ["db_query", "write_to_file"],
    guardrailCount: 2,
  },
];

export function getSkillsCatalogData(): SkillsCatalogData {
  return {
    skills: SKILLS_CATALOG,
    guardrails: GUARDRAIL_RULES,
    totalSkills: SKILLS_CATALOG.length,
    totalTools: 28,
  };
}
