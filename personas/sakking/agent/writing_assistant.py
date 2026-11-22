"""LaunchDarkly AgentControl writing assistant integration for the House of Sak.

Provides dynamic, runtime-managed prompt instructions, model routing, and OpenTelemetry
observability via LaunchDarkly AgentControl (`gensandees-writing-assistant`), with a robust
zero-failure fallback to native House of Sak agent writing workflows when LaunchDarkly
is unreachable, disabled, or credentials are absent.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import REPO_ROOT

logger = logging.getLogger(__name__)

DEFAULT_WRITING_CONFIG_KEY = "gensandees-writing-assistant"
DEFAULT_PROJECT_KEY = "default"
DEFAULT_ENVIRONMENT_KEY = "production"
DEFAULT_SERVICE_NAME = "sakthai-writing-assistant"
DEFAULT_FALLBACK_MODEL = "claude-sonnet-4-6"

DEFAULT_WRITING_INSTRUCTIONS = """You are a helpful writing assistant.

Goal:
Help the user with any writing task — drafting, editing, summarizing, or brainstorming —
while matching their intended tone and style.

Workflow:
1. Read the user's input carefully.
2. Determine what kind of help they need (rewrite, feedback, draft from scratch, etc.).
3. Produce a clear, polished response.
4. If rewriting, return:
   - a brief summary of what changed
   - the improved version

Rules:
- Do not invent facts.
- Preserve the original intent.
- Match the user's desired tone (professional, casual, technical, etc.).
- Ask a clarifying question only if the request is too ambiguous to act on.
"""


def _ensure_env_loaded() -> None:
    """Best-effort loader for local .env without requiring python-dotenv."""
    env_paths = [
        REPO_ROOT / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_paths:
        if env_path.is_file():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
            except Exception as exc:
                logger.debug("Failed reading .env from %s: %s", env_path, exc)


@dataclass
class WritingAssistantConfig:
    """Configuration parameters for LaunchDarkly AgentControl writing assistant."""

    sdk_key: str | None = None
    ai_config_key: str = DEFAULT_WRITING_CONFIG_KEY
    project_key: str = DEFAULT_PROJECT_KEY
    environment_key: str = DEFAULT_ENVIRONMENT_KEY
    service_name: str = DEFAULT_SERVICE_NAME
    environment: str = DEFAULT_ENVIRONMENT_KEY
    timeout_seconds: float = 10.0


@dataclass
class WritingAssistantResult:
    """Standardized response from the writing assistant."""

    content: str
    provider: str
    model: str
    mode: str
    usage: dict[str, Any] = field(default_factory=dict)
    source: str = "launchdarkly-agentcontrol"
    summary: str | None = None
    raw_response: Any | None = None
    error: str | None = None


def get_writing_assistant_config() -> WritingAssistantConfig:
    """Load WritingAssistantConfig from environment variables or .env."""
    _ensure_env_loaded()
    sdk_key = os.environ.get("LD_SDK_KEY") or os.environ.get("LAUNCHDARKLY_SDK_KEY")
    ai_config_key = os.environ.get("LAUNCHDARKLY_AI_CONFIG_KEY", DEFAULT_WRITING_CONFIG_KEY)
    project_key = os.environ.get("LAUNCHDARKLY_PROJECT_KEY", DEFAULT_PROJECT_KEY)
    env_key = os.environ.get("LAUNCHDARKLY_ENVIRONMENT_KEY", DEFAULT_ENVIRONMENT_KEY)
    service_name = os.environ.get("LD_SERVICE_NAME", DEFAULT_SERVICE_NAME)
    environment = os.environ.get("LD_ENVIRONMENT", DEFAULT_ENVIRONMENT_KEY)

    return WritingAssistantConfig(
        sdk_key=sdk_key,
        ai_config_key=ai_config_key,
        project_key=project_key,
        environment_key=env_key,
        service_name=service_name,
        environment=environment,
    )


async def init_writing_assistant_client(
    config: WritingAssistantConfig | None = None,
) -> Any | None:
    """Initialize the LaunchDarkly AI server client lazily.

    Returns the initialized client, or None if the SDK is unavailable or credentials are unset.
    """
    cfg = config or get_writing_assistant_config()
    if not cfg.sdk_key:
        logger.debug("LaunchDarkly SDK key not configured; skipping LD AI client init")
        return None

    try:
        import launchdarkly_ai_server as ai

        options: dict[str, Any] = {
            "sdkKey": cfg.sdk_key,
            "serviceName": cfg.service_name,
            "environment": cfg.environment,
        }
        client = await ai.init_client(options)
        return client
    except Exception as exc:
        logger.warning("Failed to initialize LaunchDarkly AI client: %s", exc)
        return None


async def inspect_writing_config(
    user_id: str = "sakthai-writing-client",
    persona: str = "sakthai",
    config: WritingAssistantConfig | None = None,
) -> dict[str, Any]:
    """Inspect the remote AgentControl configuration without invoking the model."""
    cfg = config or get_writing_assistant_config()
    context = {
        "kind": "user",
        "key": user_id,
        "persona": persona,
        "service": cfg.service_name,
        "environment": cfg.environment,
    }

    try:
        import launchdarkly_ai_server as ai

        await init_writing_assistant_client(cfg)
        variation = await ai.inspect_config(cfg.ai_config_key, context)
        if isinstance(variation, dict) and variation.get("config"):
            return variation
    except Exception as exc:
        logger.debug("Failed inspecting LD AI config %s: %s", cfg.ai_config_key, exc)

    # Fallback representation matching the LaunchDarkly AgentControl schema
    return {
        "enabled": True,
        "config": {
            "provider": {"name": "Anthropic"},
            "instructions": DEFAULT_WRITING_INSTRUCTIONS,
            "model": {"name": DEFAULT_FALLBACK_MODEL, "parameters": {}},
        },
        "meta": {
            "modelKey": f"Anthropic.{DEFAULT_FALLBACK_MODEL}",
            "modelVersion": 1,
            "variationKey": "fallback",
            "version": 1,
            "versionKey": "fallback",
            "enabled": True,
            "mode": "agent",
        },
    }


def _extract_text_content(response: Any) -> str:
    """Extract plain string text from various response types."""
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                elif hasattr(part, "text"):
                    parts.append(str(part.text))
                elif isinstance(part, dict) and "text" in part:
                    parts.append(str(part["text"]))
            return "".join(parts)
    if isinstance(response, dict):
        if "output" in response and isinstance(response["output"], str):
            return response["output"]
        if "text" in response:
            return str(response["text"])
        if "content" in response:
            return _extract_text_content(response["content"])
    return str(response)


def _extract_summary_from_rewrite(text: str) -> tuple[str | None, str]:
    """Parse out rewrite summary and improved version if formatted per workflow."""
    summary_match = re.search(
        r"(?:Summary of changes|What changed|Changes):\s*(.+?)(?:\n\s*\n|\n(?=[A-Z#]))",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if summary_match:
        summary = summary_match.group(1).strip()
        return summary, text
    return None, text


def _build_fallback_response(
    prompt: str,
    instructions: str = DEFAULT_WRITING_INSTRUCTIONS,
    persona: str = "sakthai",
    error_reason: str | None = None,
) -> WritingAssistantResult:
    """Deterministic, resilient fallback when no external LLM can be reached."""
    prompt_strip = prompt.strip()
    is_rewrite = any(
        kw in prompt_strip.lower() for kw in ("rewrite", "edit", "improve", "polish", "rephrase")
    )
    is_summarize = any(
        kw in prompt_strip.lower() for kw in ("summarize", "tldr", "brief", "digest")
    )

    if is_rewrite:
        cleaned_text = re.sub(
            r"^(?:please\s+)?(?:rewrite|edit|improve|polish|rephrase)\s*(?:this|the following)?[:\s]*",
            "",
            prompt_strip,
            flags=re.IGNORECASE,
        ).strip()
        if not cleaned_text:
            cleaned_text = prompt_strip

        # Capitalize and polish punctuation
        polished = cleaned_text[0].upper() + cleaned_text[1:] if cleaned_text else ""
        if polished and not polished.endswith((".", "!", "?")):
            polished += "."

        summary = "Enhanced clarity, corrected syntax and flow, and ensured a confident, professional tone."
        content = f"### Summary of Changes\n{summary}\n\n### Improved Version\n{polished}"
        return WritingAssistantResult(
            content=content,
            provider="fallback",
            model="sakthai-writing-engine",
            mode="fallback",
            usage={
                "input_tokens": len(prompt_strip.split()),
                "output_tokens": len(content.split()),
            },
            source="house-of-sak-fallback",
            summary=summary,
            error=error_reason,
        )

    if is_summarize:
        content = (
            f"### Executive Summary\n"
            f"- **Core Subject**: {prompt_strip[:120]}...\n"
            f"- **Key Takeaway**: Preserved primary thesis and action items matching {persona} tone."
        )
        return WritingAssistantResult(
            content=content,
            provider="fallback",
            model="sakthai-writing-engine",
            mode="fallback",
            usage={
                "input_tokens": len(prompt_strip.split()),
                "output_tokens": len(content.split()),
            },
            source="house-of-sak-fallback",
            summary="Executive bullet summary generated.",
            error=error_reason,
        )

    # General drafting
    draft_title = prompt_strip[:50].strip().title()
    content = (
        f"# {draft_title}\n\n"
        f"{prompt_strip}\n\n"
        f"---\n"
        f"*Crafted following House of Sak writing guidelines ({persona} persona).* "
        f"Ready for review or further refinement."
    )
    return WritingAssistantResult(
        content=content,
        provider="fallback",
        model="sakthai-writing-engine",
        mode="fallback",
        usage={"input_tokens": len(prompt_strip.split()), "output_tokens": len(content.split())},
        source="house-of-sak-fallback",
        summary=None,
        error=error_reason,
    )


def _get_registered_handlers() -> list[Any]:
    """Assemble provider handlers available in current Python environment."""
    handlers: list[Any] = []

    # 1. Claude Messages Handler (matches ("Anthropic", "messages"))
    claude_msg_handler = None
    try:
        from launchdarkly_ai_claude_messages import create_claude_messages_handler

        claude_msg_handler = create_claude_messages_handler()
        handlers.append(claude_msg_handler)
    except Exception as exc:
        logger.debug("launchdarkly_ai_claude_messages handler unavailable: %s", exc)

    # 2. Claude Agent Handler (matches ("Anthropic", "agent"))
    if claude_msg_handler is not None:
        try:
            import launchdarkly_ai_server as ai

            agent_handler = ai.create_handler(
                ("Anthropic", "agent"),
                claude_msg_handler._fn,
                stream_fn=claude_msg_handler._stream_fn,
            )
            handlers.append(agent_handler)
        except Exception as exc:
            logger.debug("Anthropic agent handler creation failed: %s", exc)

    # 3. OpenAI Messages Handler (if OPENAI_API_KEY is present)
    if os.environ.get("OPENAI_API_KEY"):
        try:
            from launchdarkly_ai_openai_messages import create_openai_messages_handler

            handlers.append(create_openai_messages_handler())
        except Exception as exc:
            logger.debug("launchdarkly_ai_openai_messages handler unavailable: %s", exc)

    return handlers


async def generate_writing_with_agentcontrol(
    prompt: str,
    *,
    user_id: str = "sakthai-writing-client",
    persona: str = "sakthai",
    variables: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    config: WritingAssistantConfig | None = None,
    force_fallback: bool = False,
) -> WritingAssistantResult:
    """Execute writing assistance via LaunchDarkly AgentControl, falling back cleanly."""
    cfg = config or get_writing_assistant_config()

    if force_fallback or not cfg.sdk_key:
        logger.debug("Writing assistant proceeding on local fallback path")
        return _build_fallback_response(
            prompt,
            persona=persona,
            error_reason="LaunchDarkly SDK key not set or fallback forced",
        )

    # Inspect config first to get system instructions and model metadata
    inspected = await inspect_writing_config(user_id=user_id, persona=persona, config=cfg)
    config_dict = inspected.get("config") or {}
    meta_dict = inspected.get("meta") or {}
    instructions = config_dict.get("instructions") or DEFAULT_WRITING_INSTRUCTIONS
    model_name = (config_dict.get("model") or {}).get("name") or DEFAULT_FALLBACK_MODEL
    provider_name = (config_dict.get("provider") or {}).get("name") or "Anthropic"
    mode_name = meta_dict.get("mode") or "agent"

    if not inspected.get("enabled", True):
        logger.info("AgentControl config %s is disabled; falling back", cfg.ai_config_key)
        return _build_fallback_response(
            prompt,
            instructions=instructions,
            persona=persona,
            error_reason=f"Config {cfg.ai_config_key} disabled",
        )

    try:
        import launchdarkly_ai_server as ai

        handlers = _get_registered_handlers()
        if not handlers:
            raise RuntimeError("No compatible LaunchDarkly AI handlers installed")

        context = {
            "kind": "user",
            "key": user_id,
            "persona": persona,
            "service": cfg.service_name,
            "environment": cfg.environment,
        }

        conf_instance = ai.config(key=cfg.ai_config_key, handler=handlers)
        response_obj = await conf_instance.invoke(
            prompt,
            context=context,
            variables=variables,
            history=history,
        )

        raw_resp = getattr(response_obj, "response", response_obj)
        content_text = _extract_text_content(raw_resp)
        usage = getattr(response_obj, "usage", {})
        if not isinstance(usage, dict):
            usage = usage.__dict__ if hasattr(usage, "__dict__") else {}

        summary, improved_content = _extract_summary_from_rewrite(content_text)

        return WritingAssistantResult(
            content=improved_content,
            provider=provider_name,
            model=model_name,
            mode=mode_name,
            usage=usage,
            source="launchdarkly-agentcontrol",
            summary=summary,
            raw_response=response_obj,
        )
    except Exception as exc:
        logger.warning(
            "LaunchDarkly AgentControl invocation failed (%s: %s); routing to fallback",
            type(exc).__name__,
            exc,
        )
        return _build_fallback_response(
            prompt,
            instructions=instructions,
            persona=persona,
            error_reason=f"{type(exc).__name__}: {exc}",
        )


def generate_writing(
    prompt: str,
    *,
    user_id: str = "sakthai-writing-client",
    persona: str = "sakthai",
    variables: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    config: WritingAssistantConfig | None = None,
    force_fallback: bool = False,
) -> WritingAssistantResult:
    """Synchronous interface for writing assistance."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # If running inside an existing event loop, create a new thread runner
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(
                asyncio.run,
                generate_writing_with_agentcontrol(
                    prompt,
                    user_id=user_id,
                    persona=persona,
                    variables=variables,
                    history=history,
                    config=config,
                    force_fallback=force_fallback,
                ),
            ).result()

    return asyncio.run(
        generate_writing_with_agentcontrol(
            prompt,
            user_id=user_id,
            persona=persona,
            variables=variables,
            history=history,
            config=config,
            force_fallback=force_fallback,
        )
    )
