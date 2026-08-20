"""Tests for the billing paths the main suite leaves unexercised.

Two groups, with different reasons for existing.

**The API-key hashing error branches.** `hash_api_key`'s verification half was
introduced by a CodeQL autofix ("Use of a broken or weak cryptographic hashing
algorithm on sensitive data") that replaced a bare SHA-256 digest with salted
PBKDF2. The rewrite added a parser for the stored `pbkdf2_sha256$…` encoding and
two ways to reject a value — a wrong algorithm tag, and a string it cannot parse
at all — and shipped without a test touching either. A verifier that returns
`False` for the *wrong* reason is indistinguishable from one that works, so each
rejection path is pinned separately here rather than through one "bad input"
case.

**`to_dict()` and the on-disk `TokenMeter`.** These are ordinary gaps rather
than anything introduced: the four `to_dict()` methods are the serialisation
boundary for anything reading billing state out of the store, and every existing
test constructs `TokenMeter(":memory:")`, so the file-backed constructor branch —
the one production actually uses — had never been executed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.billing.meter import TokenMeter
from sakthai.billing.middleware import extract_api_key, verify_api_key_quota
from sakthai.billing.models import (
    TenantTier,
    generate_api_key,
    hash_api_key,
)

# --------------------------------------------------------------------------
# hash_api_key: the verification branches the autofix added
# --------------------------------------------------------------------------


def test_verify_rejects_unknown_algorithm_tag() -> None:
    """A well-formed encoding naming a different algorithm must be refused.

    This is the branch that stops an attacker-supplied or legacy stored value
    from being verified under rules the current scheme does not implement — a
    stored `sha256$…` row must not validate just because it parses.
    """
    raw, _ = generate_api_key()
    forged = "sha256$310000$" + "ab" * 16 + "$" + "cd" * 32
    assert hash_api_key(raw, forged) is False


def test_verify_rejects_unparseable_stored_hash() -> None:
    """Malformed stored values return False rather than raising.

    `authenticate_key` verifies every active row in turn, so one corrupt row
    must not take down authentication for every other key in the table.
    """
    raw, _ = generate_api_key()
    for broken in (
        "",  # empty
        "not-a-hash",  # no separators at all
        "pbkdf2_sha256$310000",  # too few fields to unpack
        "pbkdf2_sha256$not-an-int$aabb$ccdd",  # iterations not an integer
        "pbkdf2_sha256$310000$zzzz$ccdd",  # salt not hex
        "pbkdf2_sha256$310000$aabb$zzzz",  # digest not hex
    ):
        assert hash_api_key(raw, broken) is False, broken


def test_verify_rejects_right_shape_wrong_key() -> None:
    """The digest comparison itself must reject, not just the parser."""
    raw, stored = generate_api_key()
    other_raw, _ = generate_api_key()
    assert hash_api_key(raw, stored) is True
    assert hash_api_key(other_raw, stored) is False


def test_stored_hash_encodes_its_own_parameters() -> None:
    """The stored value carries algorithm, iterations and salt, in that order.

    Verification re-derives the digest from these fields rather than from module
    constants, which is what lets the iteration count be raised later without
    invalidating every key already issued.
    """
    _, stored = generate_api_key()
    algorithm, iterations, salt_hex, digest_hex = stored.split("$", 3)
    assert algorithm == "pbkdf2_sha256"
    assert int(iterations) >= 310_000
    assert len(bytes.fromhex(salt_hex)) == 16
    assert len(bytes.fromhex(digest_hex)) == 32


# --------------------------------------------------------------------------
# verify_api_key_quota: the rejection paths between 401 and 200
# --------------------------------------------------------------------------


def test_verify_rejects_over_rate_limit_before_checking_quota() -> None:
    """A key over its per-minute limit gets 429, not 402 or 200.

    Order matters here: rate limiting is cheaper than the quota lookup and is
    the response a caller should back off on, so it has to be reached first.
    """
    meter = TokenMeter(db_path=":memory:")
    meter.register_tenant("tenant_rl", tier=TenantTier.FREE)
    raw_key, record = meter.create_api_key("tenant_rl", "rate limited")

    for _ in range(record.rate_limit_rpm):
        assert meter.check_rate_limit(record.key_id, record.rate_limit_rpm) is True

    allowed, status, message, returned, quota = verify_api_key_quota(
        meter, auth_header=f"Bearer {raw_key}"
    )
    assert allowed is False
    assert status == 429
    assert message is not None and "Rate limit exceeded" in message
    assert returned is not None and returned.key_id == record.key_id
    assert quota is None


def test_verify_returns_402_when_the_quota_is_spent() -> None:
    """An authenticated, in-rate key with no tokens left is payment-required."""
    meter = TokenMeter(db_path=":memory:")
    quota = meter.register_tenant("tenant_spent", tier=TenantTier.FREE)
    raw_key, record = meter.create_api_key("tenant_spent", "spent")
    meter.record_usage(
        "tenant_spent",
        record.key_id,
        model="gemini-3.1-flash",
        prompt_tokens=quota.monthly_token_quota,
        completion_tokens=0,
    )

    allowed, status, message, returned, remaining = verify_api_key_quota(
        meter, auth_header=f"Bearer {raw_key}", estimated_tokens=1_000
    )
    assert allowed is False
    assert status == 402
    assert returned is not None
    assert remaining is not None and remaining.remaining_tokens <= 0


# --------------------------------------------------------------------------
# extract_api_key: header parsing
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("auth_header", "x_api_key", "expected"),
    [
        (None, "sak_live_abc", "sak_live_abc"),  # X-API-Key wins
        ("Bearer sak_live_xyz", None, "sak_live_xyz"),
        ("bearer sak_live_xyz", None, "sak_live_xyz"),  # scheme is case-insensitive
        ("ApiKey sak_live_xyz", None, "sak_live_xyz"),
        ("sak_live_bare", None, "sak_live_bare"),  # bare key, no scheme
        (None, None, None),
        (None, "   ", None),  # whitespace-only is not a key
        ("Basic dXNlcjpwYXNz", None, None),  # unsupported scheme
        ("Bearer", None, None),  # scheme with no value
        ("Bearer a b c", None, None),  # too many parts
        ("not-a-sak-key", None, None),  # bare value without the prefix
    ],
)
def test_extract_api_key_header_forms(
    auth_header: str | None, x_api_key: str | None, expected: str | None
) -> None:
    assert extract_api_key(auth_header, x_api_key) == expected


# --------------------------------------------------------------------------
# TokenMeter: the file-backed constructor and listing
# --------------------------------------------------------------------------


def test_file_backed_meter_creates_its_parent_directory(tmp_path: Path) -> None:
    """The production path: a real file, whose parent may not exist yet."""
    db_path = tmp_path / "nested" / "dir" / "billing.sqlite3"
    meter = TokenMeter(db_path=db_path)

    assert db_path.parent.is_dir()
    meter.register_tenant("tenant_file", tier=TenantTier.PRO)
    assert meter.get_tenant_quota("tenant_file").tier == TenantTier.PRO


def test_db_path_falls_back_to_the_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`SAKTHAI_BILLING_DB` selects the store when no path is passed."""
    target = tmp_path / "from-env" / "billing.sqlite3"
    monkeypatch.setenv("SAKTHAI_BILLING_DB", str(target))
    assert TokenMeter().db_path == target


def test_db_path_defaults_under_the_home_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """With neither argument nor env var, the store sits under ~/.sakthai."""
    monkeypatch.delenv("SAKTHAI_BILLING_DB", raising=False)
    assert TokenMeter().db_path == Path.home() / ".sakthai" / "billing.sqlite3"


def test_list_api_keys_is_scoped_to_one_tenant() -> None:
    """Listing must not leak another tenant's keys — it is a tenancy boundary."""
    meter = TokenMeter(db_path=":memory:")
    meter.register_tenant("tenant_a", tier=TenantTier.PRO)
    meter.register_tenant("tenant_b", tier=TenantTier.PRO)
    meter.create_api_key("tenant_a", name="first")
    meter.create_api_key("tenant_a", name="second")
    meter.create_api_key("tenant_b", name="other")

    names = {record.name for record in meter.list_api_keys("tenant_a")}
    assert names == {"first", "second"}
    assert [r.name for r in meter.list_api_keys("tenant_b")] == ["other"]
    assert meter.list_api_keys("tenant_absent") == []


def test_authenticate_scans_past_a_non_matching_key() -> None:
    """Salted hashes force a scan-and-verify lookup, not an indexed match.

    With a random salt per key the stored digest cannot be recomputed from the
    raw key alone, so `authenticate_key` walks the active rows and verifies each.
    Two keys are issued here so the loop must reject one before accepting the
    other — with a single key the walk would succeed on its first iteration and
    never exercise the rejection.
    """
    meter = TokenMeter(db_path=":memory:")
    meter.register_tenant("tenant_scan", tier=TenantTier.PRO)
    meter.create_api_key("tenant_scan", name="decoy")
    raw_wanted, _ = meter.create_api_key("tenant_scan", name="wanted")

    record = meter.authenticate_key(raw_wanted)
    assert record is not None
    assert record.name == "wanted"
    assert meter.authenticate_key("sak_live_never-issued") is None


def test_quota_reset_date_rolls_into_january_from_december(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The December branch of the next-reset calculation increments the year.

    Reached only in December, so it would otherwise be exercised by CI for one
    month a year.
    """
    import sakthai.billing.meter as meter_mod

    real_datetime = meter_mod.datetime

    class _December(real_datetime):  # type: ignore[misc, valid-type]
        @classmethod
        def now(cls, tz: object = None) -> real_datetime:  # type: ignore[override]
            return real_datetime(2026, 12, 15, tzinfo=tz)  # type: ignore[arg-type]

    monkeypatch.setattr(meter_mod, "datetime", _December)

    meter = TokenMeter(db_path=":memory:")
    meter.register_tenant("tenant_dec", tier=TenantTier.PRO)
    assert meter.get_tenant_quota("tenant_dec").reset_date.startswith("2027-01-01")


def test_pay_as_you_go_is_never_quota_blocked() -> None:
    """That tier bills what it uses, so a quota check must always pass it."""
    meter = TokenMeter(db_path=":memory:")
    meter.register_tenant("tenant_payg", tier=TenantTier.PAY_AS_YOU_GO)

    allowed, message, quota = meter.check_quota("tenant_payg", estimated_tokens=10**12)
    assert allowed is True
    assert message == "OK"
    assert quota.tier == TenantTier.PAY_AS_YOU_GO


# --------------------------------------------------------------------------
# to_dict(): the serialisation boundary
# --------------------------------------------------------------------------


def test_every_record_serialises_to_primitives() -> None:
    """`to_dict()` is what crosses the API boundary, so it must not leak enums.

    A `TenantTier` member would serialise as `"TenantTier.PRO"` through some
    encoders and `"pro"` through others; the records convert it explicitly, and
    that is what this pins. The secret is checked separately: `hashed_key` is
    deliberately absent from `APIKeyRecord.to_dict()`.
    """
    meter = TokenMeter(db_path=":memory:")
    meter.register_tenant("tenant_ser", tier=TenantTier.PRO)
    _, key_record = meter.create_api_key("tenant_ser", name="serialisable")
    meter.record_usage(
        "tenant_ser",
        key_record.key_id,
        model="gemini-3.1-flash",
        prompt_tokens=10,
        completion_tokens=5,
    )

    key_dict = meter.list_api_keys("tenant_ser")[0].to_dict()
    assert key_dict["name"] == "serialisable"
    assert key_dict["tier"] == "pro"
    assert "hashed_key" not in key_dict, "to_dict() must not expose the stored hash"

    event_dict = meter.get_usage_events("tenant_ser")[0].to_dict()
    assert event_dict["tenant_id"] == "tenant_ser"

    quota_dict = meter.get_tenant_quota("tenant_ser").to_dict()
    assert quota_dict["tier"] == "pro"

    invoice_dict = meter.generate_invoice("tenant_ser").to_dict()
    assert invoice_dict["tenant_id"] == "tenant_ser"

    for name, payload in (
        ("key", key_dict),
        ("event", event_dict),
        ("quota", quota_dict),
        ("invoice", invoice_dict),
    ):
        for field, value in payload.items():
            assert isinstance(value, (str, int, float, bool, type(None))), (
                f"{name}.{field} serialises to {type(value).__name__}, not a primitive"
            )
