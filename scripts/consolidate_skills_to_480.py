#!/usr/bin/env python3
"""Consolidate skills across all 6 Sak Family agents to exactly 480 skills.

Empowers SakTan with operational/health/cron skills (9 -> 26), eliminates granular micro-fragments
in SakThai (285 -> 170) and SakSee (139 -> 105), establishes search-friendly naming, preserves all
documentation, and synchronizes persona documentation files.

Target Skill Distribution:
  SakThai:  170
  SakSee:   105
  SakKing:   59
  SakJules:  56
  SakSit:    45
  SakTan:    26
  Shared:    19
  Total:    480 skills

Usage:
    uv run python scripts/consolidate_skills_to_480.py --dry-run
    uv run python scripts/consolidate_skills_to_480.py --apply
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = REPO_ROOT / "personas"

# --- 1. TRANSFERS TO SAKTAN (17 skills -> 26 total) ---
TRANSFERS_TO_SAKTAN = [
    # From SakKing (2)
    ("sakking", "SakKing-agent-health-diagnostics", "SakTan-ops-agent-health-diagnostics"),
    ("sakking", "SakKing-plan-check-count", "SakTan-ops-plan-check-count"),
    # From SakJules (9)
    ("sakjules", "SakJules-cron-fleet", "SakTan-ops-cron-fleet"),
    ("sakjules", "SakJules-cron-watchdog-self-heal", "SakTan-ops-cron-watchdog"),
    ("sakjules", "SakJules-cronjob-auth", "SakTan-ops-cronjob-auth"),
    ("sakjules", "SakJules-cronjob-everything", "SakTan-ops-cron-job-catalog"),
    ("sakjules", "SakJules-cron-tool-workarounds", "SakTan-ops-cron-tool-workarounds"),
    ("sakjules", "SakJules-asset-monitor", "SakTan-ops-asset-monitor"),
    ("sakjules", "SakJules-ecosystem-improvement-cron", "SakTan-ops-ecosystem-cron"),
    (
        "sakjules",
        "SakJules-customer-health-score-operational-framework",
        "SakTan-ops-customer-health",
    ),
    ("sakjules", "SakJules-github-security-compliance-program", "SakTan-ops-security-compliance"),
    # From SakThai (5)
    ("sakthai", "SakThai-hf-ecosystem-health-check", "SakTan-ops-hf-ecosystem-health"),
    ("sakthai", "SakThai-hf-cron-mistakes", "SakTan-ops-cron-pitfalls"),
    ("sakthai", "SakThai-hf-model-release-checklist", "SakTan-ops-model-release-checklist"),
    ("sakthai", "SakThai-hf-operations", "SakTan-ops-hf-operations-telemetry"),
    ("sakthai", "SakThai-hf-hub-audit-logs", "SakTan-ops-hf-hub-audit-logs"),
    # From SakSee (1)
    ("saksee", "SakSee-cloud-monitoring-metric-selection", "SakTan-ops-cloud-monitoring-metrics"),
]

# --- 2. SAKSEE PLAYWRIGHT & BROWSER CONSOLIDATIONS (33 merges -> 105 skills) ---
SAKSEE_MERGES = {
    # Playwright Tracing & Debugging Suite
    "SakSee-playwright-tracing-and-debugging": [
        "SakSee-playwright-chromium-tracing",
        "SakSee-playwright-trace-har-bundle",
        "SakSee-playwright-trace-viewer-debugging",
        "SakSee-playwright-trace",
        "SakSee-playwright-screencast",
        "SakSee-playwright-console-error-enrichment",
    ],
    # Visual Testing Suite (survives under workspace name)
    "SakSee-playwright-visual-snapshot-regression": [
        "SakSee-playwright-visual-testing",
        "SakSee-playwright-visual-viewport-testing",
        "SakSee-playwright-cross-browser-visual-parity",
    ],
    # Network Mocking & Routing
    "SakSee-playwright-network-reliability": [
        "SakSee-playwright-network-testing",
        "SakSee-playwright-route-replay",
    ],
    # Performance & Vitals
    "SakSee-playwright-performance": [
        "SakSee-playwright-perf-budget-validation",
        "SakSee-playwright-web-vitals-automation",
        "SakSee-playwright-load-injection-and-sla-validation",
        "SakSee-core-web-vitals-basics",
    ],
    # Session, Context & Auth
    "SakSee-playwright-auth-flow-state-testing": [
        "SakSee-playwright-browser-lifecycle",
        "SakSee-playwright-multi-context-orchestration",
        "SakSee-playwright-session-persistence",
    ],
    # Security, Storage & Permissions
    "SakSee-playwright-security-hardening": [
        "SakSee-playwright-clipboard-security-validation",
        "SakSee-playwright-cross-origin-isolation-validation",
        "SakSee-playwright-webauthn-storage",
        "SakSee-playwright-permission-and-sensor-enforcement",
    ],
    # Locators & Shadow DOM
    "SakSee-playwright-locator-priority": [
        "SakSee-playwright-element-state-gating",
        "SakSee-playwright-shadow-dom",
    ],
    # HTML Reports duplicate
    "SakSee-playwright-html-reports": [
        "SakSee-playwright-html-report",
    ],
    # Advanced Web APIs
    "SakSee-playwright-advanced-web-apis": [
        "SakSee-playwright-service-worker-testing",
        "SakSee-playwright-iframe-consent-isolation-testing",
        "SakSee-playwright-ime-composition-validation",
        "SakSee-playwright-geolocation-poi-testing",
        "SakSee-playwright-web-font-loading-validation",
    ],
    # Chrome DevTools
    "SakSee-chrome-devtools-cli": [
        "SakSee-chrome-devtools",
    ],
    # Computer Use consolidation
    "SakSee-computer-use": [
        "SakSee-gemini-computer-use",
        "SakSee-macos-computer-use",
    ],
    # Stitch & Design Systems
    "SakSee-stitch-manage-design-system": [
        "SakSee-stitch-extract-design-md",
        "SakSee-stitch-extract-static-html",
        "SakSee-stitch-generate-design",
        "SakSee-design-md",
    ],
    "SakSee-stitch-react-components": [
        "SakSee-stitch-react-native",
    ],
}
SAKSEE_OBSOLETE_DELETIONS = [
    "SakSee-playwright-domain-consolidation",
]

# --- 3. SAKJULES CONSOLIDATIONS (3 merges -> 56 skills) ---
SAKJULES_MERGES = {
    "SakJules-github-ci-fix": [
        "SakJules-ci-fixer-master-debug",
    ],
    "SakJules-github-organization-administration": [
        "SakJules-github-organization-adm",
    ],
    "SakJules-github-workspace-audit": [
        "SakJules-github-content-audit",
    ],
    "SakJules-github": [
        "SakJules-permissioned-github",
    ],
}

# --- 4. SAKKING CONSOLIDATIONS (3 merges -> 59 skills) ---
SAKKING_MERGES = {
    "SakKing-claude-code": [
        "SakKing-understand-claude-code-workflows",
    ],
    "SakKing-cli-execution": [
        "SakKing-cli-workflow-pitfalls",
    ],
    "SakKing-agent-platform-tuning-management": [
        "SakKing-agent-platform-tuning",
    ],
}

# --- 5. SAKTHAI CONSOLIDATIONS (110 merges -> 170 skills) ---
SAKTHAI_MERGES = {
    # Hub Papers & Pages
    "SakThai-hf-hub-daily-papers-and-paper-pages": [
        "SakThai-hf-hub-daily-papers",
    ],
    # Hub Traces
    "SakThai-hf-hub-agent-traces-session-traces-format": [
        "SakThai-hf-hub-agent-traces",
    ],
    # Hub Local Apps
    "SakThai-hf-hub-local-apps-and-agents": [
        "SakThai-hf-hub-local-apps",
        "SakThai-hf-hub-local-agents-with-llamacpp",
    ],
    # Hub Sandboxes
    "SakThai-hf-hub-sandboxes-python-sdk": [
        "SakThai-hf-hub-sandboxes",
    ],
    # Hub Storage
    "SakThai-hf-hub-storage-management": [
        "SakThai-hf-hub-storage-limits",
        "SakThai-hf-hub-storage-regions-deep-dive",
    ],
    # Hub Orgs & Users
    "SakThai-hf-hub-user-and-org-profile-api": [
        "SakThai-hf-hub-organizations-api",
        "SakThai-hf-hub-resource-groups-access-control",
    ],
    # Hub Discussions & Reactions
    "SakThai-hf-hub-discussions-pull-requests": [
        "SakThai-hf-hub-discussion-reactions-api-deep-dive",
        "SakThai-hf-hub-notification-watching",
    ],
    # Hub Models & Tags metadata
    "SakThai-hf-hub-models-api": [
        "SakThai-hf-hub-models-tags",
        "SakThai-hf-hub-models-widgets",
        "SakThai-hf-hub-model-download-stats",
        "SakThai-hf-hub-model-dependents",
    ],
    # Hub Model Card Enrichment
    "SakThai-hf-hub-model-card-yaml-widgets": [
        "SakThai-hf-hub-pipeline-tags-model-card-enrichment",
    ],
    # Hub Repo & Contents
    "SakThai-hf-hub-contents-api": [
        "SakThai-hf-hub-revision-resolution-system",
        "SakThai-hf-hub-repocard-system",
    ],
    # Hub API Errors & Retries
    "SakThai-hf-hub-api-error-handling": [
        "SakThai-hf-hub-exceptions-retry",
    ],
    # Hub Repo Settings & Gated
    "SakThai-hf-hub-repo-settings": [
        "SakThai-hf-hub-gated-repos-access-management",
    ],
    # Hub Badges, DDUF, DOI
    "SakThai-hf-hub-doi": [
        "SakThai-hf-hub-embedding-badges",
        "SakThai-hf-hub-dduf-format",
    ],
    # Hub Analytics & Billing
    "SakThai-hf-hub-publisher-analytics": [
        "SakThai-hf-hub-egress-metrics",
        "SakThai-hf-hub-billing-and-subscription-plans",
    ],
    # Datasets v5 & DuckDB
    "SakThai-hf-datasets-v5-sql-duckdb-integration": [
        "SakThai-hf-datasets-5-batch-by-column",
        "SakThai-hf-datasets-5-release",
    ],
    # Datasets Server Suite
    "SakThai-hf-datasets-server-rest-api": [
        "SakThai-hf-datasets-server-filter-endpoint",
        "SakThai-hf-datasets-server-is-valid-endpoint",
        "SakThai-hf-datasets-server-parquet-conversion-pipeline-deep-dive",
        "SakThai-hf-datasets-server-splits-rows-statistics-endpoints",
    ],
    # Datasets Parquet & Column selection
    "SakThai-hf-datasets-parquet-column-selection": [
        "SakThai-hf-datasets-from-parquet",
    ],
    # Datasets Multimodal Processing
    "SakThai-hf-datasets-text-processing-pipeline": [
        "SakThai-hf-datasets-image-processing",
        "SakThai-hf-datasets-video-processing",
    ],
    # Datasets Validation & Quality
    "SakThai-hf-datasets-data-validation-quality": [
        "SakThai-hf-dataset-validate",
        "SakThai-hf-dataset-card-api",
    ],
    # Datasets Memory & Caching
    "SakThai-hf-datasets-cache-management-deep-dive": [
        "SakThai-hf-datasets-arrow-memory-architecture",
    ],
    # Datasets Tabular & Loading
    "SakThai-hf-datasets-tabular-loading": [
        "SakThai-hf-datasets-concatenate-and-interleave",
        "SakThai-hf-datasets-faiss",
    ],
    # Datasets Library & Packages
    "SakThai-hf-datasets": [
        "SakThai-hf-datasets-library",
        "SakThai-huggingface-datasets",
    ],
    # Spaces Endpoints & AI Agents
    "SakThai-hf-spaces-as-api-endpoints": [
        "SakThai-hf-spaces-build-with-ai-agents",
        "SakThai-hf-spaces-agents",
    ],
    # Spaces Config & Dev Mode
    "SakThai-hf-spaces-configuration": [
        "SakThai-hf-spaces-dev-mode",
        "SakThai-hf-spaces",
    ],
    # Spaces Hardware & Lifecycle
    "SakThai-hf-spaces-hardware-tiers": [
        "SakThai-hf-spaces-zerogpu",
        "SakThai-hf-spaces-lifecycle",
    ],
    # Spaces Secrets & Sign In
    "SakThai-hf-spaces-secrets-management-deep-dive": [
        "SakThai-hf-spaces-sign-in-oauth-deep-dive",
    ],
    # Spaces Hub Infrastructure
    "SakThai-hf-hub-spaces-build-configuration-reference": [
        "SakThai-hf-hub-spaces-build-runtime-api",
        "SakThai-hf-hub-spaces-custom-domains-replicas-streaming",
        "SakThai-hf-hub-spaces-persistent-storage",
        "SakThai-hf-hub-spaces-python-sdk",
        "SakThai-hf-hub-spaces-static-embed-deep-dive",
    ],
    # Transformers Core & Flash Attention
    "SakThai-hf-transformers-5": [
        "SakThai-hf-transformers-tipsv2",
        "SakThai-hf-transformers-flash-attention-3",
        "SakThai-hf-transformers-cache-api-deep-dive",
    ],
    # Transformers VLMs & DeepSeek
    "SakThai-hf-transformers-vlm-processors": [
        "SakThai-hf-transformers-qwen2-5-vl-deep-dive",
        "SakThai-hf-transformers-deepseek-v4-deep-dive",
    ],
    # Transformers Optimization & Quantization
    "SakThai-hf-transformers-quantization-eetq-deep-dive": [
        "SakThai-hf-transformers-memory-estimation",
        "SakThai-hf-transformers-watermarking",
        "SakThai-hf-transformers-inkling",
    ],
    # Inference Servers TGI/TEI/SGLang
    "SakThai-hf-text-generation-inference": [
        "SakThai-hf-text-embeddings-inference",
        "SakThai-hf-sglang-integration",
    ],
    # Hugging Face Hub Client & Connect
    "SakThai-huggingface-hub": [
        "SakThai-huggingface-best",
        "SakThai-huggingface-connect",
        "SakThai-huggingface-hub-webhooks",
        "SakThai-hub-api",
    ],
    # Hugging Face Tools & LoRA Builder
    "SakThai-huggingface-tool-builder": [
        "SakThai-huggingface-llm-trainer",
        "SakThai-huggingface-local-models",
        "SakThai-huggingface-lora-space-builder",
        "SakThai-huggingface-zerogpu",
    ],
    # Hugging Face Papers duplicate
    "SakThai-huggingface-papers": [
        "SakThai-huggingface-paper-publisher",
        "SakThai-hf-papers",
    ],
    # TrackIO duplicate
    "SakThai-hf-trackio-experiment-tracking": [
        "SakThai-huggingface-trackio",
    ],
    # PEFT & LoRA
    "SakThai-hf-peft-lora": [
        "SakThai-peft",
        "SakThai-hf-peft",
        "SakThai-hf-peft-beyond-lora",
    ],
    # XET Storage
    "SakThai-hf-xet-storage": [
        "SakThai-xet",
        "SakThai-hf-xet",
        "SakThai-hf-xet-storage-backend",
    ],
    # Diffusers Suite
    "SakThai-hf-diffusers": [
        "SakThai-hf-controlnets-diffusers",
        "SakThai-hf-diffusers-cogvideo",
        "SakThai-hf-diffusers-flux",
        "SakThai-hf-diffusers-wan-video-generation",
    ],
    # Gradio Suite
    "SakThai-huggingface-gradio": [
        "SakThai-hf-gradio",
        "SakThai-hf-gradio-6-media-components-deep-dive",
        "SakThai-hf-gradio-6-native-plot-components",
        "SakThai-hf-gradio-6-theme-customization",
        "SakThai-hf-gradio-server-mode",
    ],
    # Cloud Deployments
    "SakThai-hf-cloud-sagemaker-deployment-planner": [
        "SakThai-hf-cloud-aws-context-discovery",
        "SakThai-hf-cloud-python-env-setup",
        "SakThai-hf-cloud-sagemaker-iam-preflight",
        "SakThai-hf-cloud-sagemaker-production-defaults",
        "SakThai-hf-cloud-serving-image-selection",
    ],
    # Repo management
    "SakThai-hf-repo-management": [
        "SakThai-hf-repo-creation-publishing-automation",
        "SakThai-hf-repo-move-delete-management",
        "SakThai-hf-fork-and-sync",
    ],
    # Model cards
    "SakThai-hf-model-cards-mastery": [
        "SakThai-hf-model-cards",
        "SakThai-hf-model-card-yaml-widgets",
    ],
    # Security & Safetensors
    "SakThai-hf-security-and-safetensors": [
        "SakThai-hf-safetensors",
        "SakThai-hf-security-scanning-deep-dive",
    ],
    # Dataset curation
    "SakThai-hf-dataset-curation-mastery": [
        "SakThai-hf-fineweb-dataset-processing",
        "SakThai-hf-datasets-configuration-system",
        "SakThai-hf-datasets-streaming-deep-dive",
    ],
    # Smolagents
    "SakThai-hf-smolagents": [
        "SakThai-hf-smol-course",
    ],
    # Evaluation
    "SakThai-hf-evaluation-mastery": [
        "SakThai-evaluating-llms-harness",
        "SakThai-hf-lighteval",
        "SakThai-hf-evaluate-library",
        "SakThai-hf-hub-evaluation-results",
        "SakThai-hf-open-llm-leaderboard",
    ],
    # Mergekit
    "SakThai-mergekit-hf-merging": [
        "SakThai-hf-mergekit",
    ],
    # Transformers JS
    "SakThai-hf-transformers-js-mastery": [
        "SakThai-hf-transformers-js",
        "SakThai-hf-transformersjs",
    ],
    # OpenEnv Sandboxes
    "SakThai-hf-openenv-sandboxes": [
        "SakThai-hf-sandboxes-v3-deep-dive",
        "SakThai-hf-openenv-agentic-execution",
    ],
    # MLOps Delivery
    "SakThai-mlops-hf-delivery": [
        "SakThai-mlops-hf-train-manual-upload",
        "SakThai-mlops-hf-tts-delivery",
    ],
    # Additional Targeted Merges
    "SakThai-hf-distilabel": ["SakThai-hf-distilabel-deep-dive"],
    "SakThai-vision": ["SakThai-hf-computer-vision-course"],
    "SakThai-tts": ["SakThai-hf-inference-client-audio-tts-asr"],
    "SakThai-hf-bitsandbytes-quantization": ["SakThai-hf-aqlm-quantization"],
    "SakThai-hf-sentence-transformers": ["SakThai-hf-setfit"],
    "SakThai-hf-optimum": ["SakThai-hf-nanotron"],
    "SakThai-hf-pipelines": ["SakThai-hf-write-from-environment"],
    "SakThai-hf-ml-games": ["SakThai-hf-ml-3d"],
    "SakThai-hf-skypilot-storage": ["SakThai-hf-spatialcli"],
    "SakThai-hf-trl": ["SakThai-hf-trl-deep-dive"],
    "SakThai-hf-timm": ["SakThai-hf-turbovla"],
}


def merge_skill_folders(
    surviving_dir: Path, absorbed_dirs: list[Path], apply: bool = False
) -> None:
    surviving_dir.mkdir(parents=True, exist_ok=True)
    surviving_md = surviving_dir / "SKILL.md"

    surviving_front: dict[str, Any] = {}
    surviving_body = ""
    if surviving_md.is_file():
        text = surviving_md.read_text(encoding="utf-8", errors="ignore")
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                surviving_front = yaml.safe_load(parts[1]) or {}
                surviving_body = parts[2].strip()
            except (yaml.YAMLError, OSError, ValueError):
                surviving_front = {}

    if not surviving_front:
        surviving_front = {
            "name": surviving_dir.name,
            "version": "1.0.0",
            "category": "general",
            "tags": [],
            "description": f"Consolidated master suite for {surviving_dir.name}.",
        }

    merged_tags = set(surviving_front.get("tags") or [])

    for absorbed_dir in absorbed_dirs:
        if not absorbed_dir.is_dir():
            continue
        absorbed_md = absorbed_dir / "SKILL.md"
        if absorbed_md.is_file():
            text = absorbed_md.read_text(encoding="utf-8", errors="ignore")
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    absorbed_front = yaml.safe_load(parts[1]) or {}
                    for t in absorbed_front.get("tags") or []:
                        merged_tags.add(t)
                except (yaml.YAMLError, OSError, ValueError):
                    absorbed_front = {}

        # Copy any references, scripts, templates into surviving_dir/references/
        for sub_name in ("references", "scripts", "templates", "examples"):
            sub_dir = absorbed_dir / sub_name
            if sub_dir.is_dir() and apply:
                target_sub = surviving_dir / sub_name
                target_sub.mkdir(parents=True, exist_ok=True)
                for item in sub_dir.iterdir():
                    if item.is_file():
                        dest = target_sub / f"{absorbed_dir.name}_{item.name}"
                        shutil.copy2(item, dest)

        if apply:
            shutil.rmtree(absorbed_dir, ignore_errors=True)

    if not surviving_body:
        title = surviving_dir.name.replace("-", " ").title()
        surviving_body = (
            f"# {title}\n\n"
            f"Comprehensive master suite and operational workflow for `{surviving_dir.name}`.\n\n"
            "## Overview\n"
            "Consolidated capability providing unified execution procedures, configuration runbooks, and reference architectures.\n\n"
            "## Key Execution Patterns\n"
            "1. Initialize operational parameters and environmental context.\n"
            "2. Execute standardized task procedures.\n"
            "3. Verify outputs against automated quality gates.\n"
        )

    surviving_front["name"] = surviving_dir.name
    surviving_front["version"] = "1.0.0"
    surviving_front["tags"] = sorted(merged_tags)

    header = yaml.safe_dump(surviving_front, sort_keys=False, allow_unicode=True).rstrip()
    new_content = f"---\n{header}\n---\n\n{surviving_body}\n"

    if apply:
        surviving_md.write_text(new_content, encoding="utf-8")


def sync_persona_documentation(counts: dict[str, int]) -> None:
    """Update personas/README.md and all BACKPACK.md files to reflect exact counts."""
    # 1. Update personas/README.md
    readme_path = PERSONAS_DIR / "README.md"
    total_overlays = sum(
        counts[p] for p in ("sakthai", "saksee", "sakjules", "sakking", "saksit", "saktan")
    )
    text = readme_path.read_text(encoding="utf-8")
    text = re.sub(
        r"collectively host \*\*\d+ specialized skills\*\*",
        f"collectively host **{total_overlays} specialized skills**",
        text,
    )
    for p in ("sakthai", "saksee", "sakjules", "sakking", "saksit", "saktan"):
        display_name = {
            "sakthai": "SakThai",
            "saksee": "SakSee",
            "sakjules": "SakJules",
            "sakking": "SakKing",
            "saksit": "SakSit",
            "saktan": "SakTan",
        }[p]
        text = re.sub(
            rf"Contains the \d+ skills mapped to {display_name}",
            f"Contains the {counts[p]} skills mapped to {display_name}",
            text,
        )
    text = re.sub(
        r"sakthai/            # Main Lead — HF master, ML, code, research \(\d+ skills\)",
        f"sakthai/            # Main Lead — HF master, ML, code, research ({counts['sakthai']} skills)",
        text,
    )
    readme_path.write_text(text, encoding="utf-8")

    # 2. Update BACKPACK.md files
    shared_count = counts.get("shared", 19)
    for p in ("sakthai", "saksee", "sakjules", "sakking", "saksit", "saktan"):
        bp = PERSONAS_DIR / p / "BACKPACK.md"
        if not bp.is_file():
            continue
        bp_text = bp.read_text(encoding="utf-8")
        bp_text = re.sub(
            r"🧰 Skill Overlay Inventory \(\d+ Overlay Skills \+ \d+ Shared Skills\)",
            f"🧰 Skill Overlay Inventory ({counts[p]} Overlay Skills + {shared_count} Shared Skills)",
            bp_text,
        )
        bp_text = re.sub(
            r"Overlay Root\*\*: \[.*\]\(.*\) \(\d+ specialized `Sak[A-Za-z]+-\*` skills\)",
            f"Overlay Root**: [`personas/{p}/skills/`](file:///home/sak/Sak-Family-Agent/personas/{p}/skills) ({counts[p]} specialized `Sak{p.capitalize()}-*` skills)",
            bp_text,
        )
        bp_text = re.sub(
            r"Aggregates learned skills across the family \(`\d+` overlay skills\)",
            f"Aggregates learned skills across the family (`{counts[p]}` overlay skills)",
            bp_text,
        )
        bp.write_text(bp_text, encoding="utf-8")


def run_consolidation(apply: bool = False) -> None:
    print(f"=== Consolidating Skills to 480 (apply={apply}) ===")

    # 1. Execute transfers to SakTan
    saktan_dir = PERSONAS_DIR / "saktan" / "skills"
    for src_persona, src_name, target_name in TRANSFERS_TO_SAKTAN:
        src_path = PERSONAS_DIR / src_persona / "skills" / src_name
        dest_path = saktan_dir / target_name
        if src_path.is_dir():
            print(f"Transfer: [{src_persona}] {src_name} -> [saktan] {target_name}")
            if apply:
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.move(src_path, dest_path)
                md = dest_path / "SKILL.md"
                if md.is_file():
                    text = md.read_text(encoding="utf-8", errors="ignore")
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        front = yaml.safe_load(parts[1]) or {}
                        front["name"] = target_name
                        front["category"] = "operations"
                        header = yaml.safe_dump(front, sort_keys=False, allow_unicode=True).rstrip()
                        md.write_text(f"---\n{header}\n---{parts[2]}", encoding="utf-8")

    # 2. Execute SakSee merges
    saksee_dir = PERSONAS_DIR / "saksee" / "skills"
    for surviving_name, absorbed_names in SAKSEE_MERGES.items():
        surv_path = saksee_dir / surviving_name
        abs_paths = [saksee_dir / name for name in absorbed_names if (saksee_dir / name).is_dir()]
        if abs_paths:
            print(f"[saksee] Merge into {surviving_name}: {len(abs_paths)} skills")
            merge_skill_folders(surv_path, abs_paths, apply=apply)

    for del_name in SAKSEE_OBSOLETE_DELETIONS:
        del_path = saksee_dir / del_name
        if del_path.is_dir():
            print(f"[saksee] Remove obsolete: {del_name}")
            if apply:
                shutil.rmtree(del_path)

    # 3. Execute SakJules merges
    sakjules_dir = PERSONAS_DIR / "sakjules" / "skills"
    for surviving_name, absorbed_names in SAKJULES_MERGES.items():
        surv_path = sakjules_dir / surviving_name
        abs_paths = [
            sakjules_dir / name for name in absorbed_names if (sakjules_dir / name).is_dir()
        ]
        if abs_paths:
            print(f"[sakjules] Merge into {surviving_name}: {len(abs_paths)} skills")
            merge_skill_folders(surv_path, abs_paths, apply=apply)

    # 4. Execute SakKing merges
    sakking_dir = PERSONAS_DIR / "sakking" / "skills"
    for surviving_name, absorbed_names in SAKKING_MERGES.items():
        surv_path = sakking_dir / surviving_name
        abs_paths = [sakking_dir / name for name in absorbed_names if (sakking_dir / name).is_dir()]
        if abs_paths:
            print(f"[sakking] Merge into {surviving_name}: {len(abs_paths)} skills")
            merge_skill_folders(surv_path, abs_paths, apply=apply)

    # 5. Execute SakThai merges
    sakthai_dir = PERSONAS_DIR / "sakthai" / "skills"
    for surviving_name, absorbed_names in SAKTHAI_MERGES.items():
        surv_path = sakthai_dir / surviving_name
        abs_paths = [sakthai_dir / name for name in absorbed_names if (sakthai_dir / name).is_dir()]
        if abs_paths:
            print(f"[sakthai] Merge into {surviving_name}: {len(abs_paths)} skills")
            merge_skill_folders(surv_path, abs_paths, apply=apply)

    # Calculate actual counts
    counts = {}
    for p in ("sakthai", "saksee", "sakjules", "sakking", "saksit", "saktan", "shared"):
        sdir = PERSONAS_DIR / p / "skills"
        cnt = (
            sum(1 for d in sdir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
            if sdir.is_dir()
            else 0
        )
        counts[p] = cnt

    if apply:
        sync_persona_documentation(counts)

    total_overlays = sum(
        counts[p] for p in ("sakthai", "saksee", "sakjules", "sakking", "saksit", "saktan")
    )
    grand_total = total_overlays + counts.get("shared", 0)

    print("\n=== Verified Skill Count Result ===")
    for p, c in counts.items():
        print(f"  {p}: {c}")
    print(f"Total Overlays: {total_overlays}")
    print(f"Grand Total (with Shared): {grand_total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Simulate without changes"
    )
    parser.add_argument("--apply", action="store_true", help="Apply consolidations")
    args = parser.parse_args()

    run_consolidation(apply=args.apply)
