from app.agent_platform.safety import DataLossGuardrail


def test_guardrail_allows_safe_command():
    guard = DataLossGuardrail()
    result = guard.inspect("git status && ls -la")
    assert not result.is_destructive
    assert not result.blocked
    assert result.reason == "Command verified safe"


def test_guardrail_blocks_destructive_shell_command():
    guard = DataLossGuardrail()
    result = guard.inspect("rm -rf /tmp/my_data")
    assert result.is_destructive
    assert result.blocked
    assert "destructive file deletion" in result.reason.lower()
    assert "/tmp/my_data" in result.impact


def test_guardrail_blocks_destructive_sql():
    guard = DataLossGuardrail()
    result = guard.inspect("DROP TABLE customers;")
    assert result.is_destructive
    assert result.blocked
    assert "destructive database operation" in result.reason.lower()


def test_guardrail_allows_with_explicit_approval_token():
    guard = DataLossGuardrail()
    command = "rm -rf .cache"
    token = guard.generate_approval_token(command)
    result = guard.verify_or_halt(command, approval_token=token)
    assert result.is_destructive
    assert not result.blocked


def test_verify_or_halt_allows_safe_command_directly():
    guard = DataLossGuardrail()
    result = guard.verify_or_halt("git status && ls -la")
    assert not result.is_destructive
    assert not result.blocked
    assert result.reason == "Command verified safe"


def test_verify_or_halt_blocks_destructive_command_without_token():
    guard = DataLossGuardrail()
    result = guard.verify_or_halt("rm -rf /tmp/my_data")
    assert result.is_destructive
    assert result.blocked


def test_verify_or_halt_blocks_destructive_command_with_invalid_token():
    guard = DataLossGuardrail()
    result = guard.verify_or_halt("rm -rf /tmp/my_data", approval_token="APPROVE_invalidtoken")
    assert result.is_destructive
    assert result.blocked


def test_guardrail_blocks_destructive_gsutil_rm():
    guard = DataLossGuardrail()
    result = guard.inspect("gsutil rm -r gs://my-bucket/data")
    assert result.is_destructive
    assert result.blocked
    assert "cloud storage bucket/object deletion" in result.reason.lower()
    assert "gs://my-bucket/data" in result.impact


def test_guardrail_blocks_destructive_bq_rm():
    guard = DataLossGuardrail()
    result = guard.inspect("bq rm -f my_dataset.my_table")
    assert result.is_destructive
    assert result.blocked
    assert "bigquery table/dataset deletion" in result.reason.lower()
    assert "my_dataset.my_table" in result.impact


def test_guardrail_blocks_destructive_truncate():
    guard = DataLossGuardrail()
    result_with_table = guard.inspect("TRUNCATE TABLE customers;")
    assert result_with_table.is_destructive
    assert result_with_table.blocked
    assert "destructive database operation" in result_with_table.reason.lower()

    result_without_table = guard.inspect("TRUNCATE customers;")
    assert result_without_table.is_destructive
    assert result_without_table.blocked
    assert "destructive database operation" in result_without_table.reason.lower()


def test_guardrail_blocks_unbounded_delete_operations():
    guard = DataLossGuardrail()
    cases = [
        "DELETE FROM customers;",
        "DELETE FROM dataset.table;",
        "DELETE FROM project.dataset.table;",
        "DELETE FROM `dataset.table`;",
        "DELETE FROM `project`.`dataset`.`table`;",
        'DELETE FROM "dataset"."table";',
        "DELETE FROM customers",
    ]
    for sql in cases:
        result = guard.inspect(sql)
        assert result.is_destructive, f"Expected destructive for: {sql}"
        assert result.blocked, f"Expected blocked for: {sql}"
        assert "unbounded delete operation without where clause" in result.reason.lower()


def test_guardrail_allows_bounded_delete_with_where_clause():
    guard = DataLossGuardrail()
    cases = [
        "DELETE FROM customers WHERE id = 1;",
        "DELETE FROM dataset.table WHERE active = false;",
        "DELETE FROM `dataset.table` WHERE created_at < '2026-01-01';",
    ]
    for sql in cases:
        result = guard.inspect(sql)
        assert not result.is_destructive, f"Expected safe for bounded delete: {sql}"
        assert not result.blocked, f"Expected unblocked for bounded delete: {sql}"
