"""Data models and baseline specifications for Google AI Studio Quota Sentinel."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


@dataclass(frozen=True)
class ModelQuotaSpec:
    """Rate limit and daily quota specification for a model endpoint."""

    model_id: str
    category: str
    rpm_limit: int
    tpm_limit: int
    rpd_limit: int
    fallback_model: str | None = None
    description: str = ""


#: Verified November 2026 Free-Tier baseline specifications.
MODEL_QUOTA_SPECS: dict[str, ModelQuotaSpec] = {
    "gemini-4-hydrogen": ModelQuotaSpec(
        model_id="gemini-4-hydrogen",
        category="Frontier Reasoning",
        rpm_limit=5,
        tpm_limit=250_000,
        rpd_limit=20,
        fallback_model="gemini-3.5-flash-lite",
        description="Flagship frontier reasoning (Free-tier capped at ~20 RPD).",
    ),
    "gemini-3.8-flash": ModelQuotaSpec(
        model_id="gemini-3.8-flash",
        category="Balanced Multimodal",
        rpm_limit=10,
        tpm_limit=250_000,
        rpd_limit=1500,
        fallback_model="gemini-3.5-flash-lite",
        description="Balanced multimodal with explicit and implicit context caching.",
    ),
    "gemini-3.6-flash": ModelQuotaSpec(
        model_id="gemini-3.6-flash",
        category="Balanced Multimodal",
        rpm_limit=5,
        tpm_limit=250_000,
        rpd_limit=20,
        fallback_model="gemini-3.5-flash-lite",
        description="Previous-generation balanced multimodal flash.",
    ),
    "gemini-3.5-flash-lite": ModelQuotaSpec(
        model_id="gemini-3.5-flash-lite",
        category="High-Volume / Low-Latency",
        rpm_limit=15,
        tpm_limit=250_000,
        rpd_limit=500,
        fallback_model="gemini-3.1-flash-lite",
        description="High-volume low-latency workhorse (25x daily throughput).",
    ),
    "gemini-3.1-flash-lite": ModelQuotaSpec(
        model_id="gemini-3.1-flash-lite",
        category="High-Volume / Low-Latency",
        rpm_limit=15,
        tpm_limit=250_000,
        rpd_limit=500,
        fallback_model=None,
        description="Lightweight predecessor to 3.5 Flash-Lite.",
    ),
    "gemini-decision-1": ModelQuotaSpec(
        model_id="gemini-decision-1",
        category="Classification / Scoring",
        rpm_limit=200,
        tpm_limit=50_000,
        rpd_limit=10_000,
        fallback_model=None,
        description="Zero-output calibrated decisions & grading (10,000 RPD).",
    ),
    "gemma-4-31b-it": ModelQuotaSpec(
        model_id="gemma-4-31b-it",
        category="Open-Weight Dense",
        rpm_limit=30,
        tpm_limit=16_000,
        rpd_limit=1500,
        fallback_model=None,
        description="Open-weight dense instruction-tuned model.",
    ),
    "gemma-4-26b-a4b-it": ModelQuotaSpec(
        model_id="gemma-4-26b-a4b-it",
        category="Open-Weight MoE",
        rpm_limit=30,
        tpm_limit=16_000,
        rpd_limit=1500,
        fallback_model=None,
        description="Open-weight mixture-of-experts model.",
    ),
    "gemini-embedding-001": ModelQuotaSpec(
        model_id="gemini-embedding-001",
        category="Text Embeddings",
        rpm_limit=100,
        tpm_limit=30_000,
        rpd_limit=1000,
        fallback_model=None,
        description="Vector embeddings for semantic search.",
    ),
    "gemini-2.5-flash": ModelQuotaSpec(
        model_id="gemini-2.5-flash",
        category="Legacy",
        rpm_limit=5,
        tpm_limit=250_000,
        rpd_limit=20,
        fallback_model="gemini-3.5-flash-lite",
        description="Legacy flash model (restricted on new projects).",
    ),
    "gemini-2.5-pro": ModelQuotaSpec(
        model_id="gemini-2.5-pro",
        category="Legacy",
        rpm_limit=0,
        tpm_limit=0,
        rpd_limit=0,
        fallback_model="gemini-4-hydrogen",
        description="Legacy pro model (0 quota on new free projects).",
    ),
}


@dataclass
class QuotaUsageSummary:
    """Usage summary and meter snapshot for a model endpoint."""

    model_id: str
    category: str
    rpd_used: int
    rpd_limit: int
    rpm_used: int
    rpm_limit: int
    tpm_used: int
    tpm_limit: int
    status: str
    rpd_percentage: float = 0.0
    rpm_percentage: float = 0.0
    tpm_percentage: float = 0.0


def get_pacific_now(dt: datetime | None = None) -> datetime:
    """Return the current datetime converted to US/Pacific timezone."""
    if dt is not None:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=PACIFIC_TZ)
        return dt.astimezone(PACIFIC_TZ)
    return datetime.now(PACIFIC_TZ)


def get_pacific_date_str(dt: datetime | None = None) -> str:
    """Return current date formatted as YYYY-MM-DD in US/Pacific time."""
    return get_pacific_now(dt).strftime("%Y-%m-%d")


def seconds_until_pacific_midnight(dt: datetime | None = None) -> float:
    """Compute seconds remaining until the next midnight in US/Pacific time (08:00 UTC)."""
    now = get_pacific_now(dt)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(0.0, (next_midnight - now).total_seconds())


def format_time_remaining(seconds: float) -> str:
    """Format seconds into a compact human-readable duration (e.g., '5h 22m')."""
    total_sec = max(0, int(seconds))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    return f"{hours}h {minutes:02d}m"


def get_model_quota_spec(model: str) -> ModelQuotaSpec:
    """Retrieve quota specification for a model with optional environment overrides."""
    base_name = model.rsplit("/", 1)[-1]
    spec = MODEL_QUOTA_SPECS.get(base_name)
    if spec is None:
        spec = ModelQuotaSpec(
            model_id=base_name,
            category="Custom / Unknown",
            rpm_limit=5,
            tpm_limit=250_000,
            rpd_limit=20,
            fallback_model=None,
            description="Custom or unlisted model baseline.",
        )

    # Check environment variable overrides (e.g. GEMINI_QUOTA_RPD_GEMINI_4_HYDROGEN=50)
    clean_key = base_name.replace("-", "_").replace(".", "_").upper()
    rpd_override = os.environ.get(f"GEMINI_QUOTA_RPD_{clean_key}")
    rpm_override = os.environ.get(f"GEMINI_QUOTA_RPM_{clean_key}")
    tpm_override = os.environ.get(f"GEMINI_QUOTA_TPM_{clean_key}")

    rpd = int(rpd_override) if rpd_override and rpd_override.isdigit() else spec.rpd_limit
    rpm = int(rpm_override) if rpm_override and rpm_override.isdigit() else spec.rpm_limit
    tpm = int(tpm_override) if tpm_override and tpm_override.isdigit() else spec.tpm_limit

    if rpd != spec.rpd_limit or rpm != spec.rpm_limit or tpm != spec.tpm_limit:
        return ModelQuotaSpec(
            model_id=spec.model_id,
            category=spec.category,
            rpm_limit=rpm,
            tpm_limit=tpm,
            rpd_limit=rpd,
            fallback_model=spec.fallback_model,
            description=spec.description,
        )
    return spec
