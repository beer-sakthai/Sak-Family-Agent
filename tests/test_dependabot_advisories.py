"""Pagination contract for ``scripts/dependabot_advisories.py``.

The Dependabot alerts endpoint is **cursor-paginated, not page-numbered**. Its
documented parameters are ``before``/``after`` — cursors taken from the ``Link``
header — and ``per_page``. There is no ``page``.

The first version of this script looped ``page=1..N`` like
``scripts/code_scanning_analyses.py`` does for code scanning. That failure is
invisible at this repository's current size and silent at the size where it
matters: below 100 alerts the first short page ends the loop and everything
looks fine, while above 100 the API returns the same first page for every
request, so the "report" becomes ``MAX_PAGES`` copies of the first 100 alerts.

These tests inject a fake transport, so they touch no network and need no token.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script() -> ModuleType:
    path = REPO_ROOT / "scripts" / "dependabot_advisories.py"
    spec = importlib.util.spec_from_file_location("dependabot_advisories", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


advisories = _load_script()


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({}, None),
        ({"Link": '<https://api.github.com/b>; rel="prev"'}, None),
        ({"Link": '<https://api.github.com/b>; rel="next"'}, "https://api.github.com/b"),
        # Header names are case-insensitive; urllib passes through whatever the
        # server sent, so this must not depend on the exact spelling.
        ({"link": '<https://api.github.com/c>; rel="next"'}, "https://api.github.com/c"),
        # Real responses carry several relations in one header.
        (
            {"Link": '<https://a/1>; rel="next", <https://a/9>; rel="last"'},
            "https://a/1",
        ),
    ],
)
def test_next_link_reads_the_cursor(headers: dict[str, str], expected: str | None) -> None:
    assert advisories.next_link(headers) == expected


def test_paginate_follows_link_cursors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two full pages plus a short one, reached only via the Link header."""
    requested: list[str] = []
    pages = [
        (
            200,
            [{"number": i} for i in range(100)],
            {"Link": '<https://api.github.com/p2>; rel="next"'},
        ),
        (
            200,
            [{"number": i} for i in range(100, 200)],
            {"Link": '<https://api.github.com/p3>; rel="next"'},
        ),
        (200, [{"number": 200}], {}),
    ]

    def fake_request(method: str, url: str, token: str):
        requested.append(url)
        return pages[len(requested) - 1]

    monkeypatch.setattr(advisories, "_request", fake_request)
    alerts = advisories._paginate("/repos/o/r/dependabot/alerts", "tok", {})

    assert len(alerts) == 201, "every page's alerts must be collected"
    assert requested[1] == "https://api.github.com/p2"
    assert requested[2] == "https://api.github.com/p3", (
        "page three must come from the second response's Link header, not a page counter"
    )


def test_paginate_stops_when_no_next_link(monkeypatch: pytest.MonkeyPatch) -> None:
    """A full page with no Link is the last page — do not keep asking.

    This is the case a page-numbered loop gets wrong: `len(body) == per_page`
    looks like "there is more" even when the cursor says otherwise.
    """
    calls = 0

    def fake_request(method: str, url: str, token: str):
        nonlocal calls
        calls += 1
        return 200, [{"number": i} for i in range(advisories.PER_PAGE)], {}

    monkeypatch.setattr(advisories, "_request", fake_request)
    alerts = advisories._paginate("/repos/o/r/dependabot/alerts", "tok", {})

    assert calls == 1, "a page with no rel=next must end the loop"
    assert len(alerts) == advisories.PER_PAGE


def test_forbidden_raises_with_the_remedy_rather_than_returning_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A 403 must never render as "no open alerts"."""
    monkeypatch.setattr(
        advisories,
        "_request",
        lambda *a, **k: (403, {"message": "Resource not accessible by integration"}, {}),
    )
    with pytest.raises(advisories.ApiError) as excinfo:
        advisories._paginate("/repos/o/r/dependabot/alerts", "tok", {})

    message = str(excinfo.value)
    assert "security_events" in message, "the error must name the scope that fixes it"
    assert "Dependabot alerts" in message


def test_non_https_url_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """bandit B310: urlopen honours file:// and custom schemes.

    Not theoretical — before the guard, repointing API_ROOT at ``file:///etc``
    made this function read ``/etc/passwd`` and fail on the JSON decode rather
    than on the open.
    """
    monkeypatch.setattr(advisories, "API_ROOT", "file:///etc")
    with pytest.raises(advisories.ApiError, match="non-https"):
        advisories._request("GET", advisories._build_url("/passwd"), "tok")
