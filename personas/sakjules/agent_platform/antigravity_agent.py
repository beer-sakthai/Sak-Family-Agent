"""Standalone Google Antigravity (AGY) Agent integration and runner.

Integrates the Google Antigravity SDK with SakThai safety guardrails,
dynamic backend selection (hosted Gemini, LiteRT on-device, or local OpenAI/Ollama),
and progressive disclosure skills.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.antigravity import (
    Agent,
    AgentConfig,
    CapabilitiesConfig,
    LiteRTAgentConfig,
    LocalAgentConfig,
    LocalOpenAIAgentConfig,
)

from sakthai.agent_platform.customizations import CustomizationRegistry
from sakthai.agent_platform.safety import DataLossGuardrail

AI_STUDIO_KEY_URL = "https://aistudio.google.com/app/api-keys"


@dataclass
class AntigravityRunnerConfig:
    backend: str = "hosted"  # 'hosted', 'litert', or 'openai'
    model: str = "gemini-2.5-flash"
    api_key: str | None = None
    base_url: str | None = None  # For Ollama / Local OpenAI (e.g. http://localhost:11434/v1)
    model_path: str | None = None  # For LiteRT local model
    workspace_dir: Path | None = None
    system_instructions: str = (
        "You are an autonomous AI software engineering agent operating with House of Sak."
    )
    allow_terminal: bool = False
    allow_filesystem: bool = True


class AntigravityAgentRunner:
    """Manages the lifecycle and execution of a Google Antigravity Agent."""

    def __init__(
        self,
        config: AntigravityRunnerConfig | None = None,
        guardrail: DataLossGuardrail | None = None,
    ):
        self.config = config or AntigravityRunnerConfig()
        self.guardrail = guardrail or DataLossGuardrail()
        self.workspace = (self.config.workspace_dir or Path.cwd()).resolve()

    def create_safe_tools(self) -> list[Callable[..., Any]]:
        """Constructs tools guarded by DataLossGuardrail."""
        guard = self.guardrail
        workspace_root = self.workspace

        def safe_run_command(command: str, approval_token: str | None = None) -> str:
            """Executes a shell command after validating safety policies.

            Args:
                command: Shell command string to execute.
                approval_token: Optional bypass token (APPROVE_<digest>) for destructive actions.
            """
            check = guard.verify_or_halt(command, approval_token=approval_token)
            if check.blocked:
                expected = guard.generate_approval_token(command)
                return (
                    f"BLOCKED by DataLossGuardrail: {check.reason}. "
                    f"Impact: {check.impact}. To authorize, pass approval_token='{expected}'"
                )
            return f"Command permitted: {command}"

        def safe_read_file(relative_path: str) -> str:
            """Reads a text file inside the active workspace.

            Args:
                relative_path: File path relative to workspace root.
            """
            target = (workspace_root / relative_path).resolve()
            if not target.is_relative_to(workspace_root):
                return f"Access Denied: Path '{relative_path}' resolves outside workspace."
            if not target.exists():
                return f"File not found: '{relative_path}'"
            if not target.is_file():
                return f"Path is not a regular file: '{relative_path}'"
            try:
                content = target.read_text(encoding="utf-8")
                return content[:20_000]
            except Exception as err:
                return f"Error reading file: {err}"

        def inspect_workspace() -> str:
            """Returns a brief summary of files and skills available in the workspace."""
            reg = CustomizationRegistry(workspace_root=workspace_root)
            skills = reg.list_available_skills()
            skill_names = [s.name for s in skills]
            return f"Workspace: {workspace_root.name} | Skills: {skill_names}"

        return [safe_run_command, safe_read_file, inspect_workspace]

    def build_sdk_config(self) -> AgentConfig:
        """Constructs the appropriate Antigravity AgentConfig."""
        tools = self.create_safe_tools()
        caps = CapabilitiesConfig(
            allow_terminal=self.config.allow_terminal,
            allow_filesystem=self.config.allow_filesystem,
        )

        backend = self.config.backend.lower()
        if backend == "hosted":
            api_key = (
                self.config.api_key
                or os.environ.get("GEMINI_API_KEY")
                or os.environ.get("GOOGLE_API_KEY")
            )
            return LocalAgentConfig(
                model=self.config.model,
                api_key=api_key,
                system_instructions=self.config.system_instructions,
                capabilities=caps,
                tools=tools,
            )
        elif backend in ("openai", "ollama"):
            base_url = self.config.base_url or os.environ.get(
                "OLLAMA_BASE_URL", "http://localhost:11434/v1"
            )
            return LocalOpenAIAgentConfig(
                model=self.config.model or "gemma-2b",
                base_url=base_url,
                system_instructions=self.config.system_instructions,
                capabilities=caps,
                tools=tools,
            )
        elif backend == "litert":
            if not self.config.model_path:
                raise ValueError("LiteRT backend requires 'model_path' pointing to local model.")
            return LiteRTAgentConfig(
                model_path=self.config.model_path,
                system_instructions=self.config.system_instructions,
                capabilities=caps,
                tools=tools,
            )
        else:
            raise ValueError(
                f"Unknown backend '{self.config.backend}'. Supported: 'hosted', 'openai', 'litert'"
            )

    async def stream_chat(self, prompt: str) -> AsyncIterator[str]:
        """Streams response tokens from the Antigravity agent."""
        sdk_config = self.build_sdk_config()
        async with Agent(sdk_config) as agent:
            response = await agent.chat(prompt)
            async for token in response:
                yield str(token)
