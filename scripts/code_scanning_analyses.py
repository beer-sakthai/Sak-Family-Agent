#!/usr/bin/env python3
"""Inspect and prune GitHub code-scanning analyses by the tool that produced them.

Why this exists
---------------
A code-scanning alert is only ever closed by a *newer analysis from the same
tool* that no longer reports it. When a scanning workflow is deleted, the
alerts it uploaded lose their producer: nothing will ever re-analyse that ref
under that tool name, so those alerts stay open on the Security tab forever.
No commit, no PR, and no other scanner can clear them — the only supported
remedy is to delete the orphaned analyses (or dismiss the alerts one by one).

That is exactly what happened in this repo. ``.github/workflows/codacy.yml``
uploaded roughly 15k style-level lint findings (Pylint, Prospector,
Remark-lint, ...) before it was removed in ``7224074c`` for being broken and
redundant. See ``docs/code-scanning-sweep-2026-08-12.md``.

Usage
-----
``list`` needs a token with **read** access to code-scanning alerts; ``delete``
needs **write**. The fine-grained repository permission is
"Code scanning alerts"; a classic PAT needs ``security_events`` (or ``repo``
for a private repository).

    export GITHUB_TOKEN=...            # not the Actions-scoped token

    # What is on the dashboard, grouped by the tool that reported it
    python scripts/code_scanning_analyses.py list

    # Everything a given tool ever uploaded, oldest first
    python scripts/code_scanning_analyses.py list --tool Codacy --analyses

    # Dry run: show exactly which analyses would be deleted
    python scripts/code_scanning_analyses.py delete --tool Codacy

    # Actually delete them
    python scripts/code_scanning_analyses.py delete --tool Codacy --apply

Deleting analyses is irreversible and removes the alerts derived from them.
``delete`` is a dry run unless ``--apply`` is passed, and it refuses to touch a
tool whose name it did not find on the dashboard.

Only the standard library is used, so this runs without installing the project.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Any

API_ROOT = "https://api.github.com"
DEFAULT_REPO = "beer-sakthai/Sak-Family-Agent"
PER_PAGE = 100
# GitHub caps code-scanning pagination well below this; the guard only exists so
# a paging bug can't spin forever against the live API.
MAX_PAGES = 200


class ApiError(RuntimeError):
    """An API call failed in a way the caller should see verbatim."""


def _request(
    method: str,
    path: str,
    token: str,
    params: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    """Perform one API call. Returns ``(status, parsed_body_or_None)``."""
    url = f"{API_ROOT}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed https host
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            body = {"message": raw}
        return exc.code, body


def _paginate(path: str, token: str, params: dict[str, Any]) -> list[Any]:
    """Collect every page of a list endpoint."""
    out: list[Any] = []
    for page in range(1, MAX_PAGES + 1):
        status, body = _request("GET", path, token, {**params, "per_page": PER_PAGE, "page": page})
        if status == 403:
            raise ApiError(
                f"403 from {path}: {_message(body)}\n"
                "The token lacks the code-scanning permission. A repository "
                "Actions token cannot read this endpoint — use a PAT with the "
                '"Code scanning alerts" permission (classic: security_events).'
            )
        if status == 404:
            # No analyses/alerts at all, or the feature is off for this repo.
            return out
        if status >= 400:
            raise ApiError(f"{status} from {path}: {_message(body)}")
        if not isinstance(body, list) or not body:
            return out
        out.extend(body)
        if len(body) < PER_PAGE:
            return out
    raise ApiError(f"Refusing to page past {MAX_PAGES} pages of {path}")


def _message(body: Any) -> str:
    if isinstance(body, dict):
        return str(body.get("message", body))
    return str(body)


def _tool_name(entry: dict[str, Any]) -> str:
    """The tool name an analysis or alert was reported under."""
    tool = entry.get("tool") or {}
    return str(tool.get("name") or "(unknown)")


def fetch_open_alerts(repo: str, token: str) -> list[dict[str, Any]]:
    return _paginate(f"/repos/{repo}/code-scanning/alerts", token, {"state": "open"})


def fetch_analyses(repo: str, token: str, tool: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if tool:
        params["tool_name"] = tool
    return _paginate(f"/repos/{repo}/code-scanning/analyses", token, params)


def group_by_tool(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        grouped[_tool_name(entry)].append(entry)
    return dict(grouped)


def _print_table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line)
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))


def cmd_list(args: argparse.Namespace, token: str) -> int:
    alerts = fetch_open_alerts(args.repo, token)
    analyses = fetch_analyses(args.repo, token, args.tool)

    by_tool_alerts = group_by_tool(alerts)
    by_tool_analyses = group_by_tool(analyses)

    print(f"Open code-scanning alerts on {args.repo}: {len(alerts)}")
    print()

    rows: list[tuple[str, ...]] = []
    for tool in sorted(set(by_tool_alerts) | set(by_tool_analyses)):
        tool_analyses = by_tool_analyses.get(tool, [])
        latest = max((a.get("created_at", "") for a in tool_analyses), default="-")
        rows.append(
            (
                tool,
                str(len(by_tool_alerts.get(tool, []))),
                str(len(tool_analyses)),
                latest or "-",
            )
        )
    if rows:
        _print_table(rows, ("tool", "open alerts", "analyses", "latest analysis"))
    else:
        print("Nothing reported.")

    if args.analyses:
        print()
        for tool in sorted(by_tool_analyses):
            print(f"--- {tool} ---")
            for a in sorted(by_tool_analyses[tool], key=lambda x: x.get("created_at", "")):
                print(
                    f"  id={a.get('id')}  {a.get('created_at')}  ref={a.get('ref')}  "
                    f"category={a.get('category')}  results={a.get('results_count')}  "
                    f"deletable={a.get('deletable')}"
                )
    return 0


def cmd_delete(args: argparse.Namespace, token: str) -> int:
    analyses = fetch_analyses(args.repo, token, args.tool)
    if not analyses:
        print(
            f"No analyses found for tool {args.tool!r} on {args.repo}. "
            "Run `list` to see the exact tool names as GitHub spells them.",
            file=sys.stderr,
        )
        return 1

    # Newest first: deleting in this order keeps every remaining analysis a
    # valid "latest" for its ref, which is what the API's own delete chain does.
    ordered = sorted(analyses, key=lambda a: int(a.get("id", 0)), reverse=True)
    total_results = sum(int(a.get("results_count") or 0) for a in ordered)

    print(f"Tool:     {args.tool}")
    print(f"Repo:     {args.repo}")
    print(f"Analyses: {len(ordered)}  (reporting {total_results} results in total)")
    print()
    for a in ordered:
        print(
            f"  id={a.get('id')}  {a.get('created_at')}  ref={a.get('ref')}  "
            f"results={a.get('results_count')}"
        )
    print()

    if not args.apply:
        print("Dry run. Re-run with --apply to delete these analyses.")
        print("Deleting an analysis also removes the alerts derived from it, permanently.")
        return 0

    deleted = 0
    for a in ordered:
        analysis_id = a.get("id")
        status, body = _request(
            "DELETE",
            f"/repos/{args.repo}/code-scanning/analyses/{analysis_id}",
            token,
            {"confirm_delete": "true"},
        )
        if status == 404:
            # Already gone — deleting one analysis can cascade to others.
            print(f"  id={analysis_id}: already deleted")
            continue
        if status >= 400:
            print(f"  id={analysis_id}: {status} {_message(body)}", file=sys.stderr)
            return 1
        deleted += 1
        print(f"  id={analysis_id}: deleted")

    print()
    print(f"Deleted {deleted} analysis/analyses for {args.tool}.")
    print("Re-run `list` to confirm the tool no longer appears.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code_scanning_analyses.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO),
        help=f"owner/name (default: {DEFAULT_REPO}, or $GITHUB_REPOSITORY)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="show open alerts and analyses grouped by tool")
    p_list.add_argument("--tool", help="restrict the analyses column to one tool")
    p_list.add_argument(
        "--analyses",
        action="store_true",
        help="also print every individual analysis",
    )
    p_list.set_defaults(func=cmd_list)

    p_del = sub.add_parser("delete", help="delete every analysis uploaded by one tool")
    p_del.add_argument("--tool", required=True, help="tool name exactly as `list` prints it")
    p_del.add_argument(
        "--apply",
        action="store_true",
        help="perform the deletion (without this the command only reports)",
    )
    p_del.set_defaults(func=cmd_delete)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not token:
        print("Set GITHUB_TOKEN (or GH_TOKEN) first.", file=sys.stderr)
        return 2

    try:
        return int(args.func(args, token))
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
