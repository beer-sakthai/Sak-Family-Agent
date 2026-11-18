"""Configuration and agent repo discovery."""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Default model used for every role when no per-role override is set. Local
# Ollama by default so a run is free and needs no cloud key on this laptop.
_DEFAULT_LOCAL_MODEL = os.getenv("EVO_MODEL", "ollama_chat/qwen2.5-coder:1.5b")


@dataclass
class EvolutionConfig:
    """Configuration for a self-evolution optimization run."""

    # agent repo path. Discovered lazily and non-fatally so the config
    # can be constructed even when no repo is present (e.g. unit tests, or
    # callers that pass an explicit path). Use resolve_agent_repo_path() when
    # an explicit override should win, or get_agent_repo_path() to require one.
    agent_repo_path: Path | None = None
    hermes_agent_path: Path | None = None

    # Optimization parameters
    iterations: int = 10
    population_size: int = 5

    # LLM configuration. Defaults run fully local against Ollama so a run needs
    # no cloud API key; override per-role with EVO_OPTIMIZER_MODEL / EVO_EVAL_MODEL
    # / EVO_JUDGE_MODEL, or all three at once with EVO_MODEL. Use a LiteLLM model
    # string (e.g. "openai/gpt-4.1") to go back to a cloud provider.
    optimizer_model: str = field(
        default_factory=lambda: os.getenv("EVO_OPTIMIZER_MODEL", _DEFAULT_LOCAL_MODEL)
    )  # Model for GEPA reflections
    eval_model: str = field(
        default_factory=lambda: os.getenv("EVO_EVAL_MODEL", _DEFAULT_LOCAL_MODEL)
    )  # Model for LLM-as-judge scoring
    judge_model: str = field(
        default_factory=lambda: os.getenv("EVO_JUDGE_MODEL", _DEFAULT_LOCAL_MODEL)
    )  # Model for dataset generation

    # Constraints
    max_skill_size: int = 15_000  # 15KB default
    max_tool_desc_size: int = 500  # chars
    max_param_desc_size: int = 200  # chars
    max_prompt_growth: float = 0.2  # 20% max growth over baseline

    # Eval dataset
    eval_dataset_size: int = field(
        default_factory=lambda: int(os.getenv("EVO_DATASET_SIZE", "20"))
    )  # Total examples to generate
    train_ratio: float = 0.5
    val_ratio: float = 0.25
    holdout_ratio: float = 0.25

    # Benchmark gating
    run_pytest: bool = True
    run_tblite: bool = False  # Expensive — opt-in
    tblite_regression_threshold: float = 0.02  # Max 2% regression allowed

    # Output
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    create_pr: bool = True

    def __post_init__(self) -> None:
        if self.agent_repo_path is None and self.hermes_agent_path is not None:
            self.agent_repo_path = self.hermes_agent_path
        elif self.agent_repo_path is not None and self.hermes_agent_path is None:
            self.hermes_agent_path = self.agent_repo_path
        elif self.agent_repo_path is None and self.hermes_agent_path is None:
            discovered = _discover_agent_repo_path()
            self.agent_repo_path = discovered
            self.hermes_agent_path = discovered


def _discover_agent_repo_path() -> Path | None:
    """Best-effort agent repo discovery that never raises."""
    try:
        return get_agent_repo_path()
    except FileNotFoundError:
        return None


_discover_hermes_agent_path = _discover_agent_repo_path


def get_agent_repo_path() -> Path:
    """Discover the agent repo path.

    Priority:
    1. SAK_AGENT_REPO / HERMES_AGENT_REPO env var
    2. Repository root containing personas/sakthai
    3. ~/.sakthai / ~/.hermes install locations
    4. Sibling directory
    """
    for var in ("SAK_AGENT_REPO", "HERMES_AGENT_REPO"):
        env_path = os.getenv(var)
        if env_path:
            p = Path(env_path).expanduser()
            if p.exists():
                return p

    # Check ancestors for repository root containing personas/sakthai
    cur = Path(__file__).resolve().parent
    for _ in range(6):
        if (cur / "personas" / "sakthai").exists():
            return cur
        cur = cur.parent

    for home_candidate in (
        Path.home() / ".sakthai" / "sakthai-agent",
        Path.home() / ".hermes" / "hermes-agent",
    ):
        if home_candidate.exists():
            return home_candidate

    for sibling_path in (
        Path(__file__).parent.parent.parent / "sakthai-agent",
        Path(__file__).parent.parent.parent / "hermes-agent",
    ):
        if sibling_path.exists():
            return sibling_path

    raise FileNotFoundError(
        "Cannot find agent repo. Set SAK_AGENT_REPO env var "
        "or ensure it exists at ~/.sakthai/sakthai-agent"
    )


get_hermes_agent_path = get_agent_repo_path


def resolve_agent_repo_path(repo: str | None = None) -> Path:
    """Return the agent repo path, honoring an explicit override."""
    if repo:
        return Path(repo).expanduser()
    return get_agent_repo_path()


resolve_hermes_agent_path = resolve_agent_repo_path
