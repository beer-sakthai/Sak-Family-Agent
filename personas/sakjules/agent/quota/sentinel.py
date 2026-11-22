"""Adaptive Free-Tier Quota Sentinel with sliding-window backoff and model cascading."""

from __future__ import annotations

import logging
import os
import threading
import time

from .models import (
    QuotaUsageSummary,
    get_model_quota_spec,
    get_pacific_date_str,
)
from .store import QuotaSentinelStore

logger = logging.getLogger("sakthai.agent.quota")

_sentinel_instance: QuotaSentinel | None = None
_sentinel_lock = threading.Lock()


class QuotaSentinel:
    """Free-Tier Quota Sentinel interceptor for Google AI Studio models."""

    def __init__(self, store: QuotaSentinelStore | None = None) -> None:
        self.store = store or QuotaSentinelStore()

    @staticmethod
    def is_enabled() -> bool:
        """Return True if Quota Sentinel is enabled."""
        val = os.environ.get("SAKTHAI_QUOTA_SENTINEL", "1").strip().lower()
        return val not in ("0", "false", "no", "off")

    def preflight(
        self,
        model: str,
        estimated_tokens: int = 0,
        now: float | None = None,
    ) -> tuple[str, float]:
        """Check rate limits and daily quota before dispatching an API call.

        Returns:
            A tuple of ``(effective_model, wait_seconds)`` where ``effective_model``
            may be cascaded to a higher-volume endpoint if the primary model's RPD
            is exhausted, and ``wait_seconds`` is the smart backoff duration to avoid
            sub-minute RPM/TPM HTTP 429 errors.
        """
        if not self.is_enabled():
            return model, 0.0

        current_time = time.time() if now is None else now
        target_model = model.rsplit("/", 1)[-1]
        visited: set[str] = set()

        # 1. Daily RPD quota check & model cascading
        while target_model not in visited:
            visited.add(target_model)
            spec = get_model_quota_spec(target_model)
            daily = self.store.get_daily_usage(target_model)
            rpd_used = daily.get(target_model, {}).get("request_count", 0)

            if spec.rpd_limit > 0 and rpd_used >= spec.rpd_limit:
                if spec.fallback_model and spec.fallback_model not in visited:
                    logger.warning(
                        "[QUOTA SENTINEL] Daily RPD limit for '%s' reached (%d/%d). "
                        "Cascading to fallback model '%s'.",
                        target_model,
                        rpd_used,
                        spec.rpd_limit,
                        spec.fallback_model,
                    )
                    target_model = spec.fallback_model
                    continue
                else:
                    logger.warning(
                        "[QUOTA SENTINEL] Daily RPD limit for '%s' reached (%d/%d) and no fallback available.",
                        target_model,
                        rpd_used,
                        spec.rpd_limit,
                    )
            break

        # 2. In-memory sliding window check (RPM & TPM)
        spec = get_model_quota_spec(target_model)
        rpm_used, tpm_used = self.store.get_sliding_window_usage(target_model, now=current_time)
        wait_seconds = 0.0

        if spec.rpm_limit > 0 and rpm_used >= spec.rpm_limit:
            oldest = self.store.get_oldest_timestamp_in_window(target_model, now=current_time)
            if oldest is not None:
                remaining = 60.0 - (current_time - oldest)
                wait_seconds = max(0.0, remaining + 0.1)

        if spec.tpm_limit > 0 and (tpm_used + estimated_tokens) > spec.tpm_limit:
            oldest = self.store.get_oldest_timestamp_in_window(target_model, now=current_time)
            if oldest is not None:
                remaining = 60.0 - (current_time - oldest)
                wait_seconds = max(wait_seconds, max(0.0, remaining + 0.1))

        return target_model, wait_seconds

    def postflight(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        timestamp: float | None = None,
    ) -> None:
        """Record usage after an API call completes successfully."""
        if not self.is_enabled():
            return

        target_model = model.rsplit("/", 1)[-1]
        self.store.record_request(
            target_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            timestamp=timestamp,
        )

    def get_status_summaries(
        self,
        date_str: str | None = None,
        now: float | None = None,
    ) -> list[QuotaUsageSummary]:
        """Compile status telemetry summaries across all tracked models."""
        target_date = get_pacific_date_str() if date_str is None else date_str
        current_time = time.time() if now is None else now
        daily_data = self.store.get_daily_usage(date_str=target_date)

        # Standard ordered list of models to present
        ordered_keys = [
            "gemini-4-hydrogen",
            "gemini-3.8-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-decision-1",
            "gemma-4-31b-it",
            "gemma-4-26b-a4b-it",
            "gemini-embedding-001",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        ]

        all_keys = list(ordered_keys)
        for key in sorted(daily_data.keys()):
            if key not in all_keys:
                all_keys.append(key)

        summaries: list[QuotaUsageSummary] = []
        for model_id in all_keys:
            spec = get_model_quota_spec(model_id)
            rpd_used = daily_data.get(model_id, {}).get("request_count", 0)
            rpm_used, tpm_used = self.store.get_sliding_window_usage(model_id, now=current_time)

            rpd_pct = (rpd_used / spec.rpd_limit * 100.0) if spec.rpd_limit > 0 else 0.0
            rpm_pct = (rpm_used / spec.rpm_limit * 100.0) if spec.rpm_limit > 0 else 0.0
            tpm_pct = (tpm_used / spec.tpm_limit * 100.0) if spec.tpm_limit > 0 else 0.0

            if spec.rpd_limit > 0 and rpd_used >= spec.rpd_limit:
                status = "EXHAUSTED"
            elif spec.rpd_limit > 0 and rpd_used >= int(spec.rpd_limit * 0.85):
                status = "NEAR LIMIT"
            elif spec.rpm_limit > 0 and rpm_used >= spec.rpm_limit:
                status = "BURST THROTTLE"
            elif spec.rpd_limit >= 1000 and rpd_used < int(spec.rpd_limit * 0.5):
                status = "HEALTHY"
            else:
                status = "OK"

            summaries.append(
                QuotaUsageSummary(
                    model_id=model_id,
                    category=spec.category,
                    rpd_used=rpd_used,
                    rpd_limit=spec.rpd_limit,
                    rpm_used=rpm_used,
                    rpm_limit=spec.rpm_limit,
                    tpm_used=tpm_used,
                    tpm_limit=spec.tpm_limit,
                    status=status,
                    rpd_percentage=round(rpd_pct, 1),
                    rpm_percentage=round(rpm_pct, 1),
                    tpm_percentage=round(tpm_pct, 1),
                )
            )

        return summaries


def get_quota_sentinel() -> QuotaSentinel:
    """Return the global singleton QuotaSentinel instance."""
    global _sentinel_instance
    if _sentinel_instance is None:
        with _sentinel_lock:
            if _sentinel_instance is None:
                _sentinel_instance = QuotaSentinel()
    return _sentinel_instance


def reset_quota_sentinel() -> None:
    """Reset the global singleton QuotaSentinel instance (for test isolation)."""
    global _sentinel_instance
    with _sentinel_lock:
        _sentinel_instance = None
