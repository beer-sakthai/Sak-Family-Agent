"""The feature lifecycle and deprecation registry.

Nothing in the repository had deprecation machinery before this: no
`DeprecationWarning`, no sunset dates, no published list. The model here is the
specification's own (SEP-2596) — Active / Deprecated / Removed, a twelve-month
minimum notice, and a registry that is published rather than left in release
notes.
"""

from __future__ import annotations

import datetime as dt

import pytest

from sakthai.mcp.lifecycle import (
    FEATURE_STATES,
    MIN_DEPRECATION_DAYS,
    Feature,
    FeatureState,
    _reset_warned_for_tests,
    deprecated_features,
    get_feature,
    warn_deprecated,
)


@pytest.fixture(autouse=True)
def _fresh_warnings() -> None:
    """`warn_deprecated` warns once per process; reset between tests."""
    _reset_warned_for_tests()


# --- registry invariants -----------------------------------------------------


def test_feature_ids_are_unique() -> None:
    ids = [f.id for f in FEATURE_STATES]
    assert len(set(ids)) == len(ids)


def test_registry_is_not_empty() -> None:
    assert FEATURE_STATES


def test_every_feature_has_a_summary_and_rationale() -> None:
    """An entry nobody can act on is worse than no entry."""
    for feature in FEATURE_STATES:
        assert feature.summary.strip(), feature.id
        assert feature.rationale.strip(), feature.id


def test_deprecated_features_carry_both_dates() -> None:
    for feature in FEATURE_STATES:
        if feature.state is FeatureState.DEPRECATED:
            assert feature.deprecated_since, feature.id
            assert feature.removal_not_before, feature.id


def test_deprecated_features_give_the_minimum_notice() -> None:
    """The twelve-month window is the whole point of writing the dates down."""
    for feature in FEATURE_STATES:
        if feature.state is FeatureState.DEPRECATED:
            assert feature.notice_days is not None
            assert feature.notice_days >= MIN_DEPRECATION_DAYS, (
                f"{feature.id} gives {feature.notice_days} days of notice; "
                f"the policy minimum is {MIN_DEPRECATION_DAYS}"
            )


def test_dates_are_iso_formatted() -> None:
    for feature in FEATURE_STATES:
        for value in (feature.deprecated_since, feature.removal_not_before):
            if value:
                dt.date.fromisoformat(value)  # raises if malformed


def test_deprecated_features_name_a_replacement() -> None:
    for feature in FEATURE_STATES:
        if feature.state is FeatureState.DEPRECATED:
            assert feature.replacement.strip(), feature.id


def test_the_sse_transport_alias_is_registered() -> None:
    """The first customer of this machinery."""
    feature = get_feature('transport: "sse"')
    assert feature is not None
    assert feature.state is FeatureState.DEPRECATED
    assert "streamable-http" in feature.replacement


def test_deprecated_features_excludes_active_ones() -> None:
    assert all(f.state is not FeatureState.ACTIVE for f in deprecated_features())
    assert len(deprecated_features()) < len(FEATURE_STATES)


# --- notice_days -------------------------------------------------------------


def test_notice_days_is_none_without_both_dates() -> None:
    assert Feature("x", FeatureState.DEPRECATED, "s").notice_days is None
    assert (
        Feature("x", FeatureState.DEPRECATED, "s", deprecated_since="2026-01-01").notice_days
        is None
    )


def test_notice_days_counts_the_gap() -> None:
    feature = Feature(
        "x",
        FeatureState.DEPRECATED,
        "s",
        deprecated_since="2026-01-01",
        removal_not_before="2027-01-01",
    )
    assert feature.notice_days == 365


# --- warn_deprecated ---------------------------------------------------------


def test_warning_names_the_replacement_and_the_date() -> None:
    with pytest.warns(DeprecationWarning) as record:
        warn_deprecated('transport: "sse"')
    message = str(record[0].message)
    assert "streamable-http" in message
    assert "2027-11-23" in message


def test_warning_includes_the_context_when_given() -> None:
    with pytest.warns(DeprecationWarning, match="my-server"):
        warn_deprecated('transport: "sse"', context="MCP server 'my-server'")


def test_warning_fires_once_per_process() -> None:
    """Otherwise a manifest with six remote servers warns six times."""
    with pytest.warns(DeprecationWarning):
        warn_deprecated('transport: "sse"')
    import warnings as _w

    with _w.catch_warnings(record=True) as caught:
        _w.simplefilter("always")
        warn_deprecated('transport: "sse"')
    assert caught == []


def test_warning_also_logs(caplog: pytest.LogCaptureFixture) -> None:
    """A CLI run has warnings suppressed; the log is what the operator sees."""
    with caplog.at_level("WARNING"), pytest.warns(DeprecationWarning):
        warn_deprecated('transport: "sse"')
    assert "deprecated" in caplog.text


def test_an_active_feature_does_not_warn() -> None:
    import warnings as _w

    with _w.catch_warnings(record=True) as caught:
        _w.simplefilter("always")
        warn_deprecated("protocol: 2024-11-05")
    assert caught == []


def test_an_unknown_feature_id_raises() -> None:
    """A typo would otherwise silently never warn."""
    with pytest.raises(KeyError, match="no such feature"):
        warn_deprecated("transport: nonsense")


def test_get_feature_returns_none_for_unknown_ids() -> None:
    assert get_feature("nope") is None
