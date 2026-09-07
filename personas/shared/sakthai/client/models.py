"""Data models for ServiceQuoteBot client provisioning and verification."""

from __future__ import annotations

import datetime
import re
from dataclasses import asdict, dataclass, field
from typing import Any


def _slugify(text: str) -> str:
    """Normalize client ID into lowercase alphanumeric slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


@dataclass(frozen=True)
class ClientConfig:
    """Configuration for a provisioned ServiceQuoteBot client."""

    client_id: str
    company_name: str
    currency: str = "USD"
    price_book_path: str = ""
    telegram_bot_token: str = ""
    telegram_allowed_user_ids: tuple[int, ...] = ()
    model: str = "anthropic/claude-3-5-sonnet"
    provider: str = "anthropic"
    port: int = 8080
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())

    def __post_init__(self) -> None:
        object.__setattr__(self, "client_id", _slugify(self.client_id))
        if not self.client_id:
            raise ValueError("client_id cannot be empty")
        if not self.company_name.strip():
            raise ValueError("company_name cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to dictionary."""
        data = asdict(self)
        data["telegram_allowed_user_ids"] = list(self.telegram_allowed_user_ids)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClientConfig:
        """Create ClientConfig instance from dictionary."""
        allowed_users = data.get("telegram_allowed_user_ids", ())
        if isinstance(allowed_users, list):
            allowed_users_tuple = tuple(int(uid) for uid in allowed_users)
        else:
            allowed_users_tuple = tuple(allowed_users)

        return cls(
            client_id=str(data.get("client_id", "")),
            company_name=str(data.get("company_name", "")),
            currency=str(data.get("currency", "USD")),
            price_book_path=str(data.get("price_book_path", "")),
            telegram_bot_token=str(data.get("telegram_bot_token", "")),
            telegram_allowed_user_ids=allowed_users_tuple,
            model=str(data.get("model", "anthropic/claude-3-5-sonnet")),
            provider=str(data.get("provider", "anthropic")),
            port=int(data.get("port", 8080)),
            created_at=str(data.get("created_at", datetime.datetime.now(datetime.UTC).isoformat())),
            updated_at=str(data.get("updated_at", datetime.datetime.now(datetime.UTC).isoformat())),
        )

    def mask_sensitive(self) -> dict[str, Any]:
        """Return dict with masked credentials safe for logging and CLI display."""
        d = self.to_dict()
        token = self.telegram_bot_token
        if token and len(token) > 8:
            d["telegram_bot_token"] = f"{token[:4]}...{token[-4:]}"
        elif token:
            d["telegram_bot_token"] = "***"  # nosec B105
        return d


@dataclass(frozen=True)
class OnboardResult:
    """Outcome of client provisioning pipeline."""

    client_id: str
    workspace_dir: str
    env_file: str
    memory_db: str
    ingested_facts_count: int
    config_file: str
    service_file: str = ""
    compose_file: str = ""
    success: bool = True
    error_message: str = ""


@dataclass(frozen=True)
class SyntheticTestCase:
    """A synthetic test scenario to verify quoting behavior."""

    name: str
    customer_message: str
    expected_keywords: tuple[str, ...] = ()
    expected_price_min: float | None = None
    is_lead_capture_test: bool = False


@dataclass(frozen=True)
class SyntheticTestResult:
    """Result of executing a single synthetic test case."""

    test_name: str
    passed: bool
    response_text: str
    details: str = ""


@dataclass(frozen=True)
class VerificationResult:
    """Aggregated verification results for a client installation."""

    client_id: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    all_passed: bool
    results: tuple[SyntheticTestResult, ...]
    summary: str
