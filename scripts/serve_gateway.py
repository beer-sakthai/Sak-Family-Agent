#!/usr/bin/env python3
"""Standalone runner for the SakThai Runtime Gateway.

Serves an OpenAI-compatible and REST API Gateway for all 6 personas and agent tools.

Usage:
    python scripts/serve_gateway.py [--host 127.0.0.1] [--port 8080] [--token TOKEN]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Explicit canonical package path insertion as required by monorepo guidelines
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.gateway.config import resolve_gateway_config  # noqa: E402
from sakthai.gateway.server import RuntimeGatewayServer  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the SakThai Runtime Gateway (OpenAI-compatible & REST API)."
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host address to bind (default: 127.0.0.1)"
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--token", default=None, help="Bearer token for API authorization")
    parser.add_argument("--cors", default=None, help="CORS origin header")
    parser.add_argument("--default-persona", default="sakthai", help="Default target persona")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = resolve_gateway_config(
        host=args.host,
        port=args.port,
        bearer_token=args.token,
        cors_origin=args.cors,
        default_persona=args.default_persona,
        workspace_dir=REPO_ROOT,
    )

    server = RuntimeGatewayServer(config=config)
    print(f"🚀 SakThai Runtime Gateway starting on http://{config.host}:{config.port}")
    print(f"  Default Persona: {config.default_persona}")
    print(f"  Auth Mode:       {'Bearer Token' if config.bearer_token else 'Open Access'}")
    print("Press Ctrl+C to stop.\n")

    try:
        server.start(background=False)
    except KeyboardInterrupt:
        print("\nStopping Runtime Gateway...")
        server.shutdown()
        print("✓ Runtime Gateway stopped cleanly.")


if __name__ == "__main__":
    main()
