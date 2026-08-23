"""Billing and Quota Authentication Middleware."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sakthai.billing.meter import TokenMeter
    from sakthai.billing.models import APIKeyRecord, TenantQuota


def extract_api_key(auth_header: str | None, x_api_key: str | None = None) -> str | None:
    """Extract raw API key from Authorization header or X-API-Key header."""
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()

    if not auth_header:
        return None

    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() in ("bearer", "apikey"):
        return parts[1]
    if len(parts) == 1 and parts[0].startswith("sak_"):
        return parts[0]

    return None


def verify_api_key_quota(
    meter: TokenMeter,
    auth_header: str | None,
    x_api_key: str | None = None,
    estimated_tokens: int = 1,
) -> tuple[bool, int, str | None, APIKeyRecord | None, TenantQuota | None]:
    """Authenticate API key, check sliding-window rate limit, and verify tenant quota.

    Returns:
        tuple: (is_authorized, status_code, error_message, key_record, quota)
    """
    raw_key = extract_api_key(auth_header, x_api_key)
    if not raw_key:
        return False, 401, "Missing or malformed API key credential", None, None

    key_record = meter.authenticate_key(raw_key)
    if not key_record:
        return False, 401, "Invalid or revoked API key", None, None

    # Check Rate Limit (429)
    if not meter.check_rate_limit(key_record.key_id, key_record.rate_limit_rpm):
        return (
            False,
            429,
            f"Rate limit exceeded ({key_record.rate_limit_rpm} req/min). Please slow down.",
            key_record,
            None,
        )

    # Check Quota (402)
    has_quota, quota_msg, quota = meter.check_quota(
        key_record.tenant_id, estimated_tokens=estimated_tokens
    )
    if not has_quota:
        return False, 402, quota_msg, key_record, quota

    return True, 200, None, key_record, quota
