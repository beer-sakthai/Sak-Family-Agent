import fs from "fs";
import path from "path";
import {
  SpecKitConstitution,
  SpecKitData,
  SpecKitInitOptions,
  SpecKitIntegrationManifest,
  SpecKitIntegrationState,
  SpecKitTemplate,
  SpecKitUpstream,
  SpecKitWorkflow,
  SpecKitWorkflowStep,
} from "./types";

const UPSTREAM: SpecKitUpstream = {
  repoUrl: "https://github.com/github/spec-kit",
  license: "MIT",
  installCommand: "uv tool install specify-cli",
  minPython: "3.11+",
  requiredTools: ["Python 3.11+", "Git", "uv"],
  supportedIntegrations: [
    "GitHub Copilot",
    "Claude Code",
    "Gemini CLI",
    "Cursor",
    "opencode",
    "alquimia",
    "and 25+ more",
  ],
  commands: [
    { slash: "/speckit.constitution", purpose: "Establish project principles." },
    { slash: "/speckit.specify", purpose: "Define feature/bug requirements." },
    {
      slash: "/speckit.clarify",
      purpose: "Ask the user targeted clarifying questions on a draft spec.",
      optional: true,
    },
    { slash: "/speckit.plan", purpose: "Draft the technical implementation strategy." },
    { slash: "/speckit.tasks", purpose: "Break the plan into an ordered task list." },
    {
      slash: "/speckit.taskstoissues",
      purpose: "Push the task list into GitHub Issues.",
      optional: true,
    },
    {
      slash: "/speckit.analyze",
      purpose: "Analyze the codebase against the spec + plan.",
      optional: true,
    },
    {
      slash: "/speckit.checklist",
      purpose: "Generate a per-task acceptance checklist.",
      optional: true,
    },
    { slash: "/speckit.implement", purpose: "Execute the task list end-to-end." },
    {
      slash: "/speckit.converge",
      purpose: "Assess the codebase against spec + plan + tasks; report drift.",
    },
  ],
  layoutNote:
    "The .specify/ directory in this repo mirrors the upstream template pipeline: templates/ (core built-ins), workflows/ (composed cycles like Full SDD Cycle), integrations/ (per-agent adapters), memory/ (constitution). Overrides resolve at runtime as: overrides → presets → extensions → core.",
};

const DEFAULT_SPECKIT_DIR = path.resolve(process.cwd(), "..", "..", ".specify");

function resolveSpecKitDir(): string {
  const override = process.env.SPECKIT_DIR;
  if (override && override.trim().length > 0) return override;
  const candidates = [
    DEFAULT_SPECKIT_DIR,
    path.resolve(process.cwd(), ".specify"),
    path.resolve(process.cwd(), "..", ".specify"),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(/* turbopackIgnore: true */ c) && fs.statSync(/* turbopackIgnore: true */ c).isDirectory()) return c;
    } catch {
      // ignore
    }
  }
  return DEFAULT_SPECKIT_DIR;
}

function safeReadJson<T>(p: string): T | undefined {
  try {
    const raw = fs.readFileSync(p, "utf8");
    return JSON.parse(raw) as T;
  } catch {
    return undefined;
  }
}

function safeReadText(p: string): string | undefined {
  try {
    return fs.readFileSync(p, "utf8");
  } catch {
    return undefined;
  }
}

function toSnakeCamel(obj: any): any {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(toSnakeCamel);
  if (typeof obj !== "object") return obj;
  const out: Record<string, any> = {};
  for (const [k, v] of Object.entries(obj)) {
    const camel = k.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());
    out[camel] = toSnakeCamel(v);
  }
  return out;
}

function parseInitOptions(rootDir: string): SpecKitInitOptions | undefined {
  const raw = safeReadJson<Record<string, any>>(path.join(rootDir, "init-options.json"));
  if (!raw) return undefined;
  const camel = toSnakeCamel(raw);
  return {
    ai: String(camel.ai ?? ""),
    featureNumbering: String(camel.featureNumbering ?? ""),
    here: Boolean(camel.here),
    integration: String(camel.integration ?? ""),
    script: String(camel.script ?? ""),
    speckitVersion: String(camel.speckitVersion ?? ""),
  };
}

function parseIntegrationState(rootDir: string): SpecKitIntegrationState | undefined {
  const raw = safeReadJson<Record<string, any>>(path.join(rootDir, "integration.json"));
  if (!raw) return undefined;
  return {
    version: String(raw.version ?? ""),
    integrationStateSchema: Number(raw.integration_state_schema ?? 0),
    installedIntegrations: Array.isArray(raw.installed_integrations)
      ? raw.installed_integrations.map(String)
      : [],
    defaultIntegration: String(raw.default_integration ?? ""),
    currentIntegration: String(raw.integration ?? raw.default_integration ?? ""),
    integrationSettings:
      raw.integration_settings && typeof raw.integration_settings === "object"
        ? raw.integration_settings
        : {},
  };
}

function parseTemplates(rootDir: string): SpecKitTemplate[] {
  const templatesDir = path.join(rootDir, "templates");
  let entries: string[];
  try {
    entries = fs.readdirSync(templatesDir);
  } catch {
    return [];
  }
  const templates: SpecKitTemplate[] = [];
  for (const name of entries) {
    if (!name.endsWith(".md")) continue;
    const full = path.join(templatesDir, name);
    try {
      const stat = fs.statSync(full);
      const text = fs.readFileSync(full, "utf8");
      const lines = text.split("\n");
      const preview = lines.slice(0, 12).join("\n");
      templates.push({
        name,
        path: `.specify/templates/${name}`,
        bytes: stat.size,
        lines: lines.length,
        preview,
      });
    } catch {
      // skip
    }
  }
  return templates.sort((a, b) => a.name.localeCompare(b.name));
}

function parseIntegrations(rootDir: string): SpecKitIntegrationManifest[] {
  const integDir = path.join(rootDir, "integrations");
  let entries: string[];
  try {
    entries = fs.readdirSync(integDir);
  } catch {
    return [];
  }
  const manifests: SpecKitIntegrationManifest[] = [];
  for (const name of entries) {
    if (!name.endsWith(".manifest.json")) continue;
    const raw = safeReadJson<Record<string, any>>(path.join(integDir, name));
    if (!raw) continue;
    const files =
      raw.files && typeof raw.files === "object" && !Array.isArray(raw.files)
        ? Object.keys(raw.files)
        : [];
    manifests.push({
      integration: String(raw.integration ?? name.replace(".manifest.json", "")),
      version: String(raw.version ?? ""),
      installedAt: String(raw.installed_at ?? ""),
      fileCount: files.length,
      files,
    });
  }
  return manifests.sort((a, b) => a.integration.localeCompare(b.integration));
}

/**
 * Minimal YAML parser tailored to workflow.yml — this file's shape is
 * fixed (id/name/version/author/description at top level, requires block,
 * inputs map, steps list). Avoids adding a yaml dependency to the dashboard.
 */
function parseWorkflowYaml(yaml: string, fallbackId: string): SpecKitWorkflow {
  const meta: Record<string, string> = {};
  const inputs: SpecKitWorkflow["inputs"] = [];
  const steps: SpecKitWorkflowStep[] = [];

  const lines = yaml.split("\n").map((l) => l.replace(/\r$/, ""));
  let mode: "top" | "workflow" | "requires" | "inputs" | "steps" | "other" = "top";
  let currentInput: (typeof inputs)[number] | null = null;
  let currentStep: SpecKitWorkflowStep | null = null;
  let requiresSpeckit: string | undefined;

  const flushStep = () => {
    if (currentStep) {
      steps.push(currentStep);
      currentStep = null;
    }
  };
  const flushInput = () => {
    if (currentInput) {
      inputs.push(currentInput);
      currentInput = null;
    }
  };

  const stripQuotes = (v: string) => v.replace(/^["']/, "").replace(/["']$/, "");

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const trimmed = raw.trim();
    if (trimmed.length === 0 || trimmed.startsWith("#")) continue;
    const leading = raw.length - raw.trimStart().length;

    if (leading === 0) {
      flushStep();
      flushInput();
      if (trimmed === "workflow:") {
        mode = "workflow";
        continue;
      }
      if (trimmed === "requires:") {
        mode = "requires";
        continue;
      }
      if (trimmed === "inputs:") {
        mode = "inputs";
        continue;
      }
      if (trimmed === "steps:") {
        mode = "steps";
        continue;
      }
      const kv = trimmed.match(/^([\w_]+):\s*(.*)$/);
      if (kv) {
        meta[kv[1]] = stripQuotes(kv[2]);
      }
      mode = "top";
      continue;
    }

    if (mode === "workflow") {
      const kv = trimmed.match(/^([\w_]+):\s*(.*)$/);
      if (kv) meta[kv[1]] = stripQuotes(kv[2]);
      continue;
    }

    if (mode === "requires") {
      const kv = trimmed.match(/^([\w_]+):\s*(.*)$/);
      if (kv && kv[1] === "speckit_version") requiresSpeckit = stripQuotes(kv[2]);
      continue;
    }

    if (mode === "inputs") {
      if (leading === 2 && trimmed.endsWith(":")) {
        flushInput();
        currentInput = {
          name: trimmed.slice(0, -1),
          type: "string",
          required: false,
        };
        continue;
      }
      if (!currentInput) continue;
      const kv = trimmed.match(/^([\w_]+):\s*(.*)$/);
      if (!kv) continue;
      const key = kv[1];
      const val = stripQuotes(kv[2]);
      if (key === "type") currentInput.type = val;
      else if (key === "required") currentInput.required = val === "true";
      else if (key === "default") currentInput.default = val;
      else if (key === "prompt") currentInput.prompt = val;
      else if (key === "enum") {
        const inner = val.replace(/^\[/, "").replace(/\]$/, "");
        currentInput.enum = inner
          .split(",")
          .map((s) => stripQuotes(s.trim()))
          .filter((s) => s.length > 0);
      }
      continue;
    }

    if (mode === "steps") {
      if (trimmed.startsWith("- ")) {
        flushStep();
        currentStep = { id: "", kind: "other" };
        const rest = trimmed.slice(2).trim();
        const kv = rest.match(/^([\w_]+):\s*(.*)$/);
        if (kv) {
          if (kv[1] === "id") currentStep.id = stripQuotes(kv[2]);
        }
        continue;
      }
      if (!currentStep) continue;
      const kv = trimmed.match(/^([\w_]+):\s*(.*)$/);
      if (!kv) continue;
      const key = kv[1];
      const val = stripQuotes(kv[2]);
      if (key === "id") currentStep.id = val;
      else if (key === "command") {
        currentStep.command = val;
        currentStep.kind = "command";
      } else if (key === "type") {
        if (val === "gate") currentStep.kind = "gate";
      } else if (key === "message") currentStep.message = val;
      else if (key === "on_reject") currentStep.onReject = val;
      else if (key === "integration") currentStep.integration = val;
      else if (key === "options") {
        const inner = val.replace(/^\[/, "").replace(/\]$/, "");
        currentStep.options = inner
          .split(",")
          .map((s) => stripQuotes(s.trim()))
          .filter((s) => s.length > 0);
      }
    }
  }
  flushStep();
  flushInput();

  return {
    id: meta.id || fallbackId,
    name: meta.name || fallbackId,
    version: meta.version || "0.0.0",
    description: meta.description || "",
    author: meta.author,
    requiresSpeckitVersion: requiresSpeckit,
    inputs,
    steps,
    rawYaml: yaml,
  };
}

function parseWorkflows(rootDir: string): SpecKitWorkflow[] {
  const wfDir = path.join(rootDir, "workflows");
  const registry = safeReadJson<Record<string, any>>(
    path.join(wfDir, "workflow-registry.json")
  );
  let ids: string[] = [];
  if (registry && registry.workflows && typeof registry.workflows === "object") {
    ids = Object.keys(registry.workflows);
  } else {
    try {
      ids = fs
        .readdirSync(wfDir)
        .filter((n) => {
          try {
            return fs.statSync(path.join(wfDir, n)).isDirectory();
          } catch {
            return false;
          }
        });
    } catch {
      ids = [];
    }
  }

  const workflows: SpecKitWorkflow[] = [];
  for (const id of ids) {
    const yamlPath = path.join(wfDir, id, "workflow.yml");
    const yaml = safeReadText(yamlPath);
    let workflow: SpecKitWorkflow;
    if (yaml) {
      workflow = parseWorkflowYaml(yaml, id);
    } else {
      workflow = {
        id,
        name: id,
        version: "0.0.0",
        description: "",
        inputs: [],
        steps: [],
        rawYaml: "",
      };
    }
    const registryEntry = registry?.workflows?.[id];
    if (registryEntry && typeof registryEntry === "object") {
      workflow.installedAt = registryEntry.installed_at
        ? String(registryEntry.installed_at)
        : undefined;
      workflow.updatedAt = registryEntry.updated_at
        ? String(registryEntry.updated_at)
        : undefined;
      if (!workflow.name && registryEntry.name) workflow.name = String(registryEntry.name);
      if (!workflow.description && registryEntry.description) {
        workflow.description = String(registryEntry.description);
      }
      if (!workflow.version && registryEntry.version) {
        workflow.version = String(registryEntry.version);
      }
    }
    workflows.push(workflow);
  }
  return workflows;
}

function parseConstitution(rootDir: string): SpecKitConstitution | undefined {
  const p = path.join(rootDir, "memory", "constitution.md");
  const text = safeReadText(p);
  if (text === undefined) return undefined;
  const lines = text.split("\n");
  const isTemplate =
    text.includes("[PROJECT_NAME]") ||
    text.includes("[PRINCIPLE_1_NAME]") ||
    text.includes("[GOVERNANCE_RULES]");
  return {
    path: ".specify/memory/constitution.md",
    isTemplate,
    lines: lines.length,
    bytes: Buffer.byteLength(text, "utf8"),
    preview: lines.slice(0, 20).join("\n"),
  };
}

function parseScripts(rootDir: string): string[] {
  const bashDir = path.join(rootDir, "scripts", "bash");
  try {
    return fs
      .readdirSync(bashDir)
      .filter((n) => n.endsWith(".sh"))
      .sort();
  } catch {
    return [];
  }
}

export { UPSTREAM };

export function getSpecKitData(): SpecKitData {
  const rootDir = resolveSpecKitDir();
  const present = fs.existsSync(/* turbopackIgnore: true */ rootDir);
  if (!present) {
    return {
      present: false,
      rootPath: rootDir,
      workflows: [],
      integrations: [],
      templates: [],
      scripts: [],
      upstream: UPSTREAM,
    };
  }
  return {
    present: true,
    rootPath: rootDir,
    initOptions: parseInitOptions(rootDir),
    integrationState: parseIntegrationState(rootDir),
    workflows: parseWorkflows(rootDir),
    integrations: parseIntegrations(rootDir),
    templates: parseTemplates(rootDir),
    constitution: parseConstitution(rootDir),
    scripts: parseScripts(rootDir),
    upstream: UPSTREAM,
  };
}

export { parseWorkflowYaml };
