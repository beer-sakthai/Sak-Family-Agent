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


def test_redact_new_secret_patterns(store: MemoryStore) -> None:
    # AWS Access Key ID (constructed dynamically to avoid gitleaks false positives)
    aws_prefix = "AKIA"
    aws_suffix = "1234567890123456"
    aws_key = f"{aws_prefix}{aws_suffix}"

    store.add_fact(value=f"my aws key is {aws_key}")
    fact1 = store.list_facts()[0]
    assert aws_key not in fact1.value
    assert "[REDACTED]" in fact1.value

    # Fine-grained GitHub PAT (constructed dynamically to avoid gitleaks false positives)
    gh_prefix = "github_pat_"
    gh_suffix = "a" * 82
    github_pat = f"{gh_prefix}{gh_suffix}"

    store.add_fact(value=f"my pat is {github_pat}")
    fact2 = store.list_facts()[0]
    assert github_pat not in fact2.value
    assert "[REDACTED]" in fact2.value


def test_redact_pem_private_keys(store: MemoryStore) -> None:
    # PEM Private Key (constructed dynamically to avoid gitleaks false positives)
    begin_marker = "-----BEGIN " + "RSA PRIVATE KEY-----"
    end_marker = "-----END " + "RSA PRIVATE KEY-----"
    content = "MIIEowIBAAKCAQE" + "A0Yp7gYm"
    private_key_block = f"{begin_marker}\n{content}\n{end_marker}"

    store.add_fact(value=f"here is a key:\n{private_key_block}\nand some other text")
    fact = store.list_facts()[0]
    assert private_key_block not in fact.value
    assert "[REDACTED PRIVATE KEY]" in fact.value
