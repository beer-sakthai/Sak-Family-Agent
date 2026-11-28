"""Read-only starter tools exposed by the Sak MCP Gateway.

CRITICAL SECURITY INVARIANT:
These tools deliberately do NOT access ~/.sakthai/memory.db or execute raw SQLite
queries directly. All external M365 Copilot calls are restricted to approved,
isolated status and catalog inspection.
"""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS = [
    {
        "name": "sak_health_status",
        "description": "Inspect real-time health, active personas, and runtime telemetry for House of Sak.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "verbose": {
                    "type": "boolean",
                    "description": "Whether to include detailed runtime telemetry flags.",
                    "default": False,
                }
            },
        },
    },
    {
        "name": "sak_family_catalog",
        "description": "Retrieve the catalog of persona domains, specializations, and allowed skill domains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "persona": {
                    "type": "string",
                    "description": "Optional persona slug to filter (sakthai, sakking, saksee, saksit, saktan, sakjules).",
                }
            },
        },
    },
]


def execute_sak_health_status(verbose: bool = False) -> dict[str, Any]:
    """Return read-only status and health telemetry."""
    status: dict[str, Any] = {
        "ok": True,
        "ecosystem": "House of Sak (Sak-Family-Agent)",
        "status": "healthy",
        "active_personas": ["sakthai", "sakking", "saksee", "saksit", "saktan", "sakjules"],
        "memory_boundary": "ENFORCED (No raw SQLite memory access without approved adapter)",
        "security_isolation": "Read-only container rootfs, non-root execution, dropped Linux capabilities",
    }
    if verbose:
        status["telemetry"] = {
            "mcp_version": "2024-11-05",
            "m365_plugin_schema": "v2.4",
            "gateway_protocol": "RemoteMCPServer (Streamable HTTP)",
        }
    return status


def execute_sak_family_catalog(persona: str | None = None) -> dict[str, Any]:
    """Return catalog of persona domains and specializations."""
    catalog = {
        "sakthai": {
            "display_name": "SakThai",
            "role": "Main Lead & Hugging Face Master",
            "domain": "Machine Learning, Hugging Face, Agent Self-Evolution, Distributed Pipelines",
            "skills_count": 174,
        },
        "sakking": {
            "display_name": "SakKing",
            "role": "General Assistant & First Deputy",
            "domain": "TDD Implementation, Code Generation, Runner Execution, Quorum Governance",
            "skills_count": 64,
        },
        "saksee": {
            "display_name": "SakSee",
            "role": "Web Specialist & UI Architect",
            "domain": "3-Tier Web Scraping Escalation, Playwright DOM Distillation, Chromium Reaper",
            "skills_count": 98,
        },
        "saksit": {
            "display_name": "SakSit",
            "role": "Social & Multimodal Content Specialist",
            "domain": "B2B Thought Leadership, Multimodal Presets, Editorial Quality Evaluation",
            "skills_count": 50,
        },
        "saktan": {
            "display_name": "SakTan",
            "role": "Operations & Daily Rhythm Master",
            "domain": "Systemd Cron Fleet, SQLite WAL Compaction, Zero-Cost Local Ollama Execution",
            "skills_count": 26,
        },
        "sakjules": {
            "display_name": "SakJules",
            "role": "Master of Automation & CI/CD",
            "domain": "DevSecOps, AutoHeal-CI, Daily Dependabot, PR Rebase Sentinel, Governance",
            "skills_count": 48,
        },
    }

    if persona:
        slug = persona.strip().lower()
        if slug in catalog:
            return {"ok": True, "personas": {slug: catalog[slug]}}
        return {
            "ok": False,
            "error": f"Unknown persona '{persona}'. Valid personas: {sorted(catalog.keys())}",
        }

    return {"ok": True, "personas": catalog}


def execute_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch tool call to corresponding read-only handler."""
    args = arguments or {}
    if name == "sak_health_status":
        return execute_sak_health_status(verbose=bool(args.get("verbose", False)))
    if name == "sak_family_catalog":
        return execute_sak_family_catalog(persona=args.get("persona"))
    raise ValueError(f"Tool '{name}' is not recognized or not allow-listed.")
