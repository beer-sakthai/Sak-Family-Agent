"""Tests for sakthai.web.api — the payload builders behind the web API.

Every builder takes an injectable ``home``, so these run against a seeded
temporary runtime root and never touch a real ``~/.sakthai``.

The properties worth defending here are the honest ones: all six personas
appear whether or not they have run, a record with no persona lands in the
``unattributed`` bucket rather than being spread across personas, a
persona-scoped log attributes by its location, and a bad ``severity`` or
``limit`` narrows the result instead of silently returning everything.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from sakthai.config import PERSONA_NAMES
from sakthai.memory.store import MemoryStore
from sakthai.web import api

NOW = 1_787_000_000


def _eval_line(**overrides: Any) -> str:
    record: dict[str, Any] = {
        "timestamp": NOW,
        "task_preview": "a task",
        "model": "m1",
        "provider": "anthropic",
        "iterations": 1,
        "stop_reason": "end_turn",
        "latency_s": 1.0,
        "input_tokens": 10,
        "output_tokens": 4,
        "tool_call_count": 0,
        "had_error": False,
    }
    record.update(overrides)
    return json.dumps(record)


def _session_doc(**overrides: Any) -> str:
    doc: dict[str, Any] = {
        "timestamp": NOW,
        "task": "do the thing",
        "model": "m1",
        "persona": None,
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": [{"type": "text", "text": "yo"}]},
        ],
        "usage": {"input_tokens": 10, "output_tokens": 4, "total_tokens": 14},
        "result": {
            "text": "done",
            "iterations": 1,
            "stop_reason": "end_turn",
            "tool_calls": [{"name": "recall", "input": {}, "is_error": False}],
        },
    }
    doc.update(overrides)
    return json.dumps(doc)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """An empty runtime root — every builder must cope with nothing present."""
    root = tmp_path / "sakthai"
    root.mkdir()
    return root


@pytest.fixture
def seeded(home: Path) -> Path:
    """A runtime root with a legacy run, an attributed run, and a scoped shard."""
    (home / "sessions").mkdir()
    (home / "eval.jsonl").write_text(
        "\n".join(
            [
                _eval_line(),  # legacy: no persona key at all
                _eval_line(persona="sakthai", model="m2", had_error=True, latency_s=0.5),
                "{ not json",  # a torn line must be skipped, not fatal
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    # A persona-scoped root: no persona field, but the location attributes it.
    (home / "saksee").mkdir()
    (home / "saksee" / "eval.jsonl").write_text(_eval_line(latency_s=2.0) + "\n", encoding="utf-8")
    (home / "sessions" / f"{NOW}_abc.json").write_text(
        _session_doc(persona="sakthai"), encoding="utf-8"
    )
    (home / "audit.log").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": float(NOW),
                        "type": "mcp_validation",
                        "severity": "high",
                        "message": "blocked",
                        "details": {"server": "x"},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": float(NOW - 50),
                        "type": "env_pin",
                        "severity": "low",
                        "message": "ok",
                        "details": {},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    store = MemoryStore(home / "sakthai" / "memory.db")
    store.add_fact("dark mode", kind="preference", key="theme", tags=["ui"])
    store.add_observation("works late", weight=2.0, confidence=0.9)
    store.close()
    return home


class TestEnvelope:
    def test_defaults_to_local(self) -> None:
        assert api.envelope({"x": 1})["source"] == "local"

    def test_source_is_carried(self) -> None:
        assert api.envelope({}, "demo")["source"] == "demo"

    def test_generated_at_is_iso_utc(self) -> None:
        assert api.envelope({})["generated_at"].endswith("+00:00")

    def test_data_is_passed_through(self) -> None:
        assert api.envelope({"x": 1})["data"] == {"x": 1}


class TestDisplayName:
    @pytest.mark.parametrize("persona", PERSONA_NAMES)
    def test_every_persona_renders(self, persona: str) -> None:
        rendered = api.display_name(persona)
        assert rendered.startswith("Sak")
        assert rendered.lower() == persona


class TestRuntimeRoots:
    def test_unscoped_root_is_unattributed(self, home: Path) -> None:
        assert api.runtime_roots(home)[0] == (None, home)

    def test_one_root_per_persona(self, home: Path) -> None:
        roots = api.runtime_roots(home)
        assert len(roots) == len(PERSONA_NAMES) + 1

    def test_falls_back_to_sakthai_home(self, sakthai_home: Path) -> None:
        assert api.runtime_roots()[0][1] == sakthai_home


class TestPersonasPayload:
    def test_all_six_personas_present_on_empty_home(self, home: Path) -> None:
        """A persona that has never run is still a persona."""
        payload = api.personas_payload(home)
        assert [p["name"] for p in payload["personas"]] == list(PERSONA_NAMES)

    def test_missing_shard_reported_not_omitted(self, home: Path) -> None:
        payload = api.personas_payload(home)
        assert all(p["has_shard"] is False for p in payload["personas"])
        assert all(p["fact_count"] == 0 for p in payload["personas"])

    def test_legacy_record_counts_as_unattributed(self, seeded: Path) -> None:
        """The whole point: an unattributed run is not assigned to a persona."""
        assert api.personas_payload(seeded)["unattributed_runs"] == 1

    def test_attributed_record_reaches_its_persona(self, seeded: Path) -> None:
        by_name = {p["name"]: p for p in api.personas_payload(seeded)["personas"]}
        assert by_name["sakthai"]["runs"] == 1
        assert by_name["sakthai"]["errors"] == 1

    def test_scoped_log_attributes_by_location(self, seeded: Path) -> None:
        """A record with no persona field, in saksee's root, is saksee's."""
        by_name = {p["name"]: p for p in api.personas_payload(seeded)["personas"]}
        assert by_name["saksee"]["runs"] == 1

    def test_shard_counts_are_read(self, seeded: Path) -> None:
        by_name = {p["name"]: p for p in api.personas_payload(seeded)["personas"]}
        assert by_name["sakthai"]["has_shard"] is True
        assert by_name["sakthai"]["fact_count"] == 1
        assert by_name["sakthai"]["observation_count"] == 1

    def test_latency_is_averaged_in_ms(self, seeded: Path) -> None:
        by_name = {p["name"]: p for p in api.personas_payload(seeded)["personas"]}
        assert by_name["sakthai"]["avg_latency_ms"] == 500.0
        assert by_name["saksee"]["avg_latency_ms"] == 2000.0

    def test_last_run_at_tracks_the_newest(self, home: Path) -> None:
        (home / "eval.jsonl").write_text(
            _eval_line(persona="sakthai", timestamp=NOW)
            + "\n"
            + _eval_line(persona="sakthai", timestamp=NOW + 500)
            + "\n",
            encoding="utf-8",
        )
        by_name = {p["name"]: p for p in api.personas_payload(home)["personas"]}
        assert by_name["sakthai"]["last_run_at"] == NOW + 500

    def test_unknown_persona_in_a_record_is_unattributed(self, home: Path) -> None:
        """A persona name we don't recognise must not invent a seventh card."""
        (home / "eval.jsonl").write_text(_eval_line(persona="sakwho") + "\n", encoding="utf-8")
        payload = api.personas_payload(home)
        assert payload["unattributed_runs"] == 1
        assert len(payload["personas"]) == len(PERSONA_NAMES)

    def test_model_defaults_are_populated(self, home: Path) -> None:
        by_name = {p["name"]: p for p in api.personas_payload(home)["personas"]}
        assert by_name["sakking"]["provider"] == "huggingface"


class TestMetricsPayload:
    def test_empty_home_gives_zeroes_not_an_error(self, home: Path) -> None:
        payload = api.metrics_payload(home=home)
        assert payload["total_runs"] == 0
        assert payload["trends"] == []

    def test_counts_every_root(self, seeded: Path) -> None:
        assert api.metrics_payload(home=seeded)["total_runs"] == 3

    def test_error_rate(self, seeded: Path) -> None:
        assert api.metrics_payload(home=seeded)["error_rate"] == pytest.approx(1 / 3, abs=1e-3)

    def test_tokens_total_is_the_sum(self, seeded: Path) -> None:
        tokens = api.metrics_payload(home=seeded)["tokens"]
        assert tokens["total_tokens"] == tokens["input_tokens"] + tokens["output_tokens"]

    def test_stop_reasons_histogram(self, seeded: Path) -> None:
        assert api.metrics_payload(home=seeded)["stop_reasons"] == {"end_turn": 3}

    def test_per_model_breakdown(self, seeded: Path) -> None:
        per_model = api.metrics_payload(home=seeded)["per_model"]
        assert per_model["m1"]["count"] == 2
        assert per_model["m2"]["count"] == 1

    def test_limit_takes_the_most_recent(self, seeded: Path) -> None:
        assert api.metrics_payload(limit=1, home=seeded)["total_runs"] == 1

    def test_trends_group_by_utc_day(self, home: Path) -> None:
        day_two = NOW + 86400 * 2
        (home / "eval.jsonl").write_text(
            _eval_line(timestamp=NOW) + "\n" + _eval_line(timestamp=day_two) + "\n",
            encoding="utf-8",
        )
        trends = api.metrics_payload(home=home)["trends"]
        assert len(trends) == 2
        assert trends[0]["date"] < trends[1]["date"]

    def test_trend_skips_records_without_a_timestamp(self, home: Path) -> None:
        (home / "eval.jsonl").write_text(
            json.dumps({"model": "m", "stop_reason": "end_turn"}) + "\n", encoding="utf-8"
        )
        payload = api.metrics_payload(home=home)
        assert payload["total_runs"] == 1
        assert payload["trends"] == []

    def test_missing_model_becomes_unknown(self, home: Path) -> None:
        (home / "eval.jsonl").write_text(
            json.dumps({"timestamp": NOW, "stop_reason": "end_turn"}) + "\n", encoding="utf-8"
        )
        assert "unknown" in api.metrics_payload(home=home)["per_model"]

    def test_eval_summary_passthrough(self, seeded: Path) -> None:
        summary = api.eval_summary(path=seeded / "eval.jsonl")
        assert summary["count"] == 2


class TestSessionsPayload:
    def test_empty_home(self, home: Path) -> None:
        payload = api.sessions_payload(home=home)
        assert payload == {"sessions": [], "total": 0, "detail": None}

    def test_summary_fields(self, seeded: Path) -> None:
        session = api.sessions_payload(home=seeded)["sessions"][0]
        assert session["id"] == f"{NOW}_abc"
        assert session["persona"] == "sakthai"
        assert session["task"] == "do the thing"
        assert session["message_count"] == 2
        assert session["tool_call_count"] == 1
        assert session["tokens"]["total_tokens"] == 14

    def test_session_without_persona_reads_as_none(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_x.json").write_text(_session_doc(), encoding="utf-8")
        assert api.sessions_payload(home=home)["sessions"][0]["persona"] is None

    def test_scoped_session_attributes_by_location(self, home: Path) -> None:
        (home / "saksit" / "sessions").mkdir(parents=True)
        (home / "saksit" / "sessions" / f"{NOW}_y.json").write_text(
            _session_doc(), encoding="utf-8"
        )
        assert api.sessions_payload(home=home)["sessions"][0]["persona"] == "saksit"

    def test_had_error_from_tool_calls(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_e.json").write_text(
            _session_doc(
                result={
                    "text": "",
                    "iterations": 1,
                    "stop_reason": "end_turn",
                    "tool_calls": [{"name": "run_command", "is_error": True}],
                }
            ),
            encoding="utf-8",
        )
        assert api.sessions_payload(home=home)["sessions"][0]["had_error"] is True

    def test_corrupt_file_is_skipped_not_fatal(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_bad.json").write_text("{{{", encoding="utf-8")
        (home / "sessions" / f"{NOW}_ok.json").write_text(_session_doc(), encoding="utf-8")
        assert api.sessions_payload(home=home)["total"] == 1

    def test_non_object_json_is_skipped(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_arr.json").write_text("[1, 2]", encoding="utf-8")
        assert api.sessions_payload(home=home)["total"] == 0

    def test_newest_first(self, home: Path) -> None:
        (home / "sessions").mkdir()
        for stamp in (NOW, NOW + 10, NOW + 20):
            (home / "sessions" / f"{stamp}_s.json").write_text(
                _session_doc(timestamp=stamp), encoding="utf-8"
            )
        ids = [s["id"] for s in api.sessions_payload(home=home)["sessions"]]
        assert ids == [f"{NOW + 20}_s", f"{NOW + 10}_s", f"{NOW}_s"]

    def test_search_filters(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_a.json").write_text(
            _session_doc(task="deploy the thing"), encoding="utf-8"
        )
        (home / "sessions" / f"{NOW + 1}_b.json").write_text(
            _session_doc(task="write a report"), encoding="utf-8"
        )
        assert api.sessions_payload(search="deploy", home=home)["total"] == 1

    def test_blank_search_does_not_filter(self, seeded: Path) -> None:
        assert api.sessions_payload(search="   ", home=seeded)["total"] == 1

    def test_pagination(self, home: Path) -> None:
        (home / "sessions").mkdir()
        for i in range(5):
            (home / "sessions" / f"{NOW + i}_s.json").write_text(_session_doc(), encoding="utf-8")
        page = api.sessions_payload(limit=2, offset=2, home=home)
        assert page["total"] == 5
        assert len(page["sessions"]) == 2

    def test_limit_is_clamped_not_trusted(self, seeded: Path) -> None:
        """A silly limit must clamp, never produce an empty page by accident."""
        assert len(api.sessions_payload(limit=-5, home=seeded)["sessions"]) == 1
        assert len(api.sessions_payload(limit=10_000, home=seeded)["sessions"]) == 1

    def test_negative_offset_is_clamped(self, seeded: Path) -> None:
        assert len(api.sessions_payload(offset=-10, home=seeded)["sessions"]) == 1

    def test_detail_included_when_id_given(self, seeded: Path) -> None:
        payload = api.sessions_payload(session_id=f"{NOW}_abc", home=seeded)
        assert payload["detail"] is not None
        assert payload["detail"]["result_text"] == "done"


class TestSessionDetail:
    def test_flattens_block_content(self, seeded: Path) -> None:
        detail = api.session_detail(f"{NOW}_abc", seeded)
        assert detail is not None
        assert detail["messages"][1]["content"] == "yo"

    def test_plain_string_content_survives(self, seeded: Path) -> None:
        detail = api.session_detail(f"{NOW}_abc", seeded)
        assert detail is not None
        assert detail["messages"][0]["content"] == "hi"

    def test_tool_calls_reduced_to_name_and_error(self, seeded: Path) -> None:
        detail = api.session_detail(f"{NOW}_abc", seeded)
        assert detail is not None
        assert detail["tool_calls"] == [{"name": "recall", "is_error": False}]

    def test_unknown_id_is_none(self, seeded: Path) -> None:
        assert api.session_detail("1234_nope", seeded) is None

    @pytest.mark.parametrize("bad_id", ["../../etc/passwd", "a/b", "..", "x\x00y", "with space"])
    def test_traversal_and_junk_ids_rejected(self, bad_id: str, seeded: Path) -> None:
        """The id arrives from a query string; it must never reach a path join."""
        assert api.session_detail(bad_id, seeded) is None

    def test_corrupt_target_returns_none(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_c.json").write_text("{{{", encoding="utf-8")
        assert api.session_detail(f"{NOW}_c", home) is None

    def test_non_dict_message_entries_are_skipped(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_m.json").write_text(
            _session_doc(messages=["not a dict", {"role": "user", "content": "hi"}]),
            encoding="utf-8",
        )
        detail = api.session_detail(f"{NOW}_m", home)
        assert detail is not None
        assert len(detail["messages"]) == 1

    def test_content_list_uses_name_when_no_text(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_t.json").write_text(
            _session_doc(
                messages=[
                    {"role": "assistant", "content": [{"type": "tool_use", "name": "recall"}]}
                ]
            ),
            encoding="utf-8",
        )
        detail = api.session_detail(f"{NOW}_t", home)
        assert detail is not None
        assert detail["messages"][0]["content"] == "recall"

    def test_non_dict_block_is_stringified(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_b.json").write_text(
            _session_doc(messages=[{"role": "user", "content": ["plain", 42]}]),
            encoding="utf-8",
        )
        detail = api.session_detail(f"{NOW}_b", home)
        assert detail is not None
        assert detail["messages"][0]["content"] == "plain\n42"

    def test_null_content_becomes_empty(self, home: Path) -> None:
        (home / "sessions").mkdir()
        (home / "sessions" / f"{NOW}_n.json").write_text(
            _session_doc(messages=[{"role": "user", "content": None}]), encoding="utf-8"
        )
        detail = api.session_detail(f"{NOW}_n", home)
        assert detail is not None
        assert detail["messages"][0]["content"] == ""


class TestMemoryPayload:
    def test_empty_home(self, home: Path) -> None:
        payload = api.memory_payload(home=home)
        assert payload["facts"] == []
        assert payload["total_facts"] == 0

    def test_reads_a_shard(self, seeded: Path) -> None:
        payload = api.memory_payload(home=seeded)
        assert payload["total_facts"] == 1
        assert payload["facts"][0]["value"] == "dark mode"

    def test_facts_are_tagged_with_their_shard(self, seeded: Path) -> None:
        assert api.memory_payload(home=seeded)["facts"][0]["persona"] == "sakthai"

    def test_observations_included(self, seeded: Path) -> None:
        observations = api.memory_payload(home=seeded)["observations"]
        assert observations[0]["summary"] == "works late"
        assert observations[0]["weight"] == 2.0

    def test_kind_counts(self, seeded: Path) -> None:
        assert api.memory_payload(home=seeded)["kind_counts"] == {"preference": 1}

    def test_growth_series_is_populated(self, seeded: Path) -> None:
        """dashboard/data.py has always returned this empty; it should not be."""
        growth = api.memory_payload(home=seeded)["fact_growth"]
        assert len(growth["labels"]) == 30
        assert len(growth["values"]) == 30

    def test_growth_is_cumulative(self, home: Path) -> None:
        store = MemoryStore(home / "memory.db")
        for i in range(3):
            store.add_fact(f"fact {i}", kind="note")
        store.close()
        values = api.memory_payload(home=home)["fact_growth"]["values"]
        assert values == sorted(values)
        assert values[-1] == 3

    def test_query_searches(self, home: Path) -> None:
        store = MemoryStore(home / "memory.db")
        store.add_fact("likes coffee", kind="note")
        store.add_fact("likes tea", kind="note")
        store.close()
        assert len(api.memory_payload(query="coffee", home=home)["facts"]) == 1

    def test_blank_query_lists_everything(self, home: Path) -> None:
        store = MemoryStore(home / "memory.db")
        store.add_fact("a", kind="note")
        store.add_fact("b", kind="note")
        store.close()
        assert len(api.memory_payload(query="  ", home=home)["facts"]) == 2

    def test_merges_across_shards(self, home: Path) -> None:
        for persona, value in (("sakthai", "from thai"), ("saksee", "from see")):
            store = MemoryStore(home / persona / "memory.db")
            store.add_fact(value, kind="note")
            store.close()
        payload = api.memory_payload(home=home)
        assert payload["total_facts"] == 2
        assert {f["persona"] for f in payload["facts"]} == {"sakthai", "saksee"}

    def test_persona_subset(self, home: Path) -> None:
        for persona in ("sakthai", "saksee"):
            store = MemoryStore(home / persona / "memory.db")
            store.add_fact(f"from {persona}", kind="note")
            store.close()
        payload = api.memory_payload(personas=["sakthai"], home=home)
        assert {f["persona"] for f in payload["facts"]} == {"sakthai"}

    def test_limit_is_clamped(self, home: Path) -> None:
        store = MemoryStore(home / "memory.db")
        store.add_fact("a", kind="note")
        store.close()
        assert len(api.memory_payload(limit=-1, home=home)["facts"]) == 1
        assert len(api.memory_payload(limit=99_999, home=home)["facts"]) == 1

    def test_this_week_counter(self, home: Path) -> None:
        store = MemoryStore(home / "memory.db")
        store.add_fact("recent", kind="note")
        store.close()
        assert api.memory_payload(home=home)["facts_this_week"] == 1


class TestAuditPayload:
    def test_empty_home(self, home: Path) -> None:
        payload = api.audit_payload(home=home)
        assert payload == {"events": [], "severity_counts": {}, "total": 0}

    def test_reads_events(self, seeded: Path) -> None:
        assert api.audit_payload(home=seeded)["total"] == 2

    def test_newest_first(self, seeded: Path) -> None:
        events = api.audit_payload(home=seeded)["events"]
        assert events[0]["timestamp"] > events[1]["timestamp"]

    def test_severity_counts_cover_everything(self, seeded: Path) -> None:
        assert api.audit_payload(home=seeded)["severity_counts"] == {"high": 1, "low": 1}

    def test_severity_filter(self, seeded: Path) -> None:
        assert api.audit_payload(severity="high", home=seeded)["total"] == 1

    def test_severity_filter_is_case_insensitive(self, seeded: Path) -> None:
        assert api.audit_payload(severity="HIGH", home=seeded)["total"] == 1

    def test_unknown_severity_matches_nothing(self, seeded: Path) -> None:
        """It must narrow to zero, not silently fall back to everything."""
        assert api.audit_payload(severity="bogus", home=seeded)["total"] == 0

    def test_counts_are_unfiltered(self, seeded: Path) -> None:
        """The histogram describes the whole log, not the filtered slice."""
        payload = api.audit_payload(severity="high", home=seeded)
        assert payload["severity_counts"] == {"high": 1, "low": 1}

    def test_details_preserved(self, seeded: Path) -> None:
        events = api.audit_payload(severity="high", home=seeded)["events"]
        assert events[0]["details"] == {"server": "x"}

    def test_non_dict_details_becomes_empty(self, home: Path) -> None:
        (home / "audit.log").write_text(
            json.dumps({"timestamp": 1.0, "severity": "low", "details": "nope"}) + "\n",
            encoding="utf-8",
        )
        assert api.audit_payload(home=home)["events"][0]["details"] == {}

    def test_missing_severity_defaults_to_low(self, home: Path) -> None:
        (home / "audit.log").write_text(
            json.dumps({"timestamp": 1.0, "message": "x"}) + "\n", encoding="utf-8"
        )
        assert api.audit_payload(home=home)["events"][0]["severity"] == "low"

    def test_scoped_audit_log_is_read(self, home: Path) -> None:
        (home / "sakjules").mkdir()
        (home / "sakjules" / "audit.log").write_text(
            json.dumps({"timestamp": 1.0, "severity": "high", "message": "x"}) + "\n",
            encoding="utf-8",
        )
        assert api.audit_payload(home=home)["total"] == 1

    def test_malformed_line_skipped(self, home: Path) -> None:
        (home / "audit.log").write_text(
            "not json\n" + json.dumps({"timestamp": 1.0, "severity": "low"}) + "\n",
            encoding="utf-8",
        )
        assert api.audit_payload(home=home)["total"] == 1

    def test_non_object_line_skipped(self, home: Path) -> None:
        (home / "audit.log").write_text("[1,2]\n", encoding="utf-8")
        assert api.audit_payload(home=home)["total"] == 0

    def test_blank_lines_skipped(self, home: Path) -> None:
        (home / "audit.log").write_text("\n\n", encoding="utf-8")
        assert api.audit_payload(home=home)["total"] == 0

    def test_limit_is_clamped(self, seeded: Path) -> None:
        assert len(api.audit_payload(limit=-1, home=seeded)["events"]) == 1
        assert len(api.audit_payload(limit=99_999, home=seeded)["events"]) == 2

    def test_unreadable_file_is_not_fatal(self, home: Path, monkeypatch: Any) -> None:
        (home / "audit.log").write_text("{}\n", encoding="utf-8")
        original = Path.read_text

        def boom(self: Path, *args: Any, **kwargs: Any) -> str:
            if self.name == "audit.log":
                raise OSError("permission denied")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", boom)
        assert api.audit_payload(home=home)["total"] == 0


class TestDefaultHomeResolution:
    """The builders must work with no explicit home, off SAKTHAI_HOME."""

    def test_personas_uses_sakthai_home(self, sakthai_home: Path) -> None:
        assert api.personas_payload()["personas"][0]["name"] == PERSONA_NAMES[0]

    def test_metrics_uses_sakthai_home(self, sakthai_home: Path) -> None:
        (sakthai_home / "eval.jsonl").write_text(
            _eval_line(timestamp=int(time.time())) + "\n", encoding="utf-8"
        )
        assert api.metrics_payload()["total_runs"] == 1

    def test_sessions_uses_sakthai_home(self, sakthai_home: Path) -> None:
        assert api.sessions_payload()["total"] == 0

    def test_audit_uses_sakthai_home(self, sakthai_home: Path) -> None:
        assert api.audit_payload()["total"] == 0

    def test_memory_uses_sakthai_home(self, sakthai_home: Path) -> None:
        assert api.memory_payload()["total_facts"] == 0


class TestWorkflowsPayload:
    """Workflow runs written by apps/agent_workflow_framework.

    The framework is a separate stdlib-only package outside this one's
    dependency graph, so these fixtures mirror the on-disk format
    ``RunHistoryStore`` writes (``RunHistory.to_dict()``) rather than importing
    it. ``tests/test_workflow_storage_location.py`` pins that format down
    against the real writer.
    """

    @staticmethod
    def _run_doc(**overrides: Any) -> str:
        doc: dict[str, Any] = {
            "run_id": "run-1",
            "workflow_name": "nightly",
            "status": "completed",
            "start_time": "2026-08-26T10:00:00",
            "end_time": "2026-08-26T10:00:30",
            "step_results": {
                "fetch": {
                    "step_id": "fetch",
                    "status": "completed",
                    "output": {"n": 1},
                    "error": None,
                    "attempts": 1,
                    "start_time": "2026-08-26T10:00:00",
                    "end_time": "2026-08-26T10:00:10",
                },
                "publish": {
                    "step_id": "publish",
                    "status": "failed",
                    "output": {},
                    "error": "boom",
                    "attempts": 3,
                    "start_time": "2026-08-26T10:00:10",
                    "end_time": "2026-08-26T10:00:30",
                },
            },
        }
        doc.update(overrides)
        return json.dumps(doc)

    def _seed(self, home: Path, run_id: str = "run-1", **overrides: Any) -> Path:
        runs = home / "workflow_runs"
        runs.mkdir(exist_ok=True)
        path = runs / f"{run_id}.json"
        path.write_text(self._run_doc(run_id=run_id, **overrides), encoding="utf-8")
        return path

    def test_missing_directory_is_empty_not_an_error(self, home: Path) -> None:
        assert api.workflows_payload(home=home) == {"runs": []}

    def test_summary_fields(self, home: Path) -> None:
        self._seed(home)
        run = api.workflows_payload(home=home)["runs"][0]
        assert run["run_id"] == "run-1"
        assert run["workflow_name"] == "nightly"
        assert run["status"] == "completed"
        assert run["step_count"] == 2
        assert run["failed_steps"] == 1

    def test_duration_is_computed_from_iso_stamps(self, home: Path) -> None:
        self._seed(home)
        assert api.workflows_payload(home=home)["runs"][0]["duration_seconds"] == 30.0

    def test_duration_is_none_without_an_end(self, home: Path) -> None:
        self._seed(home, end_time=None)
        assert api.workflows_payload(home=home)["runs"][0]["duration_seconds"] is None

    def test_duration_is_none_for_unparseable_stamps(self, home: Path) -> None:
        self._seed(home, start_time="not-a-date")
        assert api.workflows_payload(home=home)["runs"][0]["duration_seconds"] is None

    def test_newest_first(self, home: Path) -> None:
        self._seed(home, "run-a", start_time="2026-08-26T09:00:00")
        self._seed(home, "run-b", start_time="2026-08-26T11:00:00")
        assert [r["run_id"] for r in api.workflows_payload(home=home)["runs"]] == [
            "run-b",
            "run-a",
        ]

    def test_corrupt_run_file_is_skipped(self, home: Path) -> None:
        self._seed(home)
        (home / "workflow_runs" / "broken.json").write_text("{{{", encoding="utf-8")
        assert len(api.workflows_payload(home=home)["runs"]) == 1

    def test_limit_is_clamped(self, home: Path) -> None:
        self._seed(home)
        assert len(api.workflows_payload(limit=-3, home=home)["runs"]) == 1
        assert len(api.workflows_payload(limit=99_999, home=home)["runs"]) == 1

    def test_uses_config_dir_by_default(self, sakthai_home: Path) -> None:
        assert api.workflow_runs_dir() == sakthai_home / "workflow_runs"


class TestWorkflowDetail:
    def test_steps_are_returned(self, home: Path) -> None:
        TestWorkflowsPayload()._seed(home)
        detail = api.workflow_detail("run-1", home)
        assert detail is not None
        assert {s["step_id"] for s in detail["steps"]} == {"fetch", "publish"}

    def test_step_error_and_attempts(self, home: Path) -> None:
        TestWorkflowsPayload()._seed(home)
        detail = api.workflow_detail("run-1", home)
        assert detail is not None
        failed = next(s for s in detail["steps"] if s["step_id"] == "publish")
        assert failed["error"] == "boom"
        assert failed["attempts"] == 3
        assert failed["duration_seconds"] == 20.0

    def test_unknown_run_is_none(self, home: Path) -> None:
        assert api.workflow_detail("nope", home) is None

    @pytest.mark.parametrize("bad_id", ["../../etc/passwd", "a/b", "..", "with space"])
    def test_traversal_ids_rejected(self, bad_id: str, home: Path) -> None:
        (home / "workflow_runs").mkdir()
        assert api.workflow_detail(bad_id, home) is None

    def test_corrupt_run_is_none(self, home: Path) -> None:
        runs = home / "workflow_runs"
        runs.mkdir()
        (runs / "bad.json").write_text("{{{", encoding="utf-8")
        assert api.workflow_detail("bad", home) is None

    def test_non_dict_step_entry_tolerated(self, home: Path) -> None:
        runs = home / "workflow_runs"
        runs.mkdir()
        (runs / "r.json").write_text(
            json.dumps(
                {
                    "run_id": "r",
                    "workflow_name": "w",
                    "status": "completed",
                    "start_time": None,
                    "end_time": None,
                    "step_results": {"a": "not a dict"},
                }
            ),
            encoding="utf-8",
        )
        detail = api.workflow_detail("r", home)
        assert detail is not None
        assert detail["steps"][0]["step_id"] == ""
