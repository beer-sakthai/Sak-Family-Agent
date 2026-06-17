"""Integration tests for the click CLI (``sakthai ...``).

Every command is driven through ``CliRunner`` against the real command group.
An autouse fixture pins ``SAKTHAI_HOME`` to a tmp dir so memory/cycle/dashboard
commands never touch the developer's real ~/.sakthai. External effects (git,
the agent loop, the MCP serve loop) are monkeypatched — nothing here reaches the
network or spawns a subprocess.
"""

from __future__ import annotations

import json
import sys
import types
from collections.abc import Iterator
from pathlib import Path

import pytest
from click.testing import CliRunner

import sakthai.cli.agent as agent_mod
import sakthai.cli.skills as skills_mod
from sakthai.cli import main
from sakthai.config import memory_db_path
from sakthai.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def _isolated_home(sakthai_home: Path) -> Path:
    """Redirect SAKTHAI_HOME for every CLI test (memory.db lands in tmp)."""
    return sakthai_home


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _write_skill(root: Path, name: str, body: str = "Body.") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    md = skill_dir / "SKILL.md"
    md.write_text(
        f"---\nname: {name}\ndescription: a {name} skill\nversion: 1.0.0\n---\n\n{body}\n",
        encoding="utf-8",
    )
    return md


# -- top level -----------------------------------------------------------


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "sakthai" in result.output


def test_help_lists_commands(runner: CliRunner) -> None:
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    for cmd in ("learn", "recall", "memory", "run", "mcp", "cycle", "skills"):
        assert cmd in result.output


# -- learn / recall ------------------------------------------------------


def test_learn_persists_fact(runner: CliRunner) -> None:
    result = runner.invoke(main, ["learn", "the sky is blue"])
    assert result.exit_code == 0
    # Behaviour, not phrasing: the fact is actually in the store.
    with MemoryStore() as store:
        assert any("sky is blue" in f.value for f in store.list_facts())


def test_learn_requires_value_or_file(runner: CliRunner) -> None:
    result = runner.invoke(main, ["learn"])
    assert result.exit_code != 0
    assert "exactly one" in result.output


def test_learn_from_file(runner: CliRunner, tmp_path: Path) -> None:
    facts_file = tmp_path / "facts.md"
    facts_file.write_text(
        "# heading (ignored)\n- apple\n* banana\n1. cherry\nplain line\n\n",
        encoding="utf-8",
    )
    result = runner.invoke(main, ["learn", "--file", str(facts_file)])
    assert result.exit_code == 0
    # The 4 bullet/numbered/plain lines are learned; the heading is skipped.
    with MemoryStore() as store:
        values = {f.value for f in store.list_facts()}
    assert {"apple", "banana", "cherry", "plain line"} <= values
    assert "heading (ignored)" not in " ".join(values)


def test_recall_finds_match(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "espresso is strong"])
    result = runner.invoke(main, ["recall", "espresso"])
    assert result.exit_code == 0
    assert "espresso is strong" in result.output


def test_recall_no_match(runner: CliRunner) -> None:
    result = runner.invoke(main, ["recall", "nonexistent-token"])
    assert result.exit_code == 0
    assert "no matches found" in result.output


def test_recall_requires_query_or_tag(runner: CliRunner) -> None:
    result = runner.invoke(main, ["recall"])
    assert result.exit_code != 0
    assert "exactly one" in result.output


def test_recall_by_tag(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "ship it", "--tag", "work"])
    result = runner.invoke(main, ["recall", "--tag", "work"])
    assert result.exit_code == 0
    assert "ship it" in result.output


# -- memory subgroup -----------------------------------------------------


def test_memory_show_empty(runner: CliRunner) -> None:
    result = runner.invoke(main, ["memory", "show"])
    assert result.exit_code == 0
    assert "memory is empty" in result.output


def test_memory_show_lists_facts(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "fact one"])
    result = runner.invoke(main, ["memory", "show"])
    assert result.exit_code == 0
    assert "fact one" in result.output


def test_memory_stats_json(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "a fact"])
    result = runner.invoke(main, ["memory", "stats", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["facts"]["total"] == 1


def test_memory_forget(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "deletable"])
    with MemoryStore() as store:
        fact_id = store.list_facts()[0].id
    ok = runner.invoke(main, ["memory", "forget", str(fact_id)])
    assert ok.exit_code == 0
    # The fact is actually gone, not just reported gone.
    with MemoryStore() as store:
        assert all(f.id != fact_id for f in store.list_facts())
    missing = runner.invoke(main, ["memory", "forget", "99999"])
    assert missing.exit_code == 0
    assert "no fact with id 99999" in missing.output


def test_memory_backup(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "back me up"])
    result = runner.invoke(main, ["memory", "backup"])
    assert result.exit_code == 0
    assert "backup created:" in result.output


def test_memory_backup_no_db(runner: CliRunner, sakthai_home: Path) -> None:
    db = memory_db_path()
    if db.exists():
        db.unlink()
    result = runner.invoke(main, ["memory", "backup"])
    assert result.exit_code != 0
    assert "No memory database exists yet" in result.output


def test_memory_healthcheck(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "x"])
    result = runner.invoke(main, ["memory", "healthcheck"])
    assert result.exit_code == 0
    assert "integrity check:" in result.output


def test_memory_export_then_import(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["learn", "exported fact"])
    snap = tmp_path / "snap.json"
    exp = runner.invoke(main, ["memory", "export", str(snap)])
    assert exp.exit_code == 0
    assert snap.is_file()
    imp = runner.invoke(main, ["memory", "import", str(snap)])
    assert imp.exit_code == 0
    assert "imported" in imp.output


def test_memory_export_refuses_overwrite(runner: CliRunner, tmp_path: Path) -> None:
    snap = tmp_path / "exists.json"
    snap.write_text("{}", encoding="utf-8")
    result = runner.invoke(main, ["memory", "export", str(snap)])
    assert result.exit_code != 0
    assert "already exists" in result.output


def test_memory_deduplicate_none(runner: CliRunner) -> None:
    result = runner.invoke(main, ["memory", "deduplicate"])
    assert result.exit_code == 0
    assert "No duplicate facts found." in result.output


def test_memory_search_finds_match(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "espresso is delicious"])
    result = runner.invoke(main, ["memory", "search", "espresso"])
    assert result.exit_code == 0
    assert "espresso is delicious" in result.output


def test_memory_search_no_match(runner: CliRunner) -> None:
    result = runner.invoke(main, ["memory", "search", "xyzzy-no-match"])
    assert result.exit_code == 0
    assert "no matches found" in result.output


def test_memory_forget_obs(runner: CliRunner) -> None:
    from sakthai.memory.store import MemoryStore

    with MemoryStore() as store:
        obs_id = store.add_observation("temporary observation")
    result = runner.invoke(main, ["memory", "forget-obs", str(obs_id)])
    assert result.exit_code == 0
    assert "forgotten" in result.output


def test_memory_forget_obs_missing(runner: CliRunner) -> None:
    result = runner.invoke(main, ["memory", "forget-obs", "99999"])
    assert result.exit_code == 0
    assert "no observation with id 99999" in result.output


def test_memory_consolidate_no_old_facts(runner: CliRunner) -> None:
    runner.invoke(main, ["learn", "fresh fact"])
    result = runner.invoke(main, ["memory", "consolidate"])
    assert result.exit_code == 0
    assert "no older facts found" in result.output


def test_memory_consolidate_moves_old_facts(runner: CliRunner, sakthai_home: Path) -> None:
    from sakthai.memory.store import MemoryStore

    with MemoryStore() as store:
        store.add_fact("very old fact")
    result = runner.invoke(main, ["memory", "consolidate", "--age", "-1"])
    assert result.exit_code == 0
    assert "consolidated" in result.output
    assert "1" in result.output


def test_memory_export_csv_format(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["learn", "csv fact"])
    snap = tmp_path / "export.csv"
    result = runner.invoke(main, ["memory", "export", str(snap), "--format", "csv"])
    assert result.exit_code == 0
    assert snap.is_file()
    content = snap.read_text(encoding="utf-8")
    assert "csv fact" in content
    assert content.startswith("type,")


def test_memory_export_jsonl_format(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["learn", "jsonl fact"])
    snap = tmp_path / "export.jsonl"
    result = runner.invoke(main, ["memory", "export", str(snap), "--format", "jsonl"])
    assert result.exit_code == 0
    assert snap.is_file()
    content = snap.read_text(encoding="utf-8")
    assert "jsonl fact" in content
    import json as _json

    for line in content.splitlines():
        if line.strip():
            _json.loads(line)  # every line must be valid JSON


def test_memory_export_force_overwrites(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["learn", "some fact"])
    snap = tmp_path / "existing.json"
    snap.write_text("{}", encoding="utf-8")
    result = runner.invoke(main, ["memory", "export", str(snap), "--force"])
    assert result.exit_code == 0
    assert snap.is_file()
    import json as _json

    data = _json.loads(snap.read_text(encoding="utf-8"))
    assert "facts" in data


def test_memory_import_replace_mode(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["learn", "original fact"])
    snap = tmp_path / "snap.json"
    runner.invoke(main, ["memory", "export", str(snap)])
    runner.invoke(main, ["learn", "extra fact that will be wiped"])
    result = runner.invoke(main, ["memory", "import", str(snap), "--replace", "--yes"])
    assert result.exit_code == 0
    assert "replace" in result.output


def test_memory_import_invalid_json(runner: CliRunner, tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    result = runner.invoke(main, ["memory", "import", str(bad)])
    assert result.exit_code != 0
    assert "could not read snapshot" in result.output


def test_memory_sync_git(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.memory.sync as sync_mod

    monkeypatch.setattr(
        sync_mod, "sync_memory_to_git", lambda remote=None: "Synced locally to Git repository."
    )
    result = runner.invoke(main, ["memory", "sync"])
    assert result.exit_code == 0
    assert "Synced" in result.output


def test_memory_sync_http(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.memory.sync as sync_mod

    monkeypatch.setattr(
        sync_mod,
        "sync_memory_via_http",
        lambda url, api_key=None: f"Synced to HTTP endpoint: {url}",
    )
    result = runner.invoke(main, ["memory", "sync", "--http-url", "http://example.com/sync"])
    assert result.exit_code == 0
    assert "example.com" in result.output


def test_memory_sync_failure_exits_nonzero(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.memory.sync as sync_mod

    monkeypatch.setattr(
        sync_mod,
        "sync_memory_to_git",
        lambda remote=None: (_ for _ in ()).throw(RuntimeError("push failed")),
    )
    result = runner.invoke(main, ["memory", "sync"])
    assert result.exit_code != 0
    assert "push failed" in result.output


# -- system commands -----------------------------------------------------


@pytest.mark.parametrize(
    ("args", "needle"),
    [
        (["doctor"], "SakThai Doctor"),
        (["setup"], "Setup Check"),
        (["status"], "SakThai Status"),
        (["tools"], "learn"),
    ],
)
def test_system_commands_run(runner: CliRunner, args: list[str], needle: str) -> None:
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert needle in result.output


# -- cycle ---------------------------------------------------------------


def test_cycle_status_defaults_to_dream(runner: CliRunner) -> None:
    result = runner.invoke(main, ["cycle", "status"])
    assert result.exit_code == 0
    assert "DREAM" in result.output
    assert "1/6" in result.output


def test_cycle_next_advances(runner: CliRunner) -> None:
    result = runner.invoke(main, ["cycle", "next"])
    assert result.exit_code == 0
    assert "HOPE" in result.output


def test_cycle_set_valid(runner: CliRunner) -> None:
    result = runner.invoke(main, ["cycle", "set", "trust"])
    assert result.exit_code == 0
    # State persists across invocations: a fresh status reports the new stage.
    status = runner.invoke(main, ["cycle", "status"])
    assert "TRUST" in status.output


def test_cycle_set_invalid(runner: CliRunner) -> None:
    result = runner.invoke(main, ["cycle", "set", "bogus"])
    assert result.exit_code != 0
    assert "Unknown stage" in result.output


def test_cycle_list_marks_current(runner: CliRunner) -> None:
    runner.invoke(main, ["cycle", "set", "care"])
    result = runner.invoke(main, ["cycle", "list"])
    assert result.exit_code == 0
    assert "▶" in result.output
    assert "CARE" in result.output


# -- skills (roots redirected to tmp) ------------------------------------


@pytest.fixture
def skill_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Path, Path]]:
    skills_root = tmp_path / "skills"
    library_root = tmp_path / "library"
    skills_root.mkdir()
    library_root.mkdir()
    monkeypatch.setattr(skills_mod, "SKILLS_DIR", skills_root)
    monkeypatch.setattr(skills_mod, "LIBRARY_DIR", library_root)
    yield skills_root, library_root


def test_skills_list(runner: CliRunner, skill_roots: tuple[Path, Path]) -> None:
    _write_skill(skill_roots[0], "alpha")
    result = runner.invoke(main, ["skills", "list"])
    assert result.exit_code == 0
    assert "alpha" in result.output


def test_skills_show(runner: CliRunner, skill_roots: tuple[Path, Path]) -> None:
    _write_skill(skill_roots[0], "alpha")
    result = runner.invoke(main, ["skills", "show", "alpha"])
    assert result.exit_code == 0
    # Don't couple to column spacing — just that the field and value are present.
    assert "name:" in result.output
    assert "alpha" in result.output


def test_skills_show_missing(runner: CliRunner, skill_roots: tuple[Path, Path]) -> None:
    result = runner.invoke(main, ["skills", "show", "ghost"])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_skills_validate_ok(runner: CliRunner, skill_roots: tuple[Path, Path]) -> None:
    _write_skill(skill_roots[0], "alpha")
    result = runner.invoke(main, ["skills", "validate"])
    assert result.exit_code == 0
    assert "validated" in result.output


def test_skills_validate_flags_errors(runner: CliRunner, skill_roots: tuple[Path, Path]) -> None:
    (skill_roots[0] / "broken").mkdir()  # dir with no SKILL.md
    result = runner.invoke(main, ["skills", "validate"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_skills_create(runner: CliRunner, skill_roots: tuple[Path, Path]) -> None:
    result = runner.invoke(main, ["skills", "create", "My Skill"])
    assert result.exit_code == 0
    created = skill_roots[0] / "my-skill" / "SKILL.md"
    assert created.is_file()
    again = runner.invoke(main, ["skills", "create", "My Skill"])
    assert again.exit_code != 0
    assert "already exists" in again.output


# -- extensions (git monkeypatched) --------------------------------------


def _fake_clone(cmd: list[str], *args: object, **kwargs: object) -> object:
    dest = Path(cmd[-1])
    skill = dest / "ext-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: ext-skill\n---\n", encoding="utf-8")
    return types.SimpleNamespace(returncode=0, stdout="", stderr="")


def test_extensions_list_empty(runner: CliRunner) -> None:
    result = runner.invoke(main, ["extensions", "list"])
    assert result.exit_code == 0
    assert "no extensions installed" in result.output


def test_extensions_install_and_remove(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.extensions.install as ext_mod

    monkeypatch.setattr(ext_mod.subprocess, "run", _fake_clone)
    inst = runner.invoke(main, ["extensions", "install", "https://github.com/foo/bar"])
    assert inst.exit_code == 0
    assert "installed: bar" in inst.output

    rm = runner.invoke(main, ["extensions", "remove", "bar"])
    assert rm.exit_code == 0
    assert "removed: bar" in rm.output


def test_extensions_remove_unknown(runner: CliRunner) -> None:
    result = runner.invoke(main, ["extensions", "remove", "nope"])
    assert result.exit_code != 0
    assert "no extension named 'nope'" in result.output


# -- agent run / mcp (loop monkeypatched) --------------------------------


def test_run_echoes_agent_text(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_agent(task: str, **kwargs: object) -> object:
        return types.SimpleNamespace(text=f"answered: {task}")

    monkeypatch.setattr(agent_mod, "run_agent", fake_run_agent)
    result = runner.invoke(main, ["run", "hello there"])
    assert result.exit_code == 0
    assert "answered: hello there" in result.output


def test_run_reports_agent_error(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(task: str, **kwargs: object) -> object:
        raise agent_mod.AgentError("no credentials")

    monkeypatch.setattr(agent_mod, "run_agent", boom)
    result = runner.invoke(main, ["run", "hi"])
    assert result.exit_code != 0
    assert "no credentials" in result.output


def test_mcp_invokes_serve(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.mcp as mcp_pkg

    called = {"n": 0}

    def fake_serve() -> None:
        called["n"] += 1

    monkeypatch.setattr(mcp_pkg, "serve", fake_serve)
    result = runner.invoke(main, ["mcp"])
    assert result.exit_code == 0
    assert called["n"] == 1


def _capture_tools(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    def fake_run_agent(task: str, **kwargs: object) -> object:
        captured["tools"] = kwargs.get("tools")
        return types.SimpleNamespace(text="ok")

    monkeypatch.setattr(agent_mod, "run_agent", fake_run_agent)
    return captured


def test_run_autoloads_configured_mcp_tools(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, tmp_path: Path
) -> None:
    server_home = tmp_path / "srv"
    (sakthai_home / "mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "sk": {
                        "command": sys.executable,
                        "args": ["-m", "sakthai.mcp"],
                        "env": {"SAKTHAI_HOME": str(server_home)},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    captured = _capture_tools(monkeypatch)
    result = runner.invoke(main, ["run", "hi"])
    assert result.exit_code == 0
    names = {t.name for t in captured["tools"]}  # type: ignore[union-attr]
    assert any(n.startswith("sk__") for n in names)  # external tools merged in
    assert "learn" in names  # built-ins still present


def test_run_no_mcp_skips_external_servers(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, sakthai_home: Path
) -> None:
    # A configured (here, deliberately broken) server must be ignored with --no-mcp.
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"sk": {"command": "sakthai-no-such-binary"}}}), encoding="utf-8"
    )
    captured = _capture_tools(monkeypatch)
    result = runner.invoke(main, ["run", "hi", "--no-mcp"])
    assert result.exit_code == 0
    names = {t.name for t in captured["tools"]}  # type: ignore[union-attr]
    assert not any(n.startswith("sk__") for n in names)
    assert "learn" in names


# -- dashboard -----------------------------------------------------------


def test_dashboard_export(runner: CliRunner, tmp_path: Path) -> None:
    runner.invoke(main, ["learn", "dashboard fact"])
    out = tmp_path / "data.json"
    result = runner.invoke(main, ["dashboard", "--export", str(out)])
    assert result.exit_code == 0
    assert "snapshot:" in result.output
    assert out.is_file()
    json.loads(out.read_text(encoding="utf-8"))  # valid JSON


def test_dashboard_rejects_bad_port(runner: CliRunner) -> None:
    result = runner.invoke(main, ["dashboard", "--port", "10"])
    assert result.exit_code != 0
    assert "not a valid port" in result.output


def test_run_dry_run_reports_and_exits_zero(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "anthropic_credential_source", lambda: "api_key")
    result = runner.invoke(main, ["run", "hi", "--dry-run", "--no-mcp", "-p", "anthropic"])
    assert result.exit_code == 0, result.output
    assert "[dry-run]" in result.output
    assert "anthropic" in result.output
    assert "runnable:    yes" in result.output


def test_run_dry_run_not_runnable_exits_nonzero(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "anthropic_credential_source", lambda: None)
    result = runner.invoke(main, ["run", "hi", "--dry-run", "--no-mcp", "-p", "anthropic"])
    assert result.exit_code != 0
    assert "runnable:    no" in result.output


def test_run_stream_prints_streamed_tokens(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sakthai.agent.loop import AgentResult

    def fake_run_agent(task: str, *, on_token=None, **_kw: object) -> AgentResult:
        if on_token is not None:
            on_token("Hel")
            on_token("lo")
        return AgentResult(text="Hello", iterations=1, stop_reason="end_turn")

    monkeypatch.setattr(agent_mod, "run_agent", fake_run_agent)
    result = runner.invoke(main, ["run", "hi", "--stream", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert "Hello" in result.output


def test_run_without_stream_prints_final_text(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sakthai.agent.loop import AgentResult

    def fake_run_agent(task: str, *, on_token=None, **_kw: object) -> AgentResult:
        assert on_token is None
        return AgentResult(text="final-answer", iterations=1, stop_reason="end_turn")

    monkeypatch.setattr(agent_mod, "run_agent", fake_run_agent)
    result = runner.invoke(main, ["run", "hi", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert "final-answer" in result.output
