"""Semantic version tag calculation and release helper for House of Sak."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def parse_semver(tag_str: str) -> tuple[int, int, int]:
    """Parse a semantic version string (with or without 'v' prefix) into (major, minor, patch)."""
    cleaned = tag_str.strip().lstrip("v")
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", cleaned)
    if not match:
        raise ValueError(f"Invalid semver tag: {tag_str!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_semver(major: int, minor: int, patch: int, prefix: str = "v") -> str:
    """Format (major, minor, patch) into a SemVer tag string."""
    return f"{prefix}{major}.{minor}.{patch}"


def get_latest_tag(repo_dir: Path | None = None) -> str | None:
    """Retrieve the latest git tag sorted by version refname."""
    try:
        proc = subprocess.run(
            ["git", "tag", "-l", "--sort=-v:refname"],
            cwd=repo_dir or Path.cwd(),
            capture_output=True,
            text=True,
            check=True,
        )
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        for line in lines:
            try:
                parse_semver(line)
                return line
            except ValueError:
                continue
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_commits_since_tag(tag: str | None = None, repo_dir: Path | None = None) -> list[str]:
    """Retrieve all commit messages since the given tag (or all commits if tag is None)."""
    cmd = ["git", "log", "--format=%B%x00"]
    if tag:
        cmd.append(f"{tag}..HEAD")
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_dir or Path.cwd(),
            capture_output=True,
            text=True,
            check=True,
        )
        raw_msgs = proc.stdout.split("\x00")
        return [m.strip() for m in raw_msgs if m.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def determine_bump_type(commit_messages: list[str]) -> str:
    """Determine SemVer bump type ('major', 'minor', 'patch', or 'none') from commit messages."""
    if not commit_messages:
        return "none"

    has_major = False
    has_minor = False

    for msg in commit_messages:
        lines = msg.splitlines()
        first_line = lines[0].strip() if lines else ""

        # Breaking change check
        if "BREAKING CHANGE:" in msg or "BREAKING-CHANGE:" in msg:
            has_major = True
            break
        if re.search(r"^[a-zA-Z0-9_\-]+(\([^\)]+\))?!:", first_line):
            has_major = True
            break

        # Minor (feature) check
        if re.search(r"^feat(\([^\)]+\))?:", first_line, re.IGNORECASE):
            has_minor = True

    if has_major:
        return "major"
    if has_minor:
        return "minor"
    return "patch"


def calculate_next_tag(current_tag: str | None, bump_type: str, fallback: str = "v2.0.0") -> str:
    """Calculate the next tag string given current tag and bump type."""
    if not current_tag:
        return fallback

    major, minor, patch = parse_semver(current_tag)
    prefix = "v" if current_tag.startswith("v") else ""

    if bump_type == "major":
        return format_semver(major + 1, 0, 0, prefix=prefix)
    if bump_type == "minor":
        return format_semver(major, minor + 1, 0, prefix=prefix)
    if bump_type == "patch":
        return format_semver(major, minor, patch + 1, prefix=prefix)
    return current_tag


def write_github_output(outputs: dict[str, str]) -> None:
    """Write outputs to GITHUB_OUTPUT file if running in GitHub Actions."""
    gh_output_path = os.environ.get("GITHUB_OUTPUT")
    if not gh_output_path:
        return
    with open(gh_output_path, "a", encoding="utf-8") as f:
        for key, val in outputs.items():
            f.write(f"{key}={val}\n")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for semantic tagger."""
    parser = argparse.ArgumentParser(description="Calculate next SemVer git tag.")
    parser.add_argument(
        "--fallback",
        default="v2.0.0",
        help="Fallback tag when no previous tag is present in git (default: v2.0.0).",
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=None,
        help="Target git repository directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print calculated tag without modifying outputs.",
    )
    args = parser.parse_args(argv)

    repo_dir = args.repo_dir or Path.cwd()
    current_tag = get_latest_tag(repo_dir)
    commits = get_commits_since_tag(current_tag, repo_dir)
    bump_type = determine_bump_type(commits)
    next_tag = calculate_next_tag(current_tag, bump_type, fallback=args.fallback)

    print(f"Previous Tag: {current_tag or '(none)'}")
    print(f"Commits since tag: {len(commits)}")
    print(f"Bump Type: {bump_type}")
    print(f"Next Tag: {next_tag}")

    outputs = {
        "previous_tag": current_tag or "",
        "bump_type": bump_type,
        "next_tag": next_tag,
        "has_bump": "true" if (not current_tag or bump_type != "none") else "false",
    }

    if not args.dry_run:
        write_github_output(outputs)

    return 0


if __name__ == "__main__":
    sys.exit(main())
