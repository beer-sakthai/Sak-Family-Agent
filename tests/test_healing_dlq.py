# tests/test_healing_dlq.py
import pytest

from sakthai.healing.dlq import DeadLetterQueue
from sakthai.healing.models import DLQItem


@pytest.fixture
def temp_dlq(tmp_path):
    db_path = tmp_path / "test_dlq.db"
    return DeadLetterQueue(db_path=db_path)


def test_dlq_enqueue_and_peek(temp_dlq):
    item = DLQItem(
        dlq_id="dlq-001",
        incident_id="inc-001",
        persona="saksee",
        payload={"url": "https://example.com/asset"},
        error_message="HTTP 500 Server Error",
    )
    temp_dlq.enqueue(item)

    items = temp_dlq.peek(limit=10)
    assert len(items) == 1
    assert items[0].dlq_id == "dlq-001"
    assert items[0].persona == "saksee"
    assert items[0].payload == {"url": "https://example.com/asset"}


def test_dlq_retry_and_dead_transition(temp_dlq):
    item = DLQItem(
        dlq_id="dlq-002",
        incident_id="inc-002",
        persona="sakjules",
        payload={"action": "deploy"},
        error_message="Network Timeout",
        max_retries=2,
    )
    temp_dlq.enqueue(item)

    # Attempt 1
    can_retry_1 = temp_dlq.record_retry_attempt("dlq-002")
    assert can_retry_1 is True

    # Attempt 2 (reaches max retries)
    can_retry_2 = temp_dlq.record_retry_attempt("dlq-002")
    assert can_retry_2 is False

    dead_items = temp_dlq.list_dead()
    assert len(dead_items) == 1
    assert dead_items[0].status == "DEAD"


def test_dlq_resolve(temp_dlq):
    item = DLQItem(
        dlq_id="dlq-003",
        incident_id="inc-003",
        persona="sakthai",
        payload={"query": "analyze_repo"},
        error_message="Rate Limit",
    )
    temp_dlq.enqueue(item)
    temp_dlq.resolve("dlq-003")

    pending = temp_dlq.peek()
    assert len(pending) == 0
