"""Tests for Hugging Face Space Telemetry and Alert Monitoring Subsystem."""

from unittest.mock import MagicMock, patch

from sakthai.hub.telemetry import (
    SpaceAlertNotifier,
    SpaceHealthAlert,
    SpaceTelemetryCollector,
    SpaceTelemetryRecord,
)


def test_collect_space_telemetry_metrics() -> None:
    collector = SpaceTelemetryCollector()
    rec = collector.collect_space_telemetry(
        repo_id="Nanthasit/sakthai-tts",
        runtime_stage="RUNNING",
        cpu_usage_pct=34.2,
        memory_usage_mb=2048.0,
        memory_total_mb=8192.0,
        http_latency_ms=150.0,
        hardware_tier="t4-small",
    )

    assert rec.repo_id == "Nanthasit/sakthai-tts"
    assert rec.cpu_usage_pct == 34.2
    assert rec.memory_usage_mb == 2048.0
    data = rec.to_dict()
    assert data["memory_pct"] == 25.0
    assert data["http_latency_ms"] == 150.0


def test_collect_all_spaces() -> None:
    collector = SpaceTelemetryCollector()
    spaces = collector.collect_all_spaces()
    assert len(spaces) == 4
    repo_ids = [s.repo_id for s in spaces]
    assert "Nanthasit/sakthai-tts" in repo_ids
    assert "Nanthasit/sakthai-vision" in repo_ids


def test_evaluate_health_alerts_down() -> None:
    collector = SpaceTelemetryCollector()
    rec = SpaceTelemetryRecord(
        repo_id="Nanthasit/sakthai-rag-demo",
        runtime_stage="RUNTIME_ERROR",
        hardware_tier="cpu-basic",
        cpu_usage_pct=0.0,
        memory_usage_mb=0.0,
        memory_total_mb=8192.0,
        http_latency_ms=0.0,
        error_rate_pct=100.0,
        uptime_sec=0,
    )

    alerts = collector.evaluate_health_alerts(rec)
    assert len(alerts) >= 1
    assert any(a.alert_type == "SPACE_DOWN" and a.severity == "CRITICAL" for a in alerts)


def test_evaluate_health_alerts_cpu_mem_latency() -> None:
    collector = SpaceTelemetryCollector()
    rec = SpaceTelemetryRecord(
        repo_id="Nanthasit/sakthai-tts",
        runtime_stage="RUNNING",
        hardware_tier="t4-small",
        cpu_usage_pct=92.5,  # > 85%
        memory_usage_mb=7800.0,  # 7800 / 8192 > 90%
        memory_total_mb=8192.0,
        http_latency_ms=2500.0,  # > 2000ms
        error_rate_pct=2.0,
        uptime_sec=3600,
    )

    alerts = collector.evaluate_health_alerts(rec)
    types = [a.alert_type for a in alerts]
    assert "HIGH_CPU" in types
    assert "HIGH_MEMORY_OOM_RISK" in types
    assert "HIGH_LATENCY" in types


def test_alert_notifier_dispatch() -> None:
    notifier_none = SpaceAlertNotifier(webhook_url=None)
    alert = SpaceHealthAlert(
        alert_id="alt_1",
        repo_id="Nanthasit/sakthai-tts",
        severity="WARNING",
        alert_type="HIGH_CPU",
        message="CPU high",
    )
    assert notifier_none.dispatch_alert(alert) is False

    notifier_invalid = SpaceAlertNotifier(webhook_url="http://insecure.test/webhook")
    assert notifier_invalid.dispatch_alert(alert) is False

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        notifier_https = SpaceAlertNotifier(webhook_url="https://api.telegram.org/bot123/alert")
        assert notifier_https.dispatch_alert(alert) is True
