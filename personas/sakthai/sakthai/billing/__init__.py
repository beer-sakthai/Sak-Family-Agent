"""Billing and Token Metering Subsystem.

Provides multi-tenant API key management, cryptographic verification,
atomic token consumption metering, tiered quota enforcement, and usage billing.
"""

from sakthai.billing.meter import TokenMeter
from sakthai.billing.middleware import verify_api_key_quota
from sakthai.billing.models import (
    APIKeyRecord,
    InvoiceRecord,
    TenantQuota,
    TenantTier,
    UsageEvent,
    generate_api_key,
)

__all__ = [
    "APIKeyRecord",
    "InvoiceRecord",
    "TenantQuota",
    "TenantTier",
    "TokenMeter",
    "UsageEvent",
    "generate_api_key",
    "verify_api_key_quota",
]
