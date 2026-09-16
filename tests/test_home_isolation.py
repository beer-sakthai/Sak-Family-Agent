"""Guard tests: the suite must not touch the invoking user's real home.

Finding 1 of docs/test-coverage-audit-2026-08-31.md (severity: high) was that
`tests/test_agent_coordinator.py` created `~/.sakthai/sakking/memory.db` and
`~/.sakthai/saksee/memory.db` — the paths a deployed persona uses on the VM,
per `infra/vm-agents/sakthai-agent-run.sh`. The `_isolate_home` autouse fixture
in `conftest.py` closes that; these tests keep it closed.
"""

from __future__ import annotations

from pathlib import Path

from sakthai import config


def test_home_points_inside_the_sandbox(real_sakthai_home: Path) -> None:
    """`Path.home()` resolves under tmp_path, not the invoking user's home."""
    home = Path.home()
    assert "sakthai-test-home-" in str(home), f"HOME was not redirected: {home}"
    assert not home.is_relative_to(real_sakthai_home.parent)


def test_persona_shard_paths_resolve_inside_the_sandbox(real_sakthai_home: Path) -> None:
    """The path that escaped `SAKTHAI_HOME` now lands in the sandbox too.

    `persona_memory_db_path()` resolves from `Path.home()` on purpose,
    independent of `SAKTHAI_HOME` — which is exactly why setting only
    `SAKTHAI_HOME` could not contain it.
    """
    for persona in ("sakking", "saksee"):
        shard = config.persona_memory_db_path(persona)
        assert not shard.is_relative_to(real_sakthai_home), (
            f"{persona} shard resolves to the real home: {shard}"
        )
        assert "sakthai-test-home-" in str(shard), f"{persona} shard escaped the sandbox: {shard}"


def test_real_sakthai_home_has_no_persona_shards_from_this_run(
    real_sakthai_home: Path,
) -> None:
    """Nothing in this run created a persona shard under the real `~/.sakthai`.

    Scoped to the persona shard paths rather than the whole directory: a
    developer's own `~/.sakthai/memory.db` may legitimately predate the run,
    and asserting on that would fail for a reason the suite did not cause.
    """
    if not real_sakthai_home.exists():
        return
    for persona in config.PERSONA_NAMES:
        shard = real_sakthai_home / persona / "memory.db"
        assert not shard.exists(), (
            f"the suite created a real persona shard at {shard}; "
            "something bypassed the _isolate_home fixture"
        )
