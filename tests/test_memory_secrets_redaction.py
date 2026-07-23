from __future__ import annotations

import pytest

from sakthai.memory.store import SNAPSHOT_VERSION, MemoryStore


@pytest.fixture
def secret() -> str:
    return "sk-ant-api03-1234567890123456789012345678901234567890"


def test_add_fact_redacts_all_fields(store: MemoryStore, secret: str) -> None:
    store.add_fact(
        value=f"secret value {secret}",
        kind=f"kind-{secret}",
        key=f"key-{secret}",
        source_session=f"session-{secret}",
        tags=[secret, "safe"],
    )
    fact = store.list_facts()[0]
    assert secret not in fact.value
    assert "[REDACTED]" in fact.value
    assert secret not in fact.kind
    assert "[REDACTED]" in fact.kind
    assert secret not in fact.key
    assert "[REDACTED]" in fact.key
    assert secret not in fact.tags
    assert "[REDACTED]" in fact.tags
    assert "safe" in fact.tags
    assert secret not in fact.source_session
    assert "[REDACTED]" in fact.source_session


def test_update_fact_redacts_all_fields(store: MemoryStore, secret: str) -> None:
    fid = store.add_fact("safe")
    store.update_fact(fid, value=f"new secret {secret}", tags=[secret])
    fact = store.list_facts()[0]
    assert secret not in fact.value
    assert "[REDACTED]" in fact.value
    assert secret not in fact.tags
    assert "[REDACTED]" in fact.tags


def test_add_observation_redacts_all_fields(store: MemoryStore, secret: str) -> None:
    store.add_observation(summary=f"obs secret {secret}", evidence_session_id=f"session-{secret}")
    obs = store.top_observations()[0]
    assert secret not in obs.summary
    assert "[REDACTED]" in obs.summary
    assert secret not in obs.evidence_session_id
    assert "[REDACTED]" in obs.evidence_session_id


def test_import_from_dict_redacts_all_fields(store: MemoryStore, secret: str) -> None:
    snapshot = {
        "version": SNAPSHOT_VERSION,
        "exported_at": 123,
        "facts": [
            {
                "id": 1,
                "kind": f"kind-{secret}",
                "key": f"key-{secret}",
                "value": f"val-{secret}",
                "source_session": f"sid-{secret}",
                "created_at": 123,
                "updated_at": 123,
                "tags": [secret],
            }
        ],
        "observations": [
            {
                "id": 1,
                "summary": f"sum-{secret}",
                "evidence_session_id": f"sid-{secret}",
                "weight": 1.0,
                "confidence": 0.5,
                "created_at": 123,
            }
        ],
    }
    store.import_from_dict(snapshot, mode="replace")

    fact = store.list_facts()[0]
    assert secret not in fact.kind
    assert secret not in fact.key
    assert secret not in fact.value
    assert secret not in fact.tags
    assert secret not in fact.source_session
    assert "[REDACTED]" in fact.kind
    assert "[REDACTED]" in fact.key
    assert "[REDACTED]" in fact.value
    assert "[REDACTED]" in fact.tags
    assert "[REDACTED]" in fact.source_session

    obs = store.top_observations()[0]
    assert secret not in obs.summary
    assert secret not in obs.evidence_session_id
    assert "[REDACTED]" in obs.summary
    assert "[REDACTED]" in obs.evidence_session_id


def test_additional_secrets_redacted() -> None:
    from sakthai.config import redact_secrets

    # 1. Test AWS key
    aws_key = "AKIA" + "IOSFODNN7EXAMPLE"
    assert redact_secrets(aws_key) == "[REDACTED]"
    assert redact_secrets(f"my key is {aws_key}") == "my key is [REDACTED]"

    # 2. Test fine-grained GitHub PAT
    gh_pat = "github_pat_" + "123456789012345678901234567890123456789012345678901234567890"
    assert redact_secrets(gh_pat) == "[REDACTED]"
    assert redact_secrets(f"my token is {gh_pat}") == "my token is [REDACTED]"

    # 3. Test PEM Private Key block
    pem_block = (
        "-----BEGIN " + "RSA PRIVATE KEY-----\n"
        "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDOf7Zp5iVzZpWk\n"
        "-----END " + "RSA PRIVATE KEY-----"
    )
    assert redact_secrets(pem_block) == "[REDACTED]"
    assert redact_secrets(f"headers\n{pem_block}\nfooters") == "headers\n[REDACTED]\nfooters"
