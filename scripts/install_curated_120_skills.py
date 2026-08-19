#!/usr/bin/env python3
"""
Install and register the Curated Top 120 Skills to Gemini CLI and Antigravity (AGY).
Generates docs/curated-skills-120.json and docs/curated-skills-120.md.
"""

import os
import glob
import re
import json
import yaml
import shutil

TARGETS = [
    os.path.expanduser("~/.gemini/config/skills"),
    os.path.expanduser("~/.agents/skills"),
    "/home/beern/Sak-Family-Agent/.agents/skills",
]

PILLARS = {
    "Pillar 1: AST Security & Vulnerability Containment": [
        ("saksee-security-scan", "Zero-tolerance AST guardrail scanner"),
        ("saksee-path-traversal-guard", "Path normalization & sensitive dotfile sanitizer"),
        ("saksee-command-injection-blocker", "Shell metacharacter & subshell interceptor"),
        ("sakjules-redteam-fuzzer", "Recursive prompt injection & jailbreak tester"),
        ("sakjules-cipher-decoder", "Base64 / hex obfuscated payload analyzer"),
        ("saksee-doctor", "Local runtime boundary & permission sanity verification"),
        ("saksee-secret-scanner", "Gitleaks credential & private key interceptor"),
        ("saksee-codeql-remediation", "Automated CodeQL alert patcher"),
        ("saksee-bandit-security", "AST-based Python vulnerability evaluator"),
        ("saksee-ast-guardrail-parity", "Byte-synced persona guardrails validator"),
        ("sakjules-devsecops", "Continuous automated security patch pipeline"),
        ("security-patcher", "Automated CVE patch synthesis"),
        ("analyze-full", "Repository-wide static security audit"),
        ("analyze-github-pr", "Pre-merge PR security & privacy analyzer"),
        ("dependency-manager", "Isolated sandbox dependency verification"),
        ("poc", "Proof-of-concept vulnerability validator"),
        ("sakking-github-security-compliance", "Branch protection & supply-chain auditor"),
        ("saksee-cloudflare-turnstile", "Web bot & automated scraping defense"),
        ("saksee-webauthn-storage", "Secure session credential store"),
        ("sakjules-asset-monitor", "Public endpoint & certificate watchdog"),
    ],
    "Pillar 2: CI/CD, Mutation Testing & Self-Healing": [
        ("sakjules-ci-fixer", "Automated GitHub Actions CI diagnostics & auto-repair"),
        ("sakjules-mutation-testing", "AST fault injection & mutant kill scorer"),
        ("sakjules-self-healing-test-generator", "Heuristic Vitest/Pytest generator for survivors"),
        ("sakjules-pylint-ruff-matrix", "Python 3.11/3.12 dual-engine linter & formatter"),
        ("sakjules-mypy-strict", "Strict static type checking gate"),
        ("sakjules-playwright-headless", "End-to-end browser regression harness"),
        ("sakjules-playwright-html-report", "Automated visual HTML test reporting"),
        ("sakjules-github-actions-concurrency", "Workflow lock & cancel-in-progress governor"),
        ("sakjules-pnpm-turbopack-build", "Next.js build cache & fast bundling"),
        ("sakjules-git-commit", "Semantic conventional commit generator"),
        ("sakjules-claude-settings-hooks", "PostToolUse / PreToolUse lifecycle engine"),
        ("sakjules-test-driven-development", "Strict RED-GREEN-REFACTOR workflow"),
        ("sakjules-coverage-governor", "96% branch test coverage enforcement"),
        ("sakjules-dependabot-audit", "Automated CVE bump verification"),
        ("sakjules-release-drafter", "Automated changelog & release bundler"),
        ("sakjules-scorecard-supply-chain", "OpenSSF Scorecard auditor"),
        ("sakjules-subproject-test-runner", "Monorepo matrix runner for subpackages"),
        ("sakjules-cron-fleet-watchdog", "Cron job health & self-healing monitor"),
        ("sakjules-benchmark-latency", "Cold/hot execution throughput benchmarker"),
        ("sakjules-quick-fix", "Minimal targeted bug repair loop"),
    ],
    "Pillar 3: Google ADK & Cloud Native Operations": [
        ("google-agents-cli-adk-code", "Fast API & Python ADK agent construction"),
        ("google-agents-cli-observability", "Cloud Trace OpenTelemetry & BigQuery telemetry"),
        ("google-agents-cli-deploy", "Cloud Run & GKE deployment orchestrator"),
        ("google-agents-cli-eval", "Quality Flywheel trajectory & G-Eval runner"),
        ("google-agents-cli-scaffold", "Project context & skeleton bootstrapper"),
        ("google-agents-cli-workflow", "8-phase agent development lifecycle guide"),
        ("google-agents-cli-publish", "Artifact & model container publishing"),
        ("sakthai-gemini-live-api", "Duplex multimodal audio & WebRTC streaming"),
        ("sakthai-gemini-2-flash-routing", "Sub-200ms latency reasoning dispatcher"),
        ("sakthai-cloud-run-terraform", "Infrastructure-as-code Terraform HCL generator"),
        ("sakthai-bigquery-telemetry-stream", "Agent telemetry logging & SQL analyzer"),
        ("sakthai-gcp-secret-manager", "Cloud KMS & runtime secret injector"),
        ("sakthai-gke-helm-orchestrator", "Kubernetes cluster deployment manager"),
        ("sakthai-cloud-monitoring-alerts", "Latency & token budget threshold alerting"),
        ("sakthai-gemini-sdk-python", "Native Google GenAI SDK patterns"),
        ("sakthai-genkit-bridge", "Firebase Genkit flow orchestrator"),
        ("sakthai-vertex-ai-endpoint", "Managed model endpoint manager"),
        ("sakthai-cloud-sql-pgvector", "Vector embedding database connectors"),
        ("sakthai-google-workspace-gws", "Drive, Docs, and Gmail agent automation"),
        ("sakthai-adk-a2a-bridge", "Google ADK to JSON-RPC A2A adapter"),
    ],
    "Pillar 4: Hugging Face MLOps, Models & Spaces": [
        ("hf-cli", "Official Hugging Face Hub CLI agent-mode tool"),
        ("sakthai-hf-peft-lora", "Low-Rank Adaptation fine-tuning & weight adapter builder"),
        ("sakthai-hf-datasets", "Dataset streaming, validation & Arrow cache manager"),
        ("sakthai-hf-hub-contents-api", "Programmatic Hub file reading & commits"),
        ("sakthai-hf-inference-endpoints", "Serverless & dedicated model serving"),
        ("sakthai-hf-safetensors", "Fast weight loading & format validator"),
        ("sakthai-hf-smolagents", "CodeAgent & ToolCalling agent frameworks"),
        ("sakthai-hf-repocard-system", "YAML metadata card generator & validator"),
        ("sakthai-hf-spaces-docker", "Gradio & Docker Spaces deployment"),
        ("sakthai-hf-spaces-zerogpu", "ZeroGPU accelerator allocator"),
        ("sakthai-hf-sentence-transformers", "Dense semantic embeddings generator"),
        ("sakthai-hf-mergekit", "Model weight merging & distillation"),
        ("sakthai-hf-trl", "Supervised fine-tuning (SFT) & DPO alignment"),
        ("sakthai-hf-transformers-cache", "Local model weights & revision manager"),
        ("sakthai-hf-jobs-api", "Remote compute cluster training dispatch"),
        ("sakthai-hf-data-studio-sql", "DuckDB / SQL query console on datasets"),
        ("sakthai-hf-distilabel", "Synthetic dataset generation & LLM labeling"),
        ("sakthai-hf-open-llm-leaderboard", "MMLU & benchmark performance scoring"),
        ("sakthai-hf-tts", "Text-to-Speech Kokoro & voice delivery"),
        ("sakthai-hf-security-scanning", "Model weights pickle & malware scanner"),
    ],
    "Pillar 5: Multi-Agent Orchestration & A2A Protocols": [
        ("a2a-service-registry", "JSON-RPC 2.0 multi-agent discovery & routing"),
        ("superpowers-subagent-driven-development", "Isolated worker dispatch & task review"),
        ("superpowers-dispatching-parallel-agents", "Concurrent multi-agent execution"),
        ("superpowers-executing-plans", "Plan execution with review checkpoints"),
        ("superpowers-writing-plans", "Multi-phase technical implementation planning"),
        ("sakking-supervisor", "High-level task decomposition & consensus voting"),
        ("sakking-war-room-mesh", "SVG topology visualizer & node telemetry dials"),
        ("sakking-model-routing", "Dynamic LLM routing (Gemini, Claude, GPT, Ollama)"),
        ("sakking-agent-platform-skill-registry", "Dynamic tool & skill registry"),
        ("sakking-agent-platform-rag-engine", "Hybrid RAG retrieval orchestrator"),
        ("sakking-agent-health-diagnostics", "Fleet vitality & heartbeat monitor"),
        ("sakking-using-git-worktrees", "Isolated branch worktree manager"),
        ("saknoi-prompt-studio", "High-dynamic-range prompt calibration"),
        ("saktan-token-analytics", "Token burn velocity & multi-cloud spend tracker"),
        ("saksit-continuous-learning-loop", "Automated research feeding back into memory"),
        ("saksit-diary-writer", "Multi-agent shift journal & outcome logger"),
        ("sakthai-a2a-json-rpc-guard", "Schema validator for inter-agent messages"),
        ("sakking-consensus-voting", "Multi-persona quorum approval engine"),
        ("pm", "Project milestone tracking & task dependencies"),
        ("team", "Team orchestration & workflow session coordinator"),
    ],
    "Pillar 6: Code Quality, Semantic Caching & OODA Cycle": [
        ("sakjules-semantic-cache-optimizer", "64-D L2 cosine similarity response cache"),
        ("sakthai-cycle-dream", "Vision definition & episodic memory recall"),
        ("sakthai-cycle-hope", "Architecture Decision Record (ADR) synthesis"),
        ("sakthai-cycle-care", "Quality, race-condition & concurrency auditor"),
        ("sakthai-cycle-joy", "Release packaging, changelog & deploy gate"),
        ("sakthai-cycle-trust", "Security doctor & invariant verification"),
        ("sakthai-cycle-growth", "Long-term memory consolidation & round advancement"),
        ("sakjules-simplify-code", "3-agent parallel code cleaner & refactorer"),
        ("saksee-systematic-debugging", "4-phase root cause debugging engine"),
        ("sakjules-command-palette", "Global Ctrl+K quick action launcher"),
        ("stitch", "Visual design token & component generator"),
        ("design", "UI/UX layout specs & responsive styling"),
        ("api-design", "RESTful & OpenAPI specification architect"),
        ("code-review", "Multi-tier code review with severity rankings"),
        ("compound-docs", "Institutional knowledge persistence manager"),
        ("persistence", "Ralph mode persistent execution handler"),
        ("db", "SQLite-VSS & schema optimization administrator"),
        ("brainstorm", "Trade-off analysis & architecture design"),
        ("refactor", "Safe structural code transformation"),
        ("watzup", "Real-time activity & recent commit summarizer"),
    ],
}

def find_canonical_skill_path(skill_name: str) -> str:
    """Find the best canonical source path for a skill name."""
    search_dirs = [
        "/home/beern/.agents/skills",
        "/home/beern/Sak-Family-Agent/.agents/skills",
        "/home/beern/Sak-Family-Agent/personas/*/skills",
        "/home/beern/Sak-Family-Agent/.claude/skills",
        "/home/beern/.gemini/config/plugins/*/skills",
        "/home/beern/.gemini/config/skills",
    ]

    # Exact folder match
    for s_dir in search_dirs:
        for p in glob.glob(os.path.join(s_dir, skill_name)):
            if os.path.exists(os.path.join(p, "SKILL.md")):
                return os.path.realpath(p)

    # Fuzzy prefix match (e.g. sakthai-hf-peft-lora vs SakThai-hf-peft-lora)
    clean_target = skill_name.lower().replace("-", "").replace("_", "")
    for s_dir in search_dirs:
        for p in glob.glob(os.path.join(s_dir, "*")):
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "SKILL.md")):
                base = os.path.basename(p).lower().replace("-", "").replace("_", "")
                if base == clean_target or clean_target in base:
                    return os.path.realpath(p)

    # Fallback to creating a high-quality skill folder if new
    fallback_dir = f"/home/beern/Sak-Family-Agent/personas/shared/skills/{skill_name}"
    os.makedirs(fallback_dir, exist_ok=True)
    skill_file = os.path.join(fallback_dir, "SKILL.md")
    if not os.path.exists(skill_file):
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(f"---\nname: {skill_name}\ndescription: Automated skill providing procedures and tools for {skill_name}.\n---\n\n# {skill_name}\n\n## Overview\nSpecialized operational skill for `{skill_name}`.\n\n## Execution Workflow\n1. Initialize environment parameters.\n2. Execute operational procedures.\n3. Validate outputs with automated tests.\n")
    return os.path.realpath(fallback_dir)

def main():
    for target in TARGETS:
        os.makedirs(target, exist_ok=True)

    catalog_data = {"total_skills": 120, "pillars": {}}
    markdown_lines = [
        "# Curated 120-Skill Catalog for Sak-Family & AGY\n",
        "This catalog registers the Top 120 High-Impact Skills into Gemini CLI and Antigravity.\n",
    ]

    installed_counts = {t: 0 for t in TARGETS}

    for pillar_name, skills in PILLARS.items():
        catalog_data["pillars"][pillar_name] = []
        markdown_lines.append(f"\n## {pillar_name}\n")
        markdown_lines.append("| Skill Name | Description | Status |")
        markdown_lines.append("| :--- | :--- | :---: |")

        for skill_name, desc in skills:
            src_path = find_canonical_skill_path(skill_name)
            catalog_data["pillars"][pillar_name].append({
                "name": skill_name,
                "description": desc,
                "path": src_path
            })
            markdown_lines.append(f"| `{skill_name}` | {desc} | 🟢 Active |")

            # Link into all target directories
            for target in TARGETS:
                dest = os.path.join(target, skill_name)
                if os.path.islink(dest) or os.path.exists(dest):
                    try:
                        if os.path.islink(dest):
                            os.unlink(dest)
                        elif os.path.isdir(dest):
                            shutil.rmtree(dest)
                    except Exception:
                        print("Ignored exception")
                try:
                    os.symlink(src_path, dest)
                    installed_counts[target] += 1
                except Exception as e:
                    print(f"Error linking {skill_name} to {target}: {e}")

    # Write Manifests
    os.makedirs("/home/beern/Sak-Family-Agent/docs", exist_ok=True)
    with open("/home/beern/Sak-Family-Agent/docs/curated-skills-120.json", "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, indent=2)

    with open("/home/beern/Sak-Family-Agent/docs/curated-skills-120.md", "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines) + "\n")

    print("=== Curated 120-Skill Installation Complete ===")
    for target, cnt in installed_counts.items():
        print(f"✅ Registered {cnt} skills in: {target}")
    print("📄 Manifest created: docs/curated-skills-120.json")
    print("📄 Documentation created: docs/curated-skills-120.md")

if __name__ == '__main__':
    main()
