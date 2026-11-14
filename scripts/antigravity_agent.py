#!/usr/bin/env python3
"""Standalone Google Antigravity (AGY) Agent Runner.

Usage:
    python scripts/antigravity_agent.py "What are the capabilities of House of Sak?"
    python scripts/antigravity_agent.py --backend openai --base-url http://localhost:11434/v1 "Hi!"
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path so it works out of the box
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas"))
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.agent_platform.antigravity_agent import (  # noqa: E402
    AI_STUDIO_KEY_URL,
    AntigravityAgentRunner,
    AntigravityRunnerConfig,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an autonomous Google Antigravity AI Agent with safety guardrails."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Inspect the active workspace and list available tools and skills.",
        help="Prompt instruction to send to the agent.",
    )
    parser.add_argument(
        "--backend",
        "-b",
        choices=["hosted", "openai", "litert"],
        default="hosted",
        help="Backend execution engine: 'hosted' (Gemini), 'openai' (Ollama), or 'litert'.",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gemini-2.5-flash",
        help="Model identifier (default: gemini-2.5-flash).",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for OpenAI-compatible server (e.g. http://localhost:11434/v1).",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help="Filesystem path to local model weights (required for LiteRT backend).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Explicit Gemini API key (defaults to GEMINI_API_KEY environment variable).",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if args.backend == "hosted" and not api_key:
        print("\n⚠️  [Authentication Required]")
        print("To run with hosted Gemini models, set your GEMINI_API_KEY environment variable,")
        print(f"or create an API key at Google AI Studio: {AI_STUDIO_KEY_URL}")
        print("Alternatively, pass '--backend openai' to connect to local Ollama.\n")
        sys.exit(1)

    config = AntigravityRunnerConfig(
        backend=args.backend,
        model=args.model,
        api_key=api_key,
        base_url=args.base_url,
        model_path=args.model_path,
        workspace_dir=REPO_ROOT,
    )

    runner = AntigravityAgentRunner(config=config)
    print(f"\n🚀 Launching Google Antigravity Agent [{args.backend.upper()}: {args.model}]...")
    print(f"Prompt: {args.prompt}\n")

    try:
        async for token in runner.stream_chat(args.prompt):
            sys.stdout.write(token)
            sys.stdout.flush()
        print("\n")
    except Exception as exc:
        print(f"\n❌ Agent execution error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
