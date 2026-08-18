"""Billing data models and cryptographic API key utilities."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import overload


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


_API_KEY_PBKDF2_ITERATIONS = 310_000
_API_KEY_SALT_BYTES = 16


@overload
def hash_api_key(raw_key: str, stored_hash: None = None) -> str: ...


@overload
def hash_api_key(raw_key: str, stored_hash: str) -> bool: ...


def hash_api_key(raw_key: str, stored_hash: str | None = None) -> str | bool:
    """Hash or verify an API key using PBKDF2-HMAC-SHA256.

    - If `stored_hash` is None, returns a new encoded hash for storage.
    - If `stored_hash` is provided, returns True/False for verification.

    The two overloads above carry no runtime effect; they exist so callers get
    the branch's actual type instead of the union. Without them every caller of
    the hashing branch sees `str | bool` — which is what broke `mypy --strict`
    on `main` at `generate_api_key` below, whose contract is `tuple[str, str]`.
    """
    if stored_hash is None:
        salt = secrets.token_bytes(_API_KEY_SALT_BYTES)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            raw_key.encode("utf-8"),
            salt,
            _API_KEY_PBKDF2_ITERATIONS,
        )
        return f"pbkdf2_sha256${_API_KEY_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"

    try:
        algorithm, iterations_s, salt_hex, expected_hex = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", raw_key.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def generate_api_key(prefix: str = "sak_live_") -> tuple[str, str]:
    """Generate a raw API key and its PBKDF2-HMAC-SHA256 storage hash.

    Returns:
        tuple[str, str]: (raw_secret_key, hashed_storage_key)
    """
    token = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{token}"
    hashed_key = hash_api_key(raw_key)
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
