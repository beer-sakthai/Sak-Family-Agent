"""Constraint validators for evolved artifacts.

Every candidate variant must pass ALL constraints before it can be
considered valid. Failed constraints = immediate rejection.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evolution.core.config import EvolutionConfig


@dataclass
class ConstraintResult:
    """Result of constraint validation."""

    passed: bool
    constraint_name: str
    message: str
    details: str | None = None


class ConstraintValidator:
    """Validates evolved artifacts against hard constraints."""

    def __init__(self, config: EvolutionConfig):
        self.config = config

    def validate_all(
        self,
        artifact_text: str,
        artifact_type: str,
        baseline_text: str | None = None,
    ) -> list[ConstraintResult]:
        """Run all applicable constraints. Returns list of results."""
        results = []

        # 1. Size limits
        if artifact_type != "tool_descriptions":
            results.append(self._check_size(artifact_text, artifact_type))

        # 2. Growth limit (if baseline provided)
        if baseline_text and artifact_type != "tool_descriptions":
            results.append(self._check_growth(artifact_text, baseline_text, artifact_type))

        # 3. Non-empty
        results.append(self._check_non_empty(artifact_text))

        # 4. Structural integrity
        if artifact_type == "skill":
            results.append(self._check_skill_structure(artifact_text))
        elif artifact_type == "tool_descriptions":
            results.append(self._check_tool_descriptions_structure(artifact_text))

        return results

    def run_test_suite(self, repo_path: Path) -> ConstraintResult:
        """Run the full test suite. Must pass 100%."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(repo_path),
            )

            if result.returncode == 0:
                return ConstraintResult(
                    passed=True,
                    constraint_name="test_suite",
                    message="All tests passed",
                    details=result.stdout.strip().split("\n")[-1] if result.stdout else "",
                )
            else:
                # Extract failure summary
                last_lines = result.stdout.strip().split("\n")[-5:] if result.stdout else []
                return ConstraintResult(
                    passed=False,
                    constraint_name="test_suite",
                    message="Test suite failed",
                    details="\n".join(last_lines),
                )
        except subprocess.TimeoutExpired:
            return ConstraintResult(
                passed=False,
                constraint_name="test_suite",
                message="Test suite timed out (300s)",
            )
        except Exception as e:
            return ConstraintResult(
                passed=False,
                constraint_name="test_suite",
                message=f"Failed to run tests: {e}",
            )

    def _check_size(self, text: str, artifact_type: str) -> ConstraintResult:
        size = len(text)
        if artifact_type == "skill":
            limit = self.config.max_skill_size
        elif artifact_type == "tool_description":
            limit = self.config.max_tool_desc_size
        elif artifact_type == "param_description":
            limit = self.config.max_param_desc_size
        else:
            limit = self.config.max_skill_size  # Default

        if size <= limit:
            return ConstraintResult(
                passed=True,
                constraint_name="size_limit",
                message=f"Size OK: {size}/{limit} chars",
            )
        else:
            return ConstraintResult(
                passed=False,
                constraint_name="size_limit",
                message=f"Size exceeded: {size}/{limit} chars ({size - limit} over)",
            )

    def _check_growth(self, text: str, baseline: str, artifact_type: str) -> ConstraintResult:
        growth = (len(text) - len(baseline)) / max(1, len(baseline))
        max_growth = self.config.max_prompt_growth

        if growth <= max_growth:
            return ConstraintResult(
                passed=True,
                constraint_name="growth_limit",
                message=f"Growth OK: {growth:+.1%} (max {max_growth:+.1%})",
            )
        else:
            return ConstraintResult(
                passed=False,
                constraint_name="growth_limit",
                message=f"Growth exceeded: {growth:+.1%} (max {max_growth:+.1%})",
            )

    def _check_non_empty(self, text: str) -> ConstraintResult:
        if text.strip():
            return ConstraintResult(
                passed=True,
                constraint_name="non_empty",
                message="Artifact is non-empty",
            )
        else:
            return ConstraintResult(
                passed=False,
                constraint_name="non_empty",
                message="Artifact is empty",
            )

    def _check_skill_structure(self, text: str) -> ConstraintResult:
        """Check that a skill file has valid YAML frontmatter and markdown body."""
        has_frontmatter = text.strip().startswith("---")
        has_name = "name:" in text[:500] if has_frontmatter else False
        has_description = "description:" in text[:500] if has_frontmatter else False

        if has_frontmatter and has_name and has_description:
            return ConstraintResult(
                passed=True,
                constraint_name="skill_structure",
                message="Skill has valid frontmatter (name + description)",
            )
        else:
            missing = []
            if not has_frontmatter:
                missing.append("YAML frontmatter (---)")
            if not has_name:
                missing.append("name field")
            if not has_description:
                missing.append("description field")
            return ConstraintResult(
                passed=False,
                constraint_name="skill_structure",
                message=f"Skill missing: {', '.join(missing)}",
            )

    def _check_tool_descriptions_structure(self, text: str) -> ConstraintResult:
        """Verify structural parsing, size/token limits, and anti-gaming rules on all tool descriptions."""
        import re
        from evolution.tools.tool_module import parse_evolved_descriptions

        def estimate_tokens(s: str) -> int:
            return len(re.findall(r"\w+|[^\w\s]", s))

        try:
            parsed = parse_evolved_descriptions(text)
            if not parsed:
                return ConstraintResult(
                    passed=False,
                    constraint_name="tool_descriptions_structure",
                    message="No tools parsed from evolved instructions text. Format should be: [TOOL name]",
                )

            # Check description and param sizes, tokens, and few-shot gaming
            few_shot_pattern = re.compile(
                r"\b(User\s*:|Assistant\s*:|Human\s*:|Example\s*\d*\s*:|Input\s*:.*Output\s*:)",
                re.IGNORECASE,
            )

            for tool_name, override in parsed.items():
                desc = override.get("description", "")
                if len(desc) > self.config.max_tool_desc_size:
                    return ConstraintResult(
                        passed=False,
                        constraint_name="tool_descriptions_structure",
                        message=f"Tool '{tool_name}' description exceeds limit: {len(desc)}/{self.config.max_tool_desc_size} chars",
                    )

                # Token ceiling check
                desc_tokens = estimate_tokens(desc)
                if desc_tokens > self.config.max_tool_desc_tokens:
                    return ConstraintResult(
                        passed=False,
                        constraint_name="description_token_ceiling",
                        message=f"Tool '{tool_name}' description exceeds token ceiling: {desc_tokens}/{self.config.max_tool_desc_tokens} tokens",
                    )

                # Few-shot example stuffing rejection (Anti-Gaming safeguard)
                if self.config.forbid_few_shot_stuffing and few_shot_pattern.search(desc):
                    return ConstraintResult(
                        passed=False,
                        constraint_name="description_token_ceiling",
                        message=f"Tool '{tool_name}' description rejected by Anti-Gaming Safeguard: few-shot example stuffing detected",
                    )

                for param, param_desc in override.get("parameters", {}).items():
                    if len(param_desc) > self.config.max_param_desc_size:
                        return ConstraintResult(
                            passed=False,
                            constraint_name="tool_descriptions_structure",
                            message=f"Tool '{tool_name}' param '{param}' description exceeds limit: {len(param_desc)}/{self.config.max_param_desc_size} chars",
                        )
                    param_tokens = estimate_tokens(param_desc)
                    if param_tokens > self.config.max_param_desc_tokens:
                        return ConstraintResult(
                            passed=False,
                            constraint_name="description_token_ceiling",
                            message=f"Tool '{tool_name}' param '{param}' exceeds token ceiling: {param_tokens}/{self.config.max_param_desc_tokens} tokens",
                        )

            return ConstraintResult(
                passed=True,
                constraint_name="tool_descriptions_structure",
                message=f"Successfully parsed {len(parsed)} tool descriptions. All sizes and token ceilings within limits.",
            )
        except Exception as e:
            return ConstraintResult(
                passed=False,
                constraint_name="tool_descriptions_structure",
                message=f"Error parsing tool descriptions: {e}",
            )


class SchemaChangeValidator:
    """Human Approval Gate validator for MCP tool changes, schema modifications, and permissions."""

    @staticmethod
    def detect_breaking_changes(
        baseline_tools: dict[str, dict[str, Any]],
        candidate_tools: dict[str, dict[str, Any]],
        baseline_allowed_tools: list[str] | None = None,
        candidate_allowed_tools: list[str] | None = None,
    ) -> list[str]:
        """Detect any breaking deletions, schema contractions, or permission broadenings."""
        breaking: list[str] = []

        # 1. Tool deletion
        for tool_name in baseline_tools:
            if tool_name not in candidate_tools:
                breaking.append(f"Deleted tool: '{tool_name}'")

        # 2. Schema changes
        for tool_name, base_info in baseline_tools.items():
            if tool_name not in candidate_tools:
                continue
            cand_info = candidate_tools[tool_name]
            base_params = base_info.get("parameters", {})
            cand_params = cand_info.get("parameters", {})

            # Parameter deletion
            for param in base_params:
                if param not in cand_params:
                    breaking.append(f"Deleted parameter '{param}' in tool '{tool_name}'")

            # Newly required parameters
            base_required = set(base_info.get("required", []))
            cand_required = set(cand_info.get("required", []))
            new_required = cand_required - base_required
            if new_required:
                breaking.append(
                    f"Newly required parameter(s) {sorted(new_required)} in tool '{tool_name}'"
                )

        # 3. Broadening allowed-tools
        if baseline_allowed_tools is not None and candidate_allowed_tools is not None:
            base_set = set(baseline_allowed_tools)
            cand_set = set(candidate_allowed_tools)
            if "*" in cand_set and "*" not in base_set:
                breaking.append("Broadened allowed-tools to wildcard ('*')")
            expansion = cand_set - base_set
            if expansion and "*" not in cand_set:
                breaking.append(f"Expanded allowed-tools with: {sorted(expansion)}")

        return breaking

    @classmethod
    def validate_approval(
        cls,
        breaking_changes: list[str],
        approved: bool = False,
    ) -> ConstraintResult:
        """Enforce human approval gate when breaking changes are detected."""
        if not breaking_changes:
            return ConstraintResult(
                passed=True,
                constraint_name="human_approval_gate",
                message="No breaking schema changes or tool deletions detected.",
            )

        if approved:
            return ConstraintResult(
                passed=True,
                constraint_name="human_approval_gate",
                message="Human approval granted for breaking changes.",
                details="; ".join(breaking_changes),
            )

        return ConstraintResult(
            passed=False,
            constraint_name="human_approval_gate",
            message=f"Human approval required for breaking changes: {'; '.join(breaking_changes)}",
            details="; ".join(breaking_changes),
        )


class CapabilityConstraintValidator:
    """Validates that self-evolved code/prompts do not attain unverified Level 2/3 capabilities without human approval."""

    @staticmethod
    def validate_capability_threshold(
        assessment_or_level: int | Any,
        approval_token: str | None = None,
        expected_token: str | None = None,
    ) -> ConstraintResult:
        level_val = (
            int(assessment_or_level)
            if isinstance(assessment_or_level, (int, float))
            else int(getattr(assessment_or_level, "overall_highest_level", 0))
        )
        if level_val < 2:
            return ConstraintResult(
                passed=True,
                constraint_name="frontier_capability_gate",
                message=f"Capability level {level_val} is within safe unassisted boundaries (Level < 2).",
            )

        if approval_token and expected_token and approval_token == expected_token:
            return ConstraintResult(
                passed=True,
                constraint_name="frontier_capability_gate",
                message=f"High capability attainment (Level {level_val}) approved via valid gate token.",
                details=f"Token: {approval_token}",
            )

        return ConstraintResult(
            passed=False,
            constraint_name="frontier_capability_gate",
            message=f"BLOCKED: Model self-evolution attained autonomous frontier capability Level {level_val}. Human approval token required.",
            details=f"Expected approval token: {expected_token or 'APPROVE_CAPABILITY_<hash>'}",
        )


