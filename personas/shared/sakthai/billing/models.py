"""Billing data models and cryptographic API key utilities."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class TenantTier(StrEnum):
    """Subscription tiers for multi-tenant metering."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    PAY_AS_YOU_GO = "pay_as_you_go"


# Tier quotas: (monthly_token_quota, max_requests_per_minute, max_keys)
TIER_LIMITS: dict[TenantTier, tuple[int, int, int]] = {
    TenantTier.FREE: (100_000, 60, 2),
    TenantTier.PRO: (5_000_000, 300, 10),
    TenantTier.ENTERPRISE: (100_000_000, 1_200, 50),
    TenantTier.PAY_AS_YOU_GO: (1_000_000_000, 600, 20),
}

# Pricing per million tokens (USD)
TIER_PRICING: dict[TenantTier, tuple[float, float]] = {
    # (prompt_cost_per_m, completion_cost_per_m)
    TenantTier.FREE: (0.0, 0.0),
    TenantTier.PRO: (0.15, 0.60),
    TenantTier.ENTERPRISE: (0.10, 0.40),
    TenantTier.PAY_AS_YOU_GO: (0.20, 0.80),
}


API_KEY_HASH_SECRET_ENV = "SAKTHAI_API_KEY_HASH_SECRET"


def _get_api_key_hash_secret() -> bytes:
    """Load and validate API key hashing secret used for deterministic keyed hashing."""
    secret = os.getenv(API_KEY_HASH_SECRET_ENV)
    if not secret:
        raise RuntimeError(f"Missing required environment variable: {API_KEY_HASH_SECRET_ENV}")
    return secret.encode("utf-8")


def hash_api_key(raw_key: str, stored_hash: str | None = None) -> str | bool:
    """Create a PBKDF2 hash or verify a raw key against a stored hash.

    With no ``stored_hash``, returns ``pbkdf2_sha256$iterations$salt$digest``.
    With a stored value, returns a boolean and rejects malformed or unsupported
    encodings without raising.
    """
    if stored_hash is None:
        iterations = 310_000
        secret = _get_api_key_hash_secret()
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", raw_key.encode("utf-8"), secret + salt, iterations)
        return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"

    try:
        algorithm, iteration_text, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iteration_text)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        if iterations <= 0 or len(salt) != 16 or len(expected) != 32:
            return False
    except (TypeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256", raw_key.encode("utf-8"), _get_api_key_hash_secret() + salt, iterations
    )
    return hmac.compare_digest(actual, expected)


def generate_api_key(prefix: str = "sak_live_") -> tuple[str, str]:
    """Generate a raw API key and its PBKDF2 storage encoding."""
    token = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{token}"
    hashed_key = hash_api_key(raw_key)
    assert isinstance(hashed_key, str)
    return raw_key, hashed_key


@dataclass
class APIKeyRecord:
    """Represents a stored API key identity."""

    key_id: str
    tenant_id: str
    hashed_key: str
    name: str
    prefix: str
    tier: TenantTier = TenantTier.FREE
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_used_at: str | None = None
    rate_limit_rpm: int = 60

    def to_dict(self) -> dict[str, object]:
        return {
            "key_id": self.key_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "prefix": self.prefix,
            "tier": self.tier.value,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "rate_limit_rpm": self.rate_limit_rpm,
        }


@dataclass
class UsageEvent:
    """Represents a recorded token consumption event."""

    event_id: str
    tenant_id: str
    key_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "key_id": self.key_id,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "timestamp": self.timestamp,
        }


@dataclass
class TenantQuota:
    """Represents real-time quota allocation and consumption for a tenant."""

    tenant_id: str
    tier: TenantTier
    monthly_token_quota: int
    consumed_tokens: int
    remaining_tokens: int
    total_cost_usd: float
    active_keys_count: int
    reset_date: str

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant_id": self.tenant_id,
            "tier": self.tier.value,
            "monthly_token_quota": self.monthly_token_quota,
            "consumed_tokens": self.consumed_tokens,
            "remaining_tokens": self.remaining_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "active_keys_count": self.active_keys_count,
            "reset_date": self.reset_date,
        }


@dataclass
class InvoiceRecord:
    """Represents a monthly billing summary invoice."""

    invoice_id: str
    tenant_id: str
    period_start: str
    period_end: str
    total_requests: int
    total_tokens: int
    amount_due_usd: float
    status: str = "paid"  # "paid", "due", "waived"

    def to_dict(self) -> dict[str, object]:
        return {
            "invoice_id": self.invoice_id,
            "tenant_id": self.tenant_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "amount_due_usd": round(self.amount_due_usd, 2),
            "status": self.status,
        }
