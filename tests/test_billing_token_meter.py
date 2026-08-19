"""Tests for multi-tenant token metering, API key authentication, and billing engine."""

import pytest

from sakthai.billing.meter import TokenMeter
from sakthai.billing.middleware import verify_api_key_quota
from sakthai.billing.models import (
    TenantTier,
    generate_api_key,
    hash_api_key,
)


@pytest.fixture
def meter() -> TokenMeter:
    """In-memory TokenMeter instance."""
    return TokenMeter(db_path=":memory:")


def test_generate_and_hash_api_key() -> None:
    raw, hashed = generate_api_key(prefix="sak_live_")
    assert raw.startswith("sak_live_")
    assert len(raw) > 20

    # `hash_api_key(raw) == hashed` — what this asserted until the hashing moved
    # from bare SHA-256 to salted PBKDF2 — cannot hold and is not meant to: each
    # call draws a fresh random salt, so hashing the same key twice gives two
    # different strings. That is the point of the salt. Verification is the
    # second parameter, so exercise the real contract in both directions.
    assert hash_api_key(raw, hashed) is True
    assert hash_api_key("sak_live_not-the-key", hashed) is False
    assert hashed.startswith("pbkdf2_sha256$")
    assert hash_api_key(raw) != hashed  # a fresh salt each time


def test_tenant_registration_and_quota(meter: TokenMeter) -> None:
    quota = meter.register_tenant("tenant_abc", tier=TenantTier.PRO)
    assert quota.tenant_id == "tenant_abc"
    assert quota.tier == TenantTier.PRO
    assert quota.monthly_token_quota == 5_000_000
    assert quota.consumed_tokens == 0
    assert quota.remaining_tokens == 5_000_000
    assert quota.active_keys_count == 0


def test_create_and_authenticate_key(meter: TokenMeter) -> None:
    meter.register_tenant("tenant_123", tier=TenantTier.FREE)
    raw_key, record = meter.create_api_key("tenant_123", name="Production Bot Key")

    assert record.tenant_id == "tenant_123"
    assert record.name == "Production Bot Key"
    assert record.is_active is True

    # Authenticate valid key
    auth_record = meter.authenticate_key(raw_key)
    assert auth_record is not None
    assert auth_record.key_id == record.key_id
    assert auth_record.last_used_at is not None

    # Authenticate invalid key
    assert meter.authenticate_key("sak_live_invalidkey123456789") is None


def test_max_keys_enforcement(meter: TokenMeter) -> None:
    meter.register_tenant("tenant_free", tier=TenantTier.FREE)  # Limit is 2 keys
    meter.create_api_key("tenant_free", "Key 1")
    meter.create_api_key("tenant_free", "Key 2")

    with pytest.raises(ValueError, match="reached max keys limit"):
        meter.create_api_key("tenant_free", "Key 3")


def test_revoke_key(meter: TokenMeter) -> None:
    meter.register_tenant("tenant_rev", tier=TenantTier.FREE)
    raw_key, record = meter.create_api_key("tenant_rev", "Temp Key")

    assert meter.authenticate_key(raw_key) is not None
    revoked = meter.revoke_api_key(record.key_id)
    assert revoked is True

    assert meter.authenticate_key(raw_key) is None


def test_record_usage_and_costs(meter: TokenMeter) -> None:
    meter.register_tenant("tenant_usage", tier=TenantTier.PRO)
    raw_key, record = meter.create_api_key("tenant_usage", "Usage Key")

    event = meter.record_usage(
        tenant_id="tenant_usage",
        key_id=record.key_id,
        model="sakthai-context-1.5b-merged",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert event.total_tokens == 1500
    assert event.cost_usd > 0.0

    quota = meter.get_tenant_quota("tenant_usage")
    assert quota.consumed_tokens == 1500
    assert quota.remaining_tokens == 5_000_000 - 1500
    assert quota.total_cost_usd > 0.0

    events = meter.get_usage_events("tenant_usage", limit=10)
    assert len(events) == 1
    assert events[0].event_id == event.event_id


def test_quota_exhaustion_blocks(meter: TokenMeter) -> None:
    meter.register_tenant("tenant_small", tier=TenantTier.FREE)  # 100,000 quota
    raw_key, record = meter.create_api_key("tenant_small", "Small Key")

    # Consume entire quota
    meter.record_usage(
        tenant_id="tenant_small",
        key_id=record.key_id,
        model="sakthai-context-1.5b-merged",
        prompt_tokens=80_000,
        completion_tokens=20_000,
    )

    ok, msg, quota = meter.check_quota("tenant_small", estimated_tokens=10)
    assert ok is False
    assert "Monthly token quota exceeded" in msg
    assert quota.remaining_tokens == 0


def test_rate_limiting_sliding_window(meter: TokenMeter) -> None:
    key_id = "test_rate_key"
    limit_rpm = 5

    # First 5 calls pass
    for _ in range(5):
        assert meter.check_rate_limit(key_id, limit_rpm) is True

    # 6th call exceeds limit
    assert meter.check_rate_limit(key_id, limit_rpm) is False


def test_invoice_generation(meter: TokenMeter) -> None:
    meter.register_tenant("tenant_inv", tier=TenantTier.PRO)
    raw_key, record = meter.create_api_key("tenant_inv", "Inv Key")

    meter.record_usage("tenant_inv", record.key_id, "test-model", 200_000, 100_000)
    invoice = meter.generate_invoice("tenant_inv")

    assert invoice.tenant_id == "tenant_inv"
    assert invoice.total_requests == 1
    assert invoice.total_tokens == 300_000
    assert invoice.amount_due_usd > 0.0


def test_middleware_auth_and_quota_verification(meter: TokenMeter) -> None:
    meter.register_tenant("tenant_mid", tier=TenantTier.FREE)
    raw_key, record = meter.create_api_key("tenant_mid", "Mid Key")

    # Missing creds
    ok, code, msg, rec, q = verify_api_key_quota(meter, auth_header=None)
    assert ok is False
    assert code == 401

    # Invalid Bearer
    ok, code, msg, rec, q = verify_api_key_quota(meter, auth_header="Bearer invalid_key")
    assert ok is False
    assert code == 401

    # Valid Bearer header
    ok, code, msg, rec, q = verify_api_key_quota(meter, auth_header=f"Bearer {raw_key}")
    assert ok is True
    assert code == 200
    assert rec is not None
    assert q is not None

    # Valid X-API-Key
    ok, code, msg, rec, q = verify_api_key_quota(meter, auth_header=None, x_api_key=raw_key)
    assert ok is True
    assert code == 200
