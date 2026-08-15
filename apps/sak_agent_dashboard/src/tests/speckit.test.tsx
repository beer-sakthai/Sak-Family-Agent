import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import fs from "fs";
import os from "os";
import path from "path";

import { GET as speckitGet } from "../app/api/speckit/route";
import { getSpecKitData, parseWorkflowYaml } from "../lib/speckit";
import SpecKitPanel from "../components/SpecKitPanel";

const SAMPLE_WORKFLOW = `schema_version: "1.0"
workflow:
  id: "speckit"
  name: "Full SDD Cycle"
  version: "1.0.0"
  author: "GitHub"
  description: "Runs specify → plan → tasks → implement with review gates"

requires:
  speckit_version: ">=0.8.5"

inputs:
  spec:
    type: string
    required: true
    prompt: "Describe what you want to build"
  scope:
    type: string
    default: "full"
    enum: ["full", "backend-only", "frontend-only"]

steps:
  - id: specify
    command: speckit.specify
    integration: "copilot"

  - id: review-spec
    type: gate
    message: "Review the generated spec before planning."
    options: [approve, reject]
    on_reject: abort

  - id: implement
    command: speckit.implement
    integration: "copilot"
`;

describe("SpecKit Feature Suite", () => {
  let tmpDir: string;
  const savedSpeckitDir = process.env.SPECKIT_DIR;

  beforeAll(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "speckit-test-"));
    fs.mkdirSync(path.join(tmpDir, "workflows", "speckit"), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, "integrations"), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, "templates"), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, "memory"), { recursive: true });
    fs.mkdirSync(path.join(tmpDir, "scripts", "bash"), { recursive: true });

    fs.writeFileSync(
      path.join(tmpDir, "init-options.json"),
      JSON.stringify({
        ai: "copilot",
        feature_numbering: "sequential",
        here: false,
        integration: "copilot",
        script: "sh",
        speckit_version: "0.15.1",
      })
    );
    fs.writeFileSync(
      path.join(tmpDir, "integration.json"),
      JSON.stringify({
        version: "0.15.1",
        integration_state_schema: 1,
        installed_integrations: ["copilot"],
        integration: "copilot",
        default_integration: "copilot",
        integration_settings: { copilot: { script: "sh" } },
      })
    );
    fs.writeFileSync(
      path.join(tmpDir, "workflows", "workflow-registry.json"),
      JSON.stringify({
        schema_version: "1.0",
        workflows: {
          speckit: {
            name: "Full SDD Cycle",
            version: "1.0.0",
            description: "Runs specify → plan → tasks → implement with review gates",
            installed_at: "2026-08-02T08:24:44.201036+00:00",
          },
        },
      })
    );
    fs.writeFileSync(
      path.join(tmpDir, "workflows", "speckit", "workflow.yml"),
      SAMPLE_WORKFLOW
    );
    fs.writeFileSync(
      path.join(tmpDir, "integrations", "copilot.manifest.json"),
      JSON.stringify({
        integration: "copilot",
        version: "0.15.1",
        installed_at: "2026-08-02T08:24:43.230082+00:00",
        files: {
          ".github/agents/speckit.specify.agent.md": "abc",
          ".github/prompts/speckit.specify.prompt.md": "def",
        },
      })
    );
    fs.writeFileSync(
      path.join(tmpDir, "templates", "spec-template.md"),
      "# Feature Specification\n\nDescribe the feature.\n"
    );
    fs.writeFileSync(
      path.join(tmpDir, "templates", "plan-template.md"),
      "# Plan\n\nOutline the plan.\n"
    );
    fs.writeFileSync(
      path.join(tmpDir, "memory", "constitution.md"),
      "# [PROJECT_NAME] Constitution\n\n[PRINCIPLE_1_NAME]\n"
    );
    fs.writeFileSync(
      path.join(tmpDir, "scripts", "bash", "create-new-feature.sh"),
      "#!/usr/bin/env bash\nexit 0\n"
    );

    process.env.SPECKIT_DIR = tmpDir;
  });

  afterAll(() => {
    if (savedSpeckitDir === undefined) delete process.env.SPECKIT_DIR;
    else process.env.SPECKIT_DIR = savedSpeckitDir;
    try {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    } catch {
      // ignore
    }
  });

  describe("parseWorkflowYaml", () => {
    it("extracts id, name, version, description, requires, inputs, and steps", () => {
      const wf = parseWorkflowYaml(SAMPLE_WORKFLOW, "speckit");
      expect(wf.id).toBe("speckit");
      expect(wf.name).toBe("Full SDD Cycle");
      expect(wf.version).toBe("1.0.0");
      expect(wf.requiresSpeckitVersion).toBe(">=0.8.5");
      expect(wf.inputs.length).toBe(2);
      const specInput = wf.inputs.find((i) => i.name === "spec");
      expect(specInput?.required).toBe(true);
      const scopeInput = wf.inputs.find((i) => i.name === "scope");
      expect(scopeInput?.enum).toEqual(["full", "backend-only", "frontend-only"]);
      expect(wf.steps.length).toBe(3);
      expect(wf.steps[0].kind).toBe("command");
      expect(wf.steps[0].command).toBe("speckit.specify");
      expect(wf.steps[1].kind).toBe("gate");
      expect(wf.steps[1].options).toEqual(["approve", "reject"]);
      expect(wf.steps[1].onReject).toBe("abort");
    });
  });

  describe("getSpecKitData + /api/speckit", () => {
    it("returns a fully populated SpecKit snapshot", async () => {
      const data = getSpecKitData();
      expect(data.present).toBe(true);
      expect(data.rootPath).toBe(tmpDir);
      expect(data.initOptions?.speckitVersion).toBe("0.15.1");
      expect(data.integrationState?.installedIntegrations).toEqual(["copilot"]);
      expect(data.workflows.length).toBe(1);
      expect(data.workflows[0].id).toBe("speckit");
      expect(data.workflows[0].steps.length).toBe(3);
      expect(data.integrations.length).toBe(1);
      expect(data.integrations[0].fileCount).toBe(2);
      expect(data.templates.map((t) => t.name).sort()).toEqual([
        "plan-template.md",
        "spec-template.md",
      ]);
      expect(data.constitution?.isTemplate).toBe(true);
      expect(data.scripts).toContain("create-new-feature.sh");

      const res = await speckitGet();
      expect(res.status).toBe(200);
      const json = await res.json();
      expect(json.success).toBe(true);
      expect(json.speckit.workflows[0].id).toBe("speckit");
    });

    it("returns present=false when SPECKIT_DIR points nowhere", async () => {
      const prev = process.env.SPECKIT_DIR;
      process.env.SPECKIT_DIR = path.join(tmpDir, "does-not-exist-xyz");
      try {
        const data = getSpecKitData();
        expect(data.present).toBe(false);
        expect(data.workflows).toEqual([]);
        expect(data.templates).toEqual([]);
      } finally {
        process.env.SPECKIT_DIR = prev;
      }
    });
  });

  describe("<SpecKitPanel /> component", () => {
    it("renders the SpecKit dashboard with workflow, integration, and template sections", () => {
      const data = getSpecKitData();
      render(<SpecKitPanel data={data} />);
      expect(screen.getAllByText(/SpecKit/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Full SDD Cycle/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/specify/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/review-spec/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/review gate/i).length).toBeGreaterThan(0);
      expect(screen.getByText("spec-template.md")).toBeInTheDocument();
      expect(screen.getByText(/init-options.json/i)).toBeInTheDocument();
      // Constitution should be flagged as a template
      expect(screen.getAllByText(/Template/i).length).toBeGreaterThan(0);
    });

    it("renders the empty state when data is absent", () => {
      render(
        <SpecKitPanel
          data={{
            present: false,
            rootPath: "/tmp/nowhere",
            workflows: [],
            integrations: [],
            templates: [],
            scripts: [],
            upstream: {
              repoUrl: "https://github.com/github/spec-kit",
              license: "MIT",
              installCommand: "uv tool install specify-cli",
              minPython: "3.11+",
              requiredTools: [],
              supportedIntegrations: [],
              commands: [],
              layoutNote: "",
            },
          }}
        />
      );
      expect(screen.getByText(/No SpecKit installation detected/i)).toBeInTheDocument();
      expect(screen.getByText(/\/tmp\/nowhere/)).toBeInTheDocument();
    });
  });
});
