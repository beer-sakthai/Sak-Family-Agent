"""Contract test between agent_workflow's writer and sakthai's reader.

``apps/agent_workflow_framework`` writes workflow run histories; ``web/api.py``
reads them. The two are separate packages — the framework is stdlib-only and
deliberately does not import ``sakthai`` — so the on-disk JSON *is* the
interface between them, and nothing else would notice if it drifted.

These tests import the real ``RunHistoryStore``, write a run with it, and read
it back with the real payload builders. If the framework changes its format, or
someone reverts the storage location, this fails.

The framework is not an installed package (``apps/`` is outside
``[tool.setuptools.packages.find]``), so its directory is put on ``sys.path``
here; the tests skip rather than error if it is ever removed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sakthai.config import workflow_runs_dir
from sakthai.web import api

_FRAMEWORK_DIR = Path(__file__).resolve().parents[1] / "apps" / "agent_workflow_framework"

if _FRAMEWORK_DIR.is_dir() and str(_FRAMEWORK_DIR) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_DIR))

agent_workflow = pytest.importorskip(
    "agent_workflow.persistence", reason="apps/agent_workflow_framework not available"
)
from agent_workflow.models import RunHistory, RunStatus, StepResult, StepStatus  # noqa: E402
from agent_workflow.persistence import RunHistoryStore, default_storage_dir  # noqa: E402


def _run(run_id: str = "run-1") -> RunHistory:
    history = RunHistory(
        run_id=run_id,
        workflow_name="nightly",
        status=RunStatus.COMPLETED,
        start_time="2026-08-26T10:00:00",
        end_time="2026-08-26T10:00:30",
    )
    history.add_step_result(
        StepResult(
            step_id="fetch",
            status=StepStatus.COMPLETED,
            output={"rows": 3},
            attempts=1,
            start_time="2026-08-26T10:00:00",
            end_time="2026-08-26T10:00:10",
        )
    )
    history.add_step_result(
        StepResult(
            step_id="publish",
            status=StepStatus.FAILED,
            error="boom",
            attempts=3,
            start_time="2026-08-26T10:00:10",
            end_time="2026-08-26T10:00:30",
        )
    )
    return history


class TestStorageLocation:
    """Runs must land where sakthai looks for them, not relative to cwd."""

    def test_default_dir_follows_sakthai_home(self, sakthai_home: Path) -> None:
        assert default_storage_dir() == sakthai_home / "workflow_runs"

    def test_the_two_packages_agree_on_the_path(self, sakthai_home: Path) -> None:
        """config.workflow_runs_dir() and the framework must not drift."""
        assert default_storage_dir() == workflow_runs_dir()

    def test_store_writes_there_by_default(self, sakthai_home: Path) -> None:
        store = RunHistoryStore()
        assert store.storage_dir == (sakthai_home / "workflow_runs").resolve()

    def test_explicit_dir_still_wins(self, tmp_path: Path, sakthai_home: Path) -> None:
        store = RunHistoryStore(storage_dir=tmp_path / "elsewhere")
        assert store.storage_dir == (tmp_path / "elsewhere").resolve()

    def test_falls_back_when_home_is_unresolvable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A container with no home directory must not crash the store."""
        monkeypatch.delenv("SAKTHAI_HOME", raising=False)
        monkeypatch.setattr(
            Path, "home", staticmethod(lambda: (_ for _ in ()).throw(RuntimeError()))
        )
        assert default_storage_dir() == Path(RunHistoryStore.FALLBACK_STORAGE_DIR)


class TestFormatContract:
    """What the framework writes is what web/api.py reads."""

    def test_a_real_run_appears_in_the_payload(self, sakthai_home: Path) -> None:
        RunHistoryStore().save_run_history(_run())

        runs = api.workflows_payload(home=sakthai_home)["runs"]
        assert len(runs) == 1
        assert runs[0]["run_id"] == "run-1"
        assert runs[0]["workflow_name"] == "nightly"

    def test_status_enum_serialises_to_the_string_the_reader_expects(
        self, sakthai_home: Path
    ) -> None:
        RunHistoryStore().save_run_history(_run())
        assert api.workflows_payload(home=sakthai_home)["runs"][0]["status"] == "completed"

    def test_step_counts_match_the_written_run(self, sakthai_home: Path) -> None:
        RunHistoryStore().save_run_history(_run())
        run = api.workflows_payload(home=sakthai_home)["runs"][0]
        assert run["step_count"] == 2
        assert run["failed_steps"] == 1

    def test_duration_is_derived_from_the_written_iso_stamps(self, sakthai_home: Path) -> None:
        RunHistoryStore().save_run_history(_run())
        assert api.workflows_payload(home=sakthai_home)["runs"][0]["duration_seconds"] == 30.0

    def test_detail_round_trips_every_step(self, sakthai_home: Path) -> None:
        RunHistoryStore().save_run_history(_run())

        detail = api.workflow_detail("run-1", sakthai_home)
        assert detail is not None
        by_id = {step["step_id"]: step for step in detail["steps"]}
        assert set(by_id) == {"fetch", "publish"}
        assert by_id["publish"]["error"] == "boom"
        assert by_id["publish"]["attempts"] == 3
        assert by_id["publish"]["status"] == "failed"

    def test_a_run_still_in_flight_reads_back(self, sakthai_home: Path) -> None:
        """The store saves at run start too, before end_time exists."""
        history = _run("in-flight")
        history.status = RunStatus.RUNNING
        history.end_time = None
        RunHistoryStore().save_run_history(history)

        run = api.workflows_payload(home=sakthai_home)["runs"][0]
        assert run["status"] == "running"
        assert run["finished_at"] is None
        assert run["duration_seconds"] is None

    def test_multiple_runs_are_ordered_newest_first(self, sakthai_home: Path) -> None:
        store = RunHistoryStore()
        early = _run("early")
        early.start_time = "2026-08-26T09:00:00"
        late = _run("late")
        late.start_time = "2026-08-26T11:00:00"
        store.save_run_history(early)
        store.save_run_history(late)

        ids = [r["run_id"] for r in api.workflows_payload(home=sakthai_home)["runs"]]
        assert ids == ["late", "early"]
