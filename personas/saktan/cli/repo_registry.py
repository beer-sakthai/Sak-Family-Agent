"""Declarative task and subsystem registry for repository-wide CLI coverage.

Provides structured metadata for tasks across scripts/, training/, eval/,
dashboard/, infra/, services/, and evolution/. Used by ``sakthai repo``
and individual domain CLI groups.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from .. import config


@dataclass(frozen=True)
class RepoTask:
    """A registered repository script or command."""

    name: str
    area: str
    summary: str
    argv: tuple[str, ...]
    cwd: str = "."
    requires: tuple[str, ...] = ()
    file_path: str | None = None

    def check_requirements(self) -> list[str]:
        """Return any missing required system executables."""
        missing: list[str] = []
        for req in self.requires:
            if shutil.which(req) is None:
                missing.append(req)
        return missing

    def check_target_file(self) -> bool:
        """Verify that the target script or entrypoint exists on disk."""
        if not self.file_path:
            return True
        path = (config.REPO_ROOT / self.file_path).resolve()
        return path.exists()


AREAS: dict[str, str] = {
    "scripts": "scripts/",
    "eval": "scripts/eval/ & evaluation_tasks/",
    "training": "training/ & scripts/train/",
    "dashboard": "apps/sak_agent_dashboard/",
    "telegram": "personas/sakthai/telegram/ & scripts/",
    "hf": "scripts/ (Hugging Face portfolio & health)",
    "infra": "infra/ & scripts/infra-audit.sh",
    "evolution": "personas/sakthai/evolution/",
    "ci": "scripts/ (CI, healing & workflow maintenance)",
    "gateway": "personas/sakthai/gateway/ & scripts/serve_gateway.py",
}


TASKS: tuple[RepoTask, ...] = (
    # --- Scripts & Maintenance ---
    RepoTask(
        name="diagnose-personas",
        area="scripts",
        summary="Audit working files, SOUL/CYCLE rubrics, and skills across all 6 personas.",
        argv=("uv", "run", "python", "scripts/diagnose_personas.py"),
        file_path="scripts/diagnose_personas.py",
        requires=("uv",),
    ),
    RepoTask(
        name="compose-persona",
        area="scripts",
        summary="Assemble composite persona instructions and validate persona coherence.",
        argv=("uv", "run", "python", "scripts/compose_persona.py"),
        file_path="scripts/compose_persona.py",
        requires=("uv",),
    ),
    RepoTask(
        name="export-agent-repo",
        area="scripts",
        summary="Export and sync core agent packages to standalone repository formats.",
        argv=("uv", "run", "python", "scripts/export_agent_repo.py"),
        file_path="scripts/export_agent_repo.py",
        requires=("uv",),
    ),
    RepoTask(
        name="system-snapshot",
        area="scripts",
        summary="Generate a comprehensive JSON and Markdown system snapshot.",
        argv=("uv", "run", "python", "scripts/gen_system_snapshot.py"),
        file_path="scripts/gen_system_snapshot.py",
        requires=("uv",),
    ),
    RepoTask(
        name="gen-dashboard-types",
        area="dashboard",
        summary="Regenerate TypeScript type definitions for the Next.js agent dashboard.",
        argv=("uv", "run", "python", "scripts/gen_dashboard_types.py"),
        file_path="scripts/gen_dashboard_types.py",
        requires=("uv",),
    ),
    RepoTask(
        name="serve-api",
        area="scripts",
        summary="Launch the local FastAPI/HTTP server for the agent workspace.",
        argv=("uv", "run", "python", "scripts/serve_api.py"),
        file_path="scripts/serve_api.py",
        requires=("uv",),
    ),
    # --- Evaluation & Benchmarking ---
    RepoTask(
        name="eval-loop",
        area="eval",
        summary="Run continuous or batch evaluation loop across registered tasks.",
        argv=("uv", "run", "python", "scripts/run_eval_loop.py"),
        file_path="scripts/run_eval_loop.py",
        requires=("uv",),
    ),
    RepoTask(
        name="eval-bench",
        area="eval",
        summary="Execute benchmark evaluation suite for SakThai models.",
        argv=("uv", "run", "python", "scripts/eval/run_bench.py"),
        file_path="scripts/eval/run_bench.py",
        requires=("uv",),
    ),
    RepoTask(
        name="eval-compare",
        area="eval",
        summary="Compare benchmark results across multiple model checkpoints.",
        argv=("uv", "run", "python", "scripts/eval/compare.py"),
        file_path="scripts/eval/compare.py",
        requires=("uv",),
    ),
    # --- Training & Datasets ---
    RepoTask(
        name="train-sft",
        area="training",
        summary="Launch SFT QLoRA fine-tuning run using the training recipe.",
        argv=("uv", "run", "python", "scripts/train/sft_qlora.py"),
        file_path="scripts/train/sft_qlora.py",
        requires=("uv",),
    ),
    RepoTask(
        name="build-dataset",
        area="training",
        summary="Compile and format v12 fine-tuning and evaluation datasets.",
        argv=("uv", "run", "python", "scripts/dataset_prep/build_v12.py"),
        file_path="scripts/dataset_prep/build_v12.py",
        requires=("uv",),
    ),
    RepoTask(
        name="build-toolcalling-dataset",
        area="training",
        summary="Generate synthetic tool-calling SFT dataset for SakThai built-in tools.",
        argv=("uv", "run", "python", "training/hf-jobs/build_toolcalling_dataset.py"),
        file_path="training/hf-jobs/build_toolcalling_dataset.py",
        requires=("uv",),
    ),
    RepoTask(
        name="fetch-toolcalling-public",
        area="training",
        summary="Fetch and reformat public function-calling dataset slices for general competence.",
        argv=("uv", "run", "python", "training/hf-jobs/fetch_public_toolcalling.py"),
        file_path="training/hf-jobs/fetch_public_toolcalling.py",
        requires=("uv",),
    ),
    RepoTask(
        name="train-toolcalling-lora",
        area="training",
        summary="Train Qwen2.5 tool-calling QLoRA adapter via HF Jobs.",
        argv=("uv", "run", "python", "training/hf-jobs/train_toolcalling_lora.py"),
        file_path="training/hf-jobs/train_toolcalling_lora.py",
        requires=("uv",),
    ),
    RepoTask(
        name="train-persona-lora",
        area="training",
        summary="Train persona voice/style QLoRA adapter on hermes dataset.",
        argv=("uv", "run", "python", "training/hf-jobs/train_persona_lora.py"),
        file_path="training/hf-jobs/train_persona_lora.py",
        requires=("uv",),
    ),
    RepoTask(
        name="train-coder-lora",
        area="training",
        summary="Train and evaluate SakThai coding adapter with AST validation.",
        argv=("uv", "run", "python", "training/hf-jobs/train_eval_coder_lora.py"),
        file_path="training/hf-jobs/train_eval_coder_lora.py",
        requires=("uv",),
    ),
    RepoTask(
        name="eval-toolcalling",
        area="training",
        summary="Smoke-test and evaluate tool-calling fidelity on fine-tuned adapters.",
        argv=("uv", "run", "python", "training/serving/eval_toolcalling.py"),
        file_path="training/serving/eval_toolcalling.py",
        requires=("uv",),
    ),
    RepoTask(
        name="export-ollama",
        area="training",
        summary="Merge LoRA adapter and export Ollama Modelfile for local agent execution.",
        argv=("uv", "run", "python", "training/serving/export_ollama.py"),
        file_path="training/serving/export_ollama.py",
        requires=("uv",),
    ),
    RepoTask(
        name="deploy-hf-endpoint",
        area="training",
        summary="Deploy or plan cloud TGI Inference Endpoint with OpenAI-compatible /v1 API.",
        argv=("uv", "run", "python", "training/serving/deploy_hf_endpoint.py"),
        file_path="training/serving/deploy_hf_endpoint.py",
        requires=("uv",),
    ),
    RepoTask(
        name="openenv-verify",
        area="training",
        summary="Run CPU OpenEnv RL environment_factory contract verification via openenv-rl-training.",
        argv=("uv", "run", "python", "scripts/train/openenv_ecosystem.py", "verify"),
        file_path="scripts/train/openenv_ecosystem.py",
        requires=("uv",),
    ),
    RepoTask(
        name="openenv-test",
        area="training",
        summary="Run the 149-test OpenEnv RL training suite across all 5 workspaces.",
        argv=("uv", "run", "python", "scripts/train/openenv_ecosystem.py", "test"),
        file_path="scripts/train/openenv_ecosystem.py",
        requires=("uv",),
    ),
    RepoTask(
        name="openenv-baselines",
        area="training",
        summary="Run CPU heuristic baseline policy competition and GRPO reward-variance checks.",
        argv=("uv", "run", "python", "scripts/train/openenv_ecosystem.py", "baselines"),
        file_path="scripts/train/openenv_ecosystem.py",
        requires=("uv",),
    ),
    # --- Hugging Face Hub ---
    RepoTask(
        name="hf-portfolio-health",
        area="hf",
        summary="Inspect and audit health of models, spaces, and datasets on Hugging Face.",
        argv=("uv", "run", "python", "scripts/hf-portfolio-health.py"),
        file_path="scripts/hf-portfolio-health.py",
        requires=("uv",),
    ),
    RepoTask(
        name="hf-check-assets",
        area="hf",
        summary="Verify asset availability and metadata across Hugging Face Hub repos.",
        argv=("uv", "run", "python", "scripts/check_hf_assets.py"),
        file_path="scripts/check_hf_assets.py",
        requires=("uv",),
    ),
    RepoTask(
        name="hf-smoke",
        area="hf",
        summary="Run Hugging Face Hub integration smoke tests.",
        argv=("uv", "run", "python", "scripts/hf_integration_smoke.py"),
        file_path="scripts/hf_integration_smoke.py",
        requires=("uv",),
    ),
    # --- Telegram & Messaging ---
    RepoTask(
        name="telegram-send",
        area="telegram",
        summary="Send a message or notification to a configured Telegram chat.",
        argv=("uv", "run", "python", "scripts/telegram_send.py"),
        file_path="scripts/telegram_send.py",
        requires=("uv",),
    ),
    RepoTask(
        name="vm-agents-setup",
        area="telegram",
        summary="Provision and configure systemd / background VM agents for Telegram bots.",
        argv=("uv", "run", "python", "scripts/setup_vm_telegram_agents.py"),
        file_path="scripts/setup_vm_telegram_agents.py",
        requires=("uv",),
    ),
    RepoTask(
        name="vm-agents-verify",
        area="telegram",
        summary="Verify live operational status of background VM Telegram bots.",
        argv=("uv", "run", "python", "scripts/verify_vm_telegram_agents.py"),
        file_path="scripts/verify_vm_telegram_agents.py",
        requires=("uv",),
    ),
    # --- CI, Quality & Auto-Healing ---
    RepoTask(
        name="ci-auto-heal",
        area="ci",
        summary="Inspect and remediate common CI and environment failures.",
        argv=("uv", "run", "python", "scripts/ci_auto_heal.py"),
        file_path="scripts/ci_auto_heal.py",
        requires=("uv",),
    ),
    RepoTask(
        name="skills-auto-heal",
        area="ci",
        summary="Automatically validate and heal frontmatter/formatting across skills.",
        argv=("uv", "run", "python", "scripts/auto_heal_skills.py"),
        file_path="scripts/auto_heal_skills.py",
        requires=("uv",),
    ),
    RepoTask(
        name="skills-quality-scan",
        area="ci",
        summary="Run bash quality scan script across all skill directories.",
        argv=("bash", "scripts/skills-quality-scan.sh"),
        file_path="scripts/skills-quality-scan.sh",
        requires=("bash",),
    ),
    RepoTask(
        name="validate-agent-definition",
        area="ci",
        summary="Validate agent configurations, YAML schemas, and persona definitions.",
        argv=("uv", "run", "python", "scripts/validate_agent_definition.py"),
        file_path="scripts/validate_agent_definition.py",
        requires=("uv",),
    ),
    RepoTask(
        name="lint-workflow-permissions",
        area="ci",
        summary="Audit GitHub Actions workflows for least-privilege token permissions.",
        argv=("uv", "run", "python", "scripts/lint_workflow_permissions.py"),
        file_path="scripts/lint_workflow_permissions.py",
        requires=("uv",),
    ),
    RepoTask(
        name="audit-workflow-concurrency",
        area="ci",
        summary="Audit workflow concurrency groups to avoid duplicate CI builds.",
        argv=("uv", "run", "python", "scripts/audit_workflow_concurrency.py"),
        file_path="scripts/audit_workflow_concurrency.py",
        requires=("uv",),
    ),
    RepoTask(
        name="code-scanning-analyses",
        area="ci",
        summary="Fetch and summarize GitHub Code Scanning alert metrics.",
        argv=("uv", "run", "python", "scripts/code_scanning_analyses.py"),
        file_path="scripts/code_scanning_analyses.py",
        requires=("uv",),
    ),
    RepoTask(
        name="sync-wiki",
        area="ci",
        summary="Synchronize repository documentation to the GitHub Wiki.",
        argv=("uv", "run", "python", "scripts/sync_wiki.py"),
        file_path="scripts/sync_wiki.py",
        requires=("uv",),
    ),
    RepoTask(
        name="a2a-bus",
        area="scripts",
        summary="Test and inspect agent-to-agent message bus communication.",
        argv=("uv", "run", "python", "scripts/a2a-bus.py"),
        file_path="scripts/a2a-bus.py",
        requires=("uv",),
    ),
    RepoTask(
        name="family-status",
        area="scripts",
        summary="Print high-level operational status across the 6 Sak Family members.",
        argv=("bash", "scripts/family-status.sh"),
        file_path="scripts/family-status.sh",
        requires=("bash",),
    ),
    RepoTask(
        name="infra-audit",
        area="infra",
        summary="Run comprehensive audit of local and cloud infrastructure.",
        argv=("bash", "scripts/infra-audit.sh"),
        file_path="scripts/infra-audit.sh",
        requires=("bash",),
    ),
    RepoTask(
        name="model-report",
        area="hf",
        summary="Generate model cards and performance report.",
        argv=("bash", "scripts/model-report.sh"),
        file_path="scripts/model-report.sh",
        requires=("bash",),
    ),
    RepoTask(
        name="gguf-chat",
        area="scripts",
        summary="Launch low-level llama.cpp / GGUF local chat runner.",
        argv=("bash", "scripts/sakthai-chat.sh"),
        file_path="scripts/sakthai-chat.sh",
        requires=("bash",),
    ),
    RepoTask(
        name="infer",
        area="scripts",
        summary="Execute local one-shot model inference script.",
        argv=("bash", "scripts/sakthai-infer.sh"),
        file_path="scripts/sakthai-infer.sh",
        requires=("bash",),
    ),
    RepoTask(
        name="release",
        area="ci",
        summary="Execute automated version release and packaging script.",
        argv=("bash", "scripts/release.sh"),
        file_path="scripts/release.sh",
        requires=("bash",),
    ),
    RepoTask(
        name="consolidate-skills",
        area="ci",
        summary="Run skill consolidation utility across personas.",
        argv=("uv", "run", "python", "scripts/consolidate_skills_to_480.py"),
        file_path="scripts/consolidate_skills_to_480.py",
        requires=("uv",),
    ),
    RepoTask(
        name="refactor-skills-metadata",
        area="ci",
        summary="Standardize and refactor category tags across all skills.",
        argv=("uv", "run", "python", "scripts/refactor_skills_metadata.py"),
        file_path="scripts/refactor_skills_metadata.py",
        requires=("uv",),
    ),
    # --- Self-Evolution Organisms ---
    RepoTask(
        name="evolve-skill",
        area="evolution",
        summary="Run DSPy GEPA optimization loop on agent skills.",
        argv=("uv", "run", "python", "-m", "evolution.skills.evolve_skill"),
        cwd="personas/sakthai",
        file_path="personas/sakthai/evolution/skills/evolve_skill.py",
        requires=("uv",),
    ),
    RepoTask(
        name="evolve-prompts",
        area="evolution",
        summary="Run DSPy GEPA optimization loop on persona system prompts.",
        argv=("uv", "run", "python", "-m", "evolution.prompts.evolve_prompts"),
        cwd="personas/sakthai",
        file_path="personas/sakthai/evolution/prompts/evolve_prompts.py",
        requires=("uv",),
    ),
    RepoTask(
        name="evolve-code",
        area="evolution",
        summary="Run self-evolution genetic optimization on Python code.",
        argv=("uv", "run", "python", "-m", "evolution.code.evolve_code"),
        cwd="personas/sakthai",
        file_path="personas/sakthai/evolution/code/evolve_code.py",
        requires=("uv",),
    ),
    RepoTask(
        name="evolve-tools",
        area="evolution",
        summary="Run self-evolution genetic optimization on agent tools.",
        argv=("uv", "run", "python", "-m", "evolution.tools.evolve_tools"),
        cwd="personas/sakthai",
        file_path="personas/sakthai/evolution/tools/evolve_tools.py",
        requires=("uv",),
    ),
    RepoTask(
        name="evolve-monitor",
        area="evolution",
        summary="Run the self-evolution monitor and trigger loop.",
        argv=("uv", "run", "python", "-m", "evolution.monitor.monitor"),
        cwd="personas/sakthai",
        file_path="personas/sakthai/evolution/monitor/monitor.py",
        requires=("uv",),
    ),
    # --- Gateway ---
    RepoTask(
        name="gateway-serve",
        area="gateway",
        summary="Run the live OpenAI-compatible Runtime Gateway HTTP server.",
        argv=("python", "scripts/serve_gateway.py"),
        file_path="scripts/serve_gateway.py",
    ),
    RepoTask(
        name="gateway-status",
        area="gateway",
        summary="Check health and operational telemetry of the Runtime Gateway.",
        argv=("sakthai", "gateway", "status"),
    ),
)


TASK_MAP: dict[str, RepoTask] = {task.name: task for task in TASKS}


def get_task(name: str) -> RepoTask | None:
    """Look up a registered task by name."""
    return TASK_MAP.get(name)


def list_tasks(area: str | None = None) -> list[RepoTask]:
    """List tasks, optionally filtered by area."""
    if area:
        return [t for t in TASKS if t.area == area]
    return list(TASKS)


def get_repo_coverage_map() -> dict[str, dict[str, object]]:
    """Build a status report mapping top-level repository areas to tasks and paths."""
    report: dict[str, dict[str, object]] = {}
    for area_key, path_desc in AREAS.items():
        area_tasks = [t for t in TASKS if t.area == area_key]
        report[area_key] = {
            "path": path_desc,
            "task_count": len(area_tasks),
            "tasks": [t.name for t in area_tasks],
        }
    return report
