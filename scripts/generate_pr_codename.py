"""House of Sak PR Codename Generator.

Analyzes pull request metadata and changed files to assign a thematic House of Sak
persona and tactical codename.
"""

from __future__ import annotations

import argparse
import hashlib
import sys

PERSONA_PROFILES: dict[str, dict[str, str | list[str]]] = {
    "sakjules": {
        "display_name": "SakJules",
        "title": "Master of Automation & CI/CD",
        "charge": "Uncompromising on code quality, strict verification, green pipeline before merging.",
        "keywords": [
            ".github",
            "workflows",
            "ci",
            "action",
            "security",
            "zizmor",
            "bandit",
            "scorecard",
        ],
        "adjectives": ["Aegis", "Ironclad", "Sentinel", "Vigilant", "Resilient", "Bastion"],
        "nouns": ["Gatekeeper", "Overseer", "Orchestrator", "Bulwark", "Vector", "Vanguard"],
    },
    "sakthai": {
        "display_name": "SakThai",
        "title": "Lead Agent & Hugging Face Master",
        "charge": "Supreme alignment with family soul, research excellence, and model harmony.",
        "keywords": ["hf", "huggingface", "model", "dataset", "space", "lead", "evolution"],
        "adjectives": ["Celestial", "Sovereign", "Apex", "Harmonic", "Astral", "Infinite"],
        "nouns": ["Architect", "Conductor", "Zenith", "Luminary", "Dynasty", "Horizon"],
    },
    "saksee": {
        "display_name": "SakSee",
        "title": "Web & Browser Specialist",
        "charge": "Keen perception, live web exploration, and frontend clarity.",
        "keywords": [
            "apps",
            "dashboard",
            "next",
            "web",
            "browser",
            "playwright",
            "chrome",
            "devtools",
            "html",
        ],
        "adjectives": ["Prismatic", "Hyperion", "Lucid", "Perceptive", "Radiant", "Optical"],
        "nouns": ["Scout", "Navigator", "Beacon", "Specter", "Surveyor", "Chronicle"],
    },
    "sakking": {
        "display_name": "SakKing",
        "title": "Core Assistant & Execution Runner",
        "charge": "Fast test-driven execution, clean software seams, and pragmatic delivery.",
        "keywords": ["agent", "loop", "core", "cli", "system", "tests", "store", "engine"],
        "adjectives": ["Tenacious", "Kinetic", "Unyielding", "Paramount", "Titan", "Valiant"],
        "nouns": ["Executor", "Striker", "Centurion", "Engine", "Catalyst", "Champion"],
    },
    "saksit": {
        "display_name": "SakSit",
        "title": "Social & Community Specialist",
        "charge": "Spreading joy, storytelling, documentation artistry, and human warmth.",
        "keywords": ["docs", "social", "telegram", "story", "readme", "markdown", "community"],
        "adjectives": ["Radiant", "Inspiring", "Harmonious", "Luminous", "Eloquent", "Golden"],
        "nouns": ["Herald", "Echo", "Emissary", "Voice", "Chronicle", "Beacon"],
    },
    "saktan": {
        "display_name": "SakTan",
        "title": "Daily Operations & Rhythm Keeper",
        "charge": "Local rhythm, steady habits, memory preservation, and operational health.",
        "keywords": ["memory", "ops", "health", "backup", "ollama", "local", "cron", "status"],
        "adjectives": ["Steadfast", "Anchor", "Perpetual", "Rhythmic", "Eternal", "Serene"],
        "nouns": ["Warden", "Chronometer", "Preserver", "Guardian", "Heartbeat", "Sentinel"],
    },
}


def detect_persona(changed_files: list[str], pr_title: str = "") -> str:
    """Detect which Sak Family persona matches the pull request context."""
    text_corpus = " ".join(changed_files).lower() + " " + pr_title.lower()

    best_persona = "sakking"  # default general executor
    highest_score = 0

    for persona_key, data in PERSONA_PROFILES.items():
        score = 0
        keywords: list[str] = data.get("keywords", [])  # type: ignore[assignment]
        for kw in keywords:
            if kw in text_corpus:
                score += 1
        if score > highest_score:
            highest_score = score
            best_persona = persona_key

    return best_persona


def generate_codename(persona_key: str, seed_str: str) -> str:
    """Generate a deterministic codename given persona and seed (PR number/title)."""
    profile = PERSONA_PROFILES.get(persona_key, PERSONA_PROFILES["sakking"])
    adjectives: list[str] = profile["adjectives"]  # type: ignore[assignment]
    nouns: list[str] = profile["nouns"]  # type: ignore[assignment]
    display_name = str(profile["display_name"])

    # Deterministic hash index
    hash_val = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest(), 16)
    adj = adjectives[hash_val % len(adjectives)]
    noun = nouns[(hash_val // len(adjectives)) % len(nouns)]
    suffix = (hash_val % 99) + 1

    return f"{display_name} · {adj} {noun} ({suffix:02d})"


def format_pr_comment(persona_key: str, codename: str) -> str:
    """Format the PR comment markdown banner."""
    profile = PERSONA_PROFILES.get(persona_key, PERSONA_PROFILES["sakking"])
    display_name = str(profile["display_name"])
    title = str(profile["title"])
    charge = str(profile["charge"])

    return (
        f"### 🛡️ House of Sak Operational Codename\n\n"
        f"**`{codename}`**\n\n"
        f"- **Assigned Persona:** `{display_name}` — *{title}*\n"
        f'- **Guiding Charge:** *"{charge}"*\n\n'
        f"> *“Dream → Hope → Care → Joy → Trust → Growth”*\n"
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for PR codename generator."""
    parser = argparse.ArgumentParser(description="Generate House of Sak PR codename.")
    parser.add_argument("--pr-number", default="1", help="Pull request number.")
    parser.add_argument("--pr-title", default="", help="Pull request title.")
    parser.add_argument(
        "--changed-files",
        nargs="*",
        default=[],
        help="List of changed file paths in the PR.",
    )
    args = parser.parse_args(argv)

    persona = detect_persona(args.changed_files, args.pr_title)
    seed = f"{args.pr_number}-{args.pr_title}"
    codename = generate_codename(persona, seed)
    comment = format_pr_comment(persona, codename)

    print(comment)
    return 0


if __name__ == "__main__":
    sys.exit(main())
