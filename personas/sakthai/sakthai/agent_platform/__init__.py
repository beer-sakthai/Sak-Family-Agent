"""SakThai Unified Agent Platform Package."""

from sakthai.agent_platform.agent_engine import (
    AgentEngineMode,
    UnifiedAgentConfig,
    UnifiedAgentRuntime,
)
from sakthai.agent_platform.customizations import (
    CustomizationRegistry,
    RuleDocument,
    SkillSummary,
)
from sakthai.agent_platform.dep_manager import (
    DependencyConfig,
    detect_dependency_manager,
)
from sakthai.agent_platform.harness_exporter import (
    export_harness_agent_spec,
    export_v1_pipeline_step,
    generate_harness_uid,
)
from sakthai.agent_platform.jules_worker import (
    build_apply_commands,
    build_jules_task_command,
    parse_git_repo_url,
    validate_patch_targets,
)
from sakthai.agent_platform.safety import (
    DataLossGuardrail,
    SafetyCheckResult,
)

__all__ = [
    "AgentEngineMode",
    "CustomizationRegistry",
    "DataLossGuardrail",
    "DependencyConfig",
    "RuleDocument",
    "SafetyCheckResult",
    "SkillSummary",
    "UnifiedAgentConfig",
    "UnifiedAgentRuntime",
    "build_apply_commands",
    "build_jules_task_command",
    "detect_dependency_manager",
    "export_harness_agent_spec",
    "export_v1_pipeline_step",
    "generate_harness_uid",
    "parse_git_repo_url",
    "validate_patch_targets",
]
