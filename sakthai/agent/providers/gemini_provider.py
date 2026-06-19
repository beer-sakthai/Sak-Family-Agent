"""Google Gemini provider backend."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from ..tools import Tool
from ..usage import extract_usage
from .base import AgentError, Block, Response, block_field, find_tool_name_by_id, logger, with_retry


def to_gemini_contents(messages: list[dict[str, Any]]) -> list[Any]:
    """Adapt the provider-agnostic message list to Gemini ``Content`` parts."""
    from google.genai import types

    contents = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        parts = []

        if isinstance(content, str):
            parts.append(types.Part(text=content))
        elif isinstance(content, list):
            for block in content:
                part = _block_to_part(block, messages)
                if part:
                    parts.append(part)

        gemini_role = _determine_role(role, parts)
        contents.append(types.Content(role=gemini_role, parts=parts))
    return contents


def _block_to_part(block: dict[str, Any], messages: list[dict[str, Any]]) -> Any:
    """Convert a single content block to a Gemini Part."""
    from google.genai import types

    block_type = block_field(block, "type")
    if block_type == "text":
        return types.Part(text=block_field(block, "text"))
    if block_type == "tool_use":
        return types.Part(
            function_call=types.FunctionCall(
                name=block_field(block, "name"),
                args=dict(block_field(block, "input", {}) or {}),
            )
        )
    if block_type == "tool_result":
        tool_use_id = block_field(block, "tool_use_id")
        return types.Part(
            function_response=types.FunctionResponse(
                name=find_tool_name_by_id(messages, tool_use_id),
                response={"result": block_field(block, "content")},
            )
        )
    return None


def _determine_role(role: str, parts: list[Any]) -> str:
    """Determine the Gemini role for a message based on its parts and original role."""
    if any(getattr(p, "function_response", None) is not None for p in parts):
        return "tool"
    if role == "assistant":
        return "model"
    return "user"


def call_gemini(
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
    on_token: Callable[[str], None] | None = None,
) -> Response:
    """Make one Gemini generate_content call, normalised to :class:`Response`.

    ``on_token`` is accepted for interface parity; Gemini streaming is not yet
    implemented.
    """
    from google.genai import types

    declarations = _create_tool_declarations(tools)
    try:
        raw = with_retry(
            client.models.generate_content,
            model=model,
            contents=to_gemini_contents(messages),
            config=types.GenerateContentConfig(system_instruction=system, tools=declarations),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Gemini API call failed: %s", exc)
        raise AgentError(f"Gemini API call failed: {exc}") from exc

    return _parse_gemini_response(raw, iteration)


def _create_tool_declarations(tools: tuple[Tool, ...]) -> list[Any]:
    """Create Gemini tool declarations from Tool objects."""
    from google.genai import types

    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t.name, description=t.description, parameters=cast(Any, t.input_schema)
                )
            ]
        )
        for t in tools
    ]


def _parse_gemini_response(raw: Any, iteration: int) -> Response:
    """Parse raw Gemini response into a Response object."""
    if not raw.candidates:
        raise AgentError("Gemini returned no candidates.")

    candidate = raw.candidates[0]
    blocks: list[Any] = []
    has_tool_call = False
    parts = (candidate.content.parts if candidate.content else None) or []

    for idx, part in enumerate(parts):
        if part.text:
            blocks.append(Block("text", text=part.text))
        elif part.function_calls:
            has_tool_call = True
            for fc in part.function_calls:
                blocks.append(
                    Block(
                        "tool_use",
                        id=f"call_{fc.name}_{iteration}_{idx}",
                        name=fc.name,
                        input=dict(fc.args or {}),
                    )
                )

    if has_tool_call:
        stop_reason = "tool_use"
    elif candidate.finish_reason == "MAX_TOKENS":
        stop_reason = "max_tokens"
    else:
        stop_reason = "end_turn"

    return Response(stop_reason=stop_reason, content=blocks, usage=extract_usage(raw))
