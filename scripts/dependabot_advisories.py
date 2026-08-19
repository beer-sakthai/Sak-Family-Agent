#!/usr/bin/env python3
"""Read the repository's Dependabot alerts and render them as an internal advisory.

Why this exists
---------------
``docs/dependabot-sweep-2026-08-18.md`` reconstructed the alert list by reasoning
about manifests, accounted for 19 of 35 alerts, and ended with:

    Closing that gap properly needs the actual alert list from
    /security/dependabot, which is not readable without a token carrying
    security_events. Do not assume this note is exhaustive.

This script is that read. It is also the data behind
``.github/workflows/innersource-advisories.yml``, which publishes the result
daily as a standing issue so internal consumers of this repository's shared
packages can see what they are exposed to without needing Security-tab access.

The token this needs, and why it is not the Actions token
---------------------------------------------------------
``GITHUB_TOKEN`` **cannot** read Dependabot alerts, and granting a job
``security-events: read`` does not change that: the Actions GitHub App does not
carry the "Dependabot alerts" permission at all, so the endpoint answers
``403 Resource not accessible by integration``.

This is the one place where Dependabot alerts differ from code scanning.
``scripts/code_scanning_analyses.py`` really does run on the stock Actions token
with a per-job ``security-events: write`` — see
``.github/workflows/code-scanning-cleanup.yml``. Do not copy that assumption
here; it produces a job that looks configured and 403s every night.

So this needs a personal access token:

* classic — the ``security_events`` scope (or ``repo`` for a private repository)
* fine-grained — the "Dependabot alerts" repository permission, read

A 403 is therefore reported as a hard, explained failure rather than an empty
list. An empty list means "no open alerts"; it must never mean "could not look".

Usage
-----
::

    export GITHUB_TOKEN=...   # a PAT; an Actions checkout token will not do

    # Open alerts, grouped by severity, with the manifest each came from
    python scripts/dependabot_advisories.py list

    # Everything, including dismissed and fixed
    python scripts/dependabot_advisories.py list --state all

    # The Markdown body the daily workflow posts
    python scripts/dependabot_advisories.py report

    # Non-zero exit if anything at or above a severity is open (for gating)
    python scripts/dependabot_advisories.py list --fail-on high

Only the standard library is used, so this runs without installing the project.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Any

API_ROOT = "https://api.github.com"
DEFAULT_REPO = "beer-sakthai/Sak-Family-Agent"
PER_PAGE = 100
# A guard so a paging bug cannot spin forever against the live API.
MAX_PAGES = 100

# `Link: <url>; rel="next"` — how this endpoint hands over its next cursor.
_LINK_NEXT = re.compile(r'<([^>]+)>\s*;\s*rel="next"')

# Most severe first — this is the display and the ``--fail-on`` ordering.
SEVERITIES = ("critical", "high", "medium", "low")

# Advisories with no upstream fix, recorded in docs/dependabot-sweep-2026-08-18.md.
# They are called out in the report rather than filtered from it: an accepted
# risk that disappears from the report stops being reviewed.
KNOWN_UNFIXABLE = {
    "GHSA-g4r7-86gm-pgqc": (
        "sqlitedict 2.1.0 is the latest release (Dec 2022) and the advisory has no "
        "fixed version. Transitive via lm-eval in the `evals` dependency group, which "
        "only run-evals.yml installs; nothing in `sakthai` imports it."
    ),
    "GHSA-vvw2-h478-xwr3": (
        "dspy — the advisory covers all versions including current. Reachable only from "
        "the agent-self-evolution subproject, and only when pointed at untrusted prompts."
    ),
}

ALERTS_PERMISSION_HELP = (
    "The token cannot read Dependabot alerts.\n"
    "\n"
    "This is expected for a GitHub Actions GITHUB_TOKEN: the Actions app does not\n"
    "carry the 'Dependabot alerts' permission, so `security-events: read` on the job\n"
    "does NOT grant it. (Code scanning is different — that one does work with the\n"
    "Actions token, which is why scripts/code_scanning_analyses.py can use it.)\n"
    "\n"
    "Use a personal access token instead:\n"
    "  classic       -> the `security_events` scope (or `repo` if private)\n"
    "  fine-grained  -> the 'Dependabot alerts' repository permission, read\n"
    "\n"
    "In CI, put it in the DEPENDABOT_ALERTS_TOKEN secret."
)


class ApiError(RuntimeError):
    """An API call failed in a way the caller should see verbatim."""


def _build_url(path: str, params: dict[str, Any] | None = None) -> str:
    url = f"{API_ROOT}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return url


def _request(
    method: str,
    url: str,
    token: str,
) -> tuple[int, Any, dict[str, str]]:
    """Perform one API call against a full URL.

    Returns ``(status, parsed_body_or_None, headers)``. The headers matter:
    this endpoint is cursor-paginated, so the ``Link`` header is the only way
    to reach page two.
    """
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    # bandit B310: urlopen honours file:// and custom schemes. `url` is built
    # from API_ROOT, a hardcoded https:// literal, so the scheme cannot vary
    # today — but assert it rather than trusting that to stay true. Verified not
    # theoretical: with API_ROOT repointed at file:///etc this function read
    # /etc/passwd and failed on the JSON decode rather than on the open. This
    # repo validates schemes rather than assuming them; see giturl.py, which
    # exists because `ext::` in a git remote runs arbitrary commands.
    if not url.startswith("https://"):
        raise ApiError(f"refusing to open a non-https URL: {url!r}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310  # nosec B310
            raw = resp.read().decode("utf-8")
            return (
                resp.status,
                (json.loads(raw) if raw.strip() else None),
                dict(resp.headers),
            )
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            body = {"message": raw}
        return exc.code, body, dict(exc.headers or {})


def _message(body: Any) -> str:
    if isinstance(body, dict):
        return str(body.get("message", body))
    return str(body)


def next_link(headers: dict[str, str]) -> str | None:
    """The ``rel="next"`` URL from a ``Link`` header, if there is one.

    Header names are case-insensitive and `urllib` preserves whatever the
    server sent, so match case-insensitively rather than assuming "Link".
    """
    raw = ""
    for name, value in headers.items():
        if name.lower() == "link":
            raw = value
            break
    if not raw:
        return None
    match = _LINK_NEXT.search(raw)
    return match.group(1) if match else None


def _paginate(path: str, token: str, params: dict[str, Any]) -> list[Any]:
    """Collect every page of the alerts endpoint, following its Link cursors.

    **This endpoint is cursor-paginated, not page-numbered.** Its documented
    parameters are `before`/`after` (cursors taken from the `Link` header) and
    `per_page` — there is no `page`. Passing `page=2` does not advance anything;
    the API just returns the first page again, so a page-numbered loop silently
    yields `MAX_PAGES` copies of the first 100 alerts. That stays invisible
    below 100 alerts (the first short page ends the loop) and corrupts the
    report above it, which is exactly the size at which the report matters.

    A 401/403 raises rather than returning ``[]``. An empty alert list is a
    real, meaningful answer ("nothing open"); a permission failure that renders
    as an empty list is how a security report quietly stops being one.
    """
    out: list[Any] = []
    url: str | None = _build_url(path, {**params, "per_page": PER_PAGE})
    for _ in range(MAX_PAGES):
        assert url is not None
        status, body, headers = _request("GET", url, token)
        if status in (401, 403):
            raise ApiError(f"{status} from {path}: {_message(body)}\n\n{ALERTS_PERMISSION_HELP}")
        if status == 404:
            raise ApiError(
                f"404 from {path}: {_message(body)}\n"
                "Either the repository name is wrong, or Dependabot alerts are not\n"
                "enabled for it. See docs/dependabot-setup.md to turn them on."
            )
        if status >= 400:
            raise ApiError(f"{status} from {path}: {_message(body)}")
        if not isinstance(body, list) or not body:
            return out
        out.extend(body)
        url = next_link(headers)
        if not url:
            return out
    raise ApiError(f"Refusing to follow past {MAX_PAGES} pages of {path}")


def fetch_alerts(repo: str, token: str, state: str = "open") -> list[dict[str, Any]]:
    """Dependabot alerts in one state, or every state when ``state`` is ``all``."""
    params: dict[str, Any] = {} if state == "all" else {"state": state}
    return _paginate(f"/repos/{repo}/dependabot/alerts", token, params)


def _severity(alert: dict[str, Any]) -> str:
    advisory = alert.get("security_advisory") or {}
    return str(advisory.get("severity") or "unknown").lower()


def _ghsa(alert: dict[str, Any]) -> str:
    advisory = alert.get("security_advisory") or {}
    return str(advisory.get("ghsa_id") or "-")


def _package(alert: dict[str, Any]) -> str:
    dependency = alert.get("dependency") or {}
    package = dependency.get("package") or {}
    return str(package.get("name") or "-")


def _ecosystem(alert: dict[str, Any]) -> str:
    dependency = alert.get("dependency") or {}
    package = dependency.get("package") or {}
    return str(package.get("ecosystem") or "-")


def _manifest(alert: dict[str, Any]) -> str:
    dependency = alert.get("dependency") or {}
    return str(dependency.get("manifest_path") or "-")


def _fixed_in(alert: dict[str, Any]) -> str:
    """The first patched version, or an explicit marker when there is none.

    "No fix available" is the single most decision-relevant field in the whole
    report: it is what separates "bump it" from "accept the risk and record why".
    """
    first_patched = (alert.get("security_vulnerability") or {}).get("first_patched_version") or {}
    return str(first_patched.get("identifier") or "none")


def _summary(alert: dict[str, Any]) -> str:
    advisory = alert.get("security_advisory") or {}
    return str(advisory.get("summary") or "").strip()


def group_by_severity(alerts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for alert in alerts:
        grouped[_severity(alert)].append(alert)
    return dict(grouped)


def _severity_order(name: str) -> int:
    return SEVERITIES.index(name) if name in SEVERITIES else len(SEVERITIES)


def _sorted_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(alerts, key=lambda a: (_severity_order(_severity(a)), _manifest(a), _package(a)))


def _counts_line(alerts: list[dict[str, Any]]) -> str:
    grouped = group_by_severity(alerts)
    parts = [f"{len(grouped[s])} {s}" for s in SEVERITIES if grouped.get(s)]
    other = sorted(set(grouped) - set(SEVERITIES))
    parts += [f"{len(grouped[s])} {s}" for s in other]
    return ", ".join(parts) if parts else "none"


def cmd_list(args: argparse.Namespace, token: str) -> int:
    alerts = fetch_alerts(args.repo, token, args.state)
    label = "Open" if args.state == "open" else args.state.capitalize()
    print(f"{label} Dependabot alerts on {args.repo}: {len(alerts)} ({_counts_line(alerts)})")

    if alerts:
        print()
        for severity in sorted(group_by_severity(alerts), key=_severity_order):
            group = group_by_severity(alerts)[severity]
            print(f"--- {severity} ({len(group)}) ---")
            for alert in _sorted_alerts(group):
                fixed = _fixed_in(alert)
                marker = "  [NO FIX]" if fixed == "none" else ""
                print(
                    f"  #{alert.get('number')}  {_package(alert)} ({_ecosystem(alert)})"
                    f"  {_ghsa(alert)}  fixed-in={fixed}{marker}"
                )
                print(f"      {_manifest(alert)}")
                summary = _summary(alert)
                if summary:
                    print(f"      {summary.splitlines()[0][:160]}")

    if args.fail_on:
        threshold = _severity_order(args.fail_on)
        breaching = [a for a in alerts if _severity_order(_severity(a)) <= threshold]
        if breaching:
            print(
                f"\n{len(breaching)} alert(s) at or above {args.fail_on}.",
                file=sys.stderr,
            )
            return 1
    return 0


def render_report(repo: str, alerts: list[dict[str, Any]]) -> str:
    """The Markdown body for the standing advisory issue."""
    lines: list[str] = []
    lines.append("## Dependency advisory report")
    lines.append("")
    lines.append(
        f"**{len(alerts)} open Dependabot alert(s)** on `{repo}` — {_counts_line(alerts)}."
    )
    lines.append("")
    lines.append(
        "This issue is rewritten in place by "
        "[`innersource-advisories.yml`](../blob/main/.github/workflows/innersource-advisories.yml). "
        "It is the whole current list, not a diff — an advisory that disappears from it has been "
        "fixed or dismissed. Ownership and response times are in "
        "[`.github/INNERSOURCE.md`](../blob/main/.github/INNERSOURCE.md)."
    )
    lines.append("")

    if not alerts:
        lines.append("No open alerts. Nothing to action.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Sev | Package | Ecosystem | Advisory | Fixed in | Manifest |")
    lines.append("|---|---|---|---|---|---|")
    for alert in _sorted_alerts(alerts):
        fixed = _fixed_in(alert)
        fixed_cell = "**none**" if fixed == "none" else f"`{fixed}`"
        lines.append(
            f"| {_severity(alert)} | `{_package(alert)}` | {_ecosystem(alert)} "
            f"| {_ghsa(alert)} | {fixed_cell} | `{_manifest(alert)}` |"
        )
    lines.append("")

    unfixable = [a for a in alerts if _fixed_in(a) == "none"]
    if unfixable:
        lines.append("### No upstream fix — a dismissal decision, not a bump")
        lines.append("")
        for alert in _sorted_alerts(unfixable):
            note = KNOWN_UNFIXABLE.get(_ghsa(alert))
            lines.append(f"- **`{_package(alert)}`** ({_ghsa(alert)}, {_severity(alert)})")
            lines.append(f"  - {note}" if note else "  - Not yet triaged. Assess reachability.")
        lines.append("")

    lines.append("### Coverage caveat")
    lines.append("")
    lines.append(
        "Alerts come from the dependency graph, which scans the whole repository. "
        "Version-update pull requests only reach directories listed in "
        "[`.github/dependabot.yml`](../blob/main/.github/dependabot.yml). A manifest in this "
        "table but not in that config will keep alerting and will never self-heal — "
        "`tests/test_dependabot_config.py` lists the deliberate exceptions in "
        "`UNCOVERED_BY_DESIGN`."
    )
    lines.append("")
    return "\n".join(lines)


def cmd_report(args: argparse.Namespace, token: str) -> int:
    alerts = fetch_alerts(args.repo, token, "open")
    body = render_report(args.repo, alerts)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(body)
        print(f"wrote {args.output} ({len(alerts)} open alerts)", file=sys.stderr)
    else:
        print(body)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dependabot_advisories.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO),
        help=f"owner/name (default: {DEFAULT_REPO}, or $GITHUB_REPOSITORY)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="print open alerts grouped by severity")
    p_list.add_argument(
        "--state",
        choices=("open", "dismissed", "fixed", "auto_dismissed", "all"),
        default="open",
        help="which alert state to list (default: open)",
    )
    p_list.add_argument(
        "--fail-on",
        choices=SEVERITIES,
        help="exit non-zero if any alert is at or above this severity",
    )
    p_list.set_defaults(func=cmd_list)

    p_report = sub.add_parser("report", help="render the Markdown advisory body")
    p_report.add_argument("--output", help="write to this file instead of stdout")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not token:
        print(f"Set GITHUB_TOKEN (or GH_TOKEN) first.\n\n{ALERTS_PERMISSION_HELP}", file=sys.stderr)
        return 2

    try:
        return int(args.func(args, token))
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
