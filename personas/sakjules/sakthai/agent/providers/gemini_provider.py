"""Google Gemini provider backend."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

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
        # Content that is neither a str nor a list contributes no parts; unknown
        # block types within a list are skipped. Both are deliberate,
        # forward-compatible no-ops rather than hard errors. A fallback empty
        # text part is added below so the Content stays schema-compliant.
        if isinstance(content, str):
            parts.append(types.Part(text=content))
        elif isinstance(content, list):
            for block in content:
                block_type = block_field(block, "type")
                if block_type == "text":
                    parts.append(types.Part(text=block_field(block, "text")))
                elif block_type == "tool_use":
                    parts.append(
                        types.Part(
                            function_call=types.FunctionCall(
                                name=block_field(block, "name"),
                                args=dict(block_field(block, "input", {}) or {}),
                            )
                        )
                    )
                elif block_type == "tool_result":
                    tool_use_id = block_field(block, "tool_use_id")
                    parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=find_tool_name_by_id(messages, tool_use_id),
                                response={"result": block_field(block, "content")},
                            )
                        )
                    )
        if not parts:
            # Gemini rejects a Content with an empty parts list (400); keep one
            # empty text part so the payload stays valid.
            parts.append(types.Part(text=""))
        if any(getattr(p, "function_response", None) is not None for p in parts):
            gemini_role = "tool"
        elif role == "assistant":
            gemini_role = "model"
        else:
            gemini_role = "user"
        contents.append(types.Content(role=gemini_role, parts=parts))
    return contents


def _stop_reason(has_tool_call: bool, finish_reason: Any) -> str:
    """Map Gemini's tool-call/finish signals to a normalised stop reason."""
    if has_tool_call:
        return "tool_use"
    if finish_reason == "MAX_TOKENS":
        return "max_tokens"
    return "end_turn"


def call_gemini(
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
    on_token: Callable[[str], None] | None = None,
) -> Response:
    """Make one Gemini call, normalised to :class:`Response`.

    When ``on_token`` is provided, the response is streamed via
    ``client.models.generate_content_stream`` and each text delta is forwarded to
    the callback; the assembled result is identical in shape to the non-streaming
    ``generate_content`` response (a single text block plus any tool_use blocks).
    """
    from google.genai import types

    def _clean_schema(schema: Any) -> Any:
        if isinstance(schema, dict):
            cleaned = schema.copy()
            cleaned.pop("$schema", None)
            cleaned.pop("$id", None)
            return cleaned
        return schema

    declarations: list[Any] = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters=_clean_schema(t.input_schema),
                )
            ]
        )
        for t in tools
    ]
    contents = to_gemini_contents(messages)
    config = types.GenerateContentConfig(system_instruction=system, tools=declarations)

    def _generate() -> Response:
        raw = client.models.generate_content(model=model, contents=contents, config=config)
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
        return Response(
            stop_reason=_stop_reason(has_tool_call, candidate.finish_reason),
            content=blocks,
            usage=extract_usage(raw),
        )

    def _stream() -> Response:
        text_parts: list[str] = []
        tool_blocks: list[Any] = []
        finish_reason: Any = None
        last_chunk: Any = None
        fc_index = 0
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config
        ):
            last_chunk = chunk
            for candidate in chunk.candidates or []:
                if candidate.finish_reason is not None:
                    finish_reason = candidate.finish_reason
                parts = (candidate.content.parts if candidate.content else None) or []
                for part in parts:
                    if part.text:
                        text_parts.append(part.text)
                        if on_token is not None:
                            on_token(part.text)
                    elif part.function_calls:
                        for fc in part.function_calls:
                            tool_blocks.append(
                                Block(
                                    "tool_use",
                                    id=f"call_{fc.name}_{iteration}_{fc_index}",
                                    name=fc.name,
                                    input=dict(fc.args or {}),
                                )
                            )
                            fc_index += 1
        blocks: list[Any] = []
        if text_parts:
            # Deltas are concatenated into one block so downstream text extraction
            # doesn't see spurious newlines between streamed chunks.
            blocks.append(Block("text", text="".join(text_parts)))
        blocks.extend(tool_blocks)
        return Response(
            stop_reason=_stop_reason(bool(tool_blocks), finish_reason),
            content=blocks,
            usage=extract_usage(last_chunk),
        )

    try:
        return with_retry(_stream if on_token is not None else _generate)  # type: ignore[no-any-return]
    except AgentError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Gemini API call failed: %s", exc)
        raise AgentError(f"Gemini API call failed: {exc}") from exc
