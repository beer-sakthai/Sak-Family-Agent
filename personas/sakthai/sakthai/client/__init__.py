"""ServiceQuoteBot Client Provisioning, Onboarding, and Verification."""

from __future__ import annotations

from .manager import (
    generate_client_env,
    generate_docker_compose,
    generate_systemd_service,
    get_client_dir,
    get_clients_base_dir,
    ingest_client_price_book,
    list_clients,
    load_client,
    onboard_client,
    save_client,
)
from .models import (
    ClientConfig,
    OnboardResult,
    SyntheticTestCase,
    SyntheticTestResult,
    VerificationResult,
)
from .verifier import (
    DEFAULT_TEST_CASES,
    run_client_verification,
)

__all__ = [
    "ClientConfig",
    "DEFAULT_TEST_CASES",
    "OnboardResult",
    "SyntheticTestCase",
    "SyntheticTestResult",
    "VerificationResult",
    "generate_client_env",
    "generate_docker_compose",
    "generate_systemd_service",
    "get_client_dir",
    "get_clients_base_dir",
    "ingest_client_price_book",
    "list_clients",
    "load_client",
    "onboard_client",
    "run_client_verification",
    "save_client",
]
