"""Memory commands: ``learn``, ``recall``, and the ``memory`` subgroup."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import click

from ..learn.capture import learn as learn_fact
from ..memory.backup import backup_memory
from ..memory.store import Fact, MemoryStore, Observation, snapshot_to_csv, snapshot_to_jsonl


def _fact_line(f: Fact) -> str:
    head = f"[{f.kind}] {f.key}: " if f.key else f"[{f.kind}] "
    tags = f"  #{' #'.join(f.tags)}" if getattr(f, "tags", None) else ""
    return f"  {f.id:>4}  {head}{f.value}{tags}"


def _obs_line(o: Observation) -> str:
    return f"  {o.id:>4}  ({o.weight:.2f}) {o.summary}"


@click.command()
@click.argument("value", required=False)
@click.option("--kind", default="note", show_default=True, help="Fact category.")
@click.option("--key", default=None, help="Optional key/name for the fact.")
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Attach a tag (repeatable, e.g. --tag work --tag urgent).",
)
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Read facts from a text/markdown file (one per line/bullet).",
)
def learn(
    value: str | None,
    kind: str,
    key: str | None,
    tags: tuple[str, ...],
    file: Path | None,
) -> None:
    """Add a fact (or a file of facts) to persistent memory."""
    if bool(value) == bool(file):
        raise click.UsageError("Provide exactly one of VALUE or --file / -f.")
    tag_list = list(tags) or None

    if file is None:
        fact_id = learn_fact(cast(str, value), kind=kind, key=key, tags=tag_list)
        click.echo(f"learned (id={fact_id})")
        return

    learned: list[int] = []
    with MemoryStore() as store:
        for raw in file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("- ", "* ", "+ ")):
                line = line[2:].strip()
            elif (
                "." in line
                and line.split(".", 1)[0].isdigit()
                and line.split(".", 1)[1].startswith(" ")
            ):
                line = line.split(".", 1)[1].strip()
            if line:
                learned.append(store.add_fact(line, kind=kind, key=key, tags=tag_list))
    if not learned:
        click.echo("No valid facts found in file.")
        return
    click.echo(f"learned {len(learned)} facts (ids: {learned})")


@click.command()
@click.argument("query", required=False)
@click.option("--tag", "tag", default=None, help="Recall facts carrying this exact tag.")
@click.option("--limit", default=20, show_default=True, help="Max results to display.")
def recall(query: str | None, tag: str | None, limit: int) -> None:
    """Recall facts (and observations) matching QUERY, or filter by --tag."""
    if bool(query) == bool(tag):
        raise click.UsageError("Provide exactly one of QUERY or --tag.")
    with MemoryStore() as store:
        if tag:
            facts = store.search_by_tag(tag, limit=limit)
            obs: list[Observation] = []
        else:
            facts, obs = store.search_memory(cast(str, query), limit=limit)
    if not facts and not obs:
        click.echo(f"no matches found for {f'tag {tag!r}' if tag else repr(query)}")
        return
    if facts:
        click.echo(f"# Facts ({len(facts)})")
        for f in facts:
            click.echo(_fact_line(f))
    if obs:
        click.echo(f"# Observations ({len(obs)})")
        for o in obs:
            click.echo(_obs_line(o))


@click.group()
def memory() -> None:
    """Inspect and manage persistent memory."""


@memory.command("show")
@click.option("--limit", default=50, show_default=True)
def memory_show(limit: int) -> None:
    """List recent facts and top observations."""
    with MemoryStore() as store:
        facts = store.list_facts(limit=limit)
        obs = store.top_observations(limit=limit)
    if not facts and not obs:
        click.echo('(memory is empty — try `sakthai learn "..."`)')
        return
    if facts:
        click.echo("# Facts")
        for f in facts:
            click.echo(_fact_line(f))
    if obs:
        click.echo("# Observations")
        for o in obs:
            click.echo(_obs_line(o))


@memory.command("stats")
@click.option("--json", "as_json", is_flag=True, help="Emit the raw stats as JSON.")
def memory_stats(as_json: bool) -> None:
    """Show aggregate counts and distributions over memory."""
    with MemoryStore() as store:
        data = store.stats()
    if as_json:
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    def _ts(value: int | None) -> str:
        return datetime.fromtimestamp(value, tz=UTC).strftime("%Y-%m-%d") if value else "—"

    facts, obs = data["facts"], data["observations"]
    click.echo("# Memory stats")
    click.echo(f"  db: {data['db_path']}")
    click.echo(f"  facts: {facts['total']}  ({_ts(facts['oldest'])} → {_ts(facts['newest'])})")
    if facts["by_kind"]:
        click.echo("  by kind:")
        for kind, n in facts["by_kind"].items():
            click.echo(f"    {n:>4}  {kind}")
    if data["tags"]:
        click.echo("  tags:")
        for tag, n in data["tags"].items():
            click.echo(f"    {n:>4}  #{tag}")
    click.echo(f"  observations: {obs['total']}  ({_ts(obs['oldest'])} → {_ts(obs['newest'])})")
    if obs["total"]:
        click.echo(f"    avg weight: {obs['avg_weight']}  avg confidence: {obs['avg_confidence']}")


@memory.command("search")
@click.argument("query")
@click.option("--limit", default=50, show_default=True, help="Max results per section.")
def memory_search(query: str, limit: int) -> None:
    """Search facts and observations for QUERY."""
    with MemoryStore() as store:
        facts, obs = store.search_memory(query, limit=limit)
    if not facts and not obs:
        click.echo(f"no matches found for '{query}'")
        return
    if facts:
        click.echo(f"# Matching Facts ({len(facts)})")
        for f in facts:
            click.echo(_fact_line(f))
    if obs:
        click.echo(f"# Matching Observations ({len(obs)})")
        for o in obs:
            click.echo(_obs_line(o))


@memory.command("forget")
@click.argument("fact_id", type=int)
def memory_forget(fact_id: int) -> None:
    """Delete a fact by id."""
    with MemoryStore() as store:
        ok = store.forget_fact(fact_id)
    click.echo("forgotten" if ok else f"no fact with id {fact_id}")


@memory.command("forget-obs")
@click.argument("obs_id", type=int)
def memory_forget_obs(obs_id: int) -> None:
    """Delete an observation by id."""
    with MemoryStore() as store:
        ok = store.forget_observation(obs_id)
    click.echo("forgotten" if ok else f"no observation with id {obs_id}")


@memory.command("backup")
def memory_backup() -> None:
    """Write a timestamped backup of the memory database."""
    try:
        dest = backup_memory()
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"backup created: {dest}")


@memory.command("healthcheck")
def memory_healthcheck() -> None:
    """Run a SQLite integrity check."""
    with MemoryStore() as store:
        click.echo(f"integrity check: {store.healthcheck()}")


@memory.command("export")
@click.argument("path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--force", is_flag=True, help="Overwrite PATH if it already exists.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "csv", "jsonl"]),
    default="json",
    show_default=True,
    help="json restores via `memory import`; csv/jsonl are flat exports.",
)
def memory_export(path: Path, force: bool, fmt: str) -> None:
    """Write a snapshot of facts + observations to PATH."""
    if path.exists() and not force:
        raise click.ClickException(f"{path} already exists. Pass --force to overwrite.")
    with MemoryStore() as store:
        snapshot = store.export_to_dict()
    if fmt == "csv":
        payload = snapshot_to_csv(snapshot)
    elif fmt == "jsonl":
        payload = snapshot_to_jsonl(snapshot)
    else:
        payload = json.dumps(snapshot, indent=2, ensure_ascii=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    click.echo(
        f"exported {len(snapshot['facts'])} facts, "
        f"{len(snapshot['observations'])} observations -> {path} ({fmt})"
    )


@memory.command("import")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--replace", is_flag=True, help="Wipe memory first (preserves snapshot IDs).")
@click.option("--yes", is_flag=True, help="Skip the --replace confirmation prompt.")
def memory_import(path: Path, replace: bool, yes: bool) -> None:
    """Restore facts + observations from a JSON snapshot at PATH."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise click.ClickException(f"could not read snapshot: {exc}") from exc
    if replace and not yes:
        click.confirm(
            "--replace will delete all existing facts and observations. Continue?",
            abort=True,
        )
    mode = "replace" if replace else "merge"
    try:
        with MemoryStore() as store:
            n_facts, n_obs = store.import_from_dict(data, mode=mode)
    except ValueError as exc:
        raise click.ClickException(f"invalid snapshot: {exc}") from exc
    click.echo(f"imported {n_facts} facts, {n_obs} observations ({mode} mode)")


@memory.command("consolidate")
@click.option(
    "--age", default=86400, show_default=True, type=int, help="Fold facts older than AGE seconds."
)
def memory_consolidate(age: int) -> None:
    """Fold older facts into a single observation."""
    with MemoryStore() as store:
        n = store.consolidate_facts(age_seconds=age)
    click.echo(
        f"consolidated {n} older fact(s) into a new observation"
        if n
        else "no older facts found to consolidate"
    )


_CONSOLIDATE_PROMPT = (
    "You are a memory-extraction tool. Below is a trace of one session between a user and "
    "their personal agent. Pull out any new, concrete, durable facts about the *user* worth "
    "remembering long-term (preferences, habits, environment, identity, recurring goals).\n\n"
    "Rules:\n"
    "- Only facts about the human user, not the agent or the task mechanics.\n"
    "- One fact per line, concise and declarative (e.g. 'User prefers dark mode', "
    "'User timezone is GMT+7').\n"
    "- No preamble, bullets, numbering, or commentary.\n"
    "- If there is nothing worth keeping, output exactly: None\n\n"
    "Session trace:\n{trace}"
)


@memory.command("consolidate-sessions")
@click.option("--limit", default=10, show_default=True, type=int, help="Max sessions to process.")
@click.option("--model", default=None, help="Model override for the extraction LLM.")
def memory_consolidate_sessions(limit: int, model: str | None) -> None:
    """Mine local session logs for durable facts and learn them.

    Reads agent session logs from ``sessions_dir()``, asks an LLM to extract
    long-term facts about the user, and stores each as a ``consolidated`` fact.
    Already-processed logs are tracked so re-runs are idempotent.
    """
    from ..agent.loop import DEFAULT_MODEL, run_agent
    from ..config import sakthai_home, sessions_dir

    s_dir = sessions_dir()
    logs = sorted(s_dir.glob("*.json")) if s_dir.is_dir() else []
    if not logs:
        click.echo("No local session logs found.")
        return

    state_file = sakthai_home() / "consolidated_sessions.json"
    processed: set[str] = set()
    if state_file.exists():
        try:
            processed = set(json.loads(state_file.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            processed = set()

    pending = [f for f in logs if f.name not in processed][:limit]
    if not pending:
        click.echo("All local sessions have already been consolidated.")
        return

    click.echo(f"Consolidating {len(pending)} session(s)...")
    extraction_model = model or DEFAULT_MODEL
    learned = 0

    for f in pending:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            click.echo(f"Skipping unreadable session log {f.name}: {exc}")
            continue

        task = data.get("task", "")
        result_text = (data.get("result") or {}).get("text", "")
        trace = f"User: {task}\nAgent: {result_text}"

        try:
            res = run_agent(
                _CONSOLIDATE_PROMPT.format(trace=trace),
                model=extraction_model,
                max_iterations=1,
                tools=(),
            )
        except Exception as exc:  # noqa: BLE001 - report and continue, never abort the batch
            click.echo(f"Error extracting from {f.name}: {exc}")
            continue

        for raw in res.text.strip().splitlines():
            line = raw.strip().lstrip("-*+ ").strip()
            if not line or line.lower() == "none" or line.startswith("#"):
                continue
            learn_fact(line, kind="consolidated", tags=["consolidated"])
            learned += 1

        processed.add(f.name)

    try:
        state_file.write_text(json.dumps(sorted(processed), indent=2), encoding="utf-8")
    except OSError as exc:
        click.echo(f"Warning: could not save consolidation state: {exc}")

    click.secho(
        f"consolidated {len(pending)} session(s), learned {learned} new fact(s)",
        fg="green",
        bold=True,
    )


@memory.command("deduplicate")
@click.option("--dry-run", "-n", is_flag=True, help="Report duplicates without deleting.")
@click.option("--verbose", "-v", is_flag=True, help="Print every pruned row.")
def memory_deduplicate(dry_run: bool, verbose: bool) -> None:
    """Find and remove duplicate facts and observations."""
    from ..memory.store import Fact, Observation

    with MemoryStore() as store:
        facts = cast(list[Fact], store.deduplicate_facts(detailed=True, dry_run=dry_run))
        obs = cast(
            list[Observation], store.deduplicate_observations(detailed=True, dry_run=dry_run)
        )

    verb = "Found" if dry_run else "Removed"
    if facts:
        click.echo(f"{verb} {len(facts)} duplicate fact(s)")
        if verbose:
            for f in sorted(facts, key=lambda x: (x.kind, x.key or "", x.id)):
                click.echo(f"  - id {f.id} [{f.kind}] ({f.key or 'no-key'}): {f.value}")
    else:
        click.echo("No duplicate facts found.")
    if obs:
        click.echo(f"{verb} {len(obs)} duplicate observation(s)")
        if verbose:
            for o in sorted(obs, key=lambda x: (x.summary, x.id)):
                click.echo(f"  - id {o.id} ({o.summary[:60]}) [w={o.weight}, c={o.confidence}]")
    else:
        click.echo("No duplicate observations found.")


@memory.command("sync")
@click.option("--remote", default=None, help="Git remote URL to push the snapshot to.")
@click.option("--http-url", default=None, help="HTTP URL to POST the snapshot to (fallback mode).")
@click.option("--http-key", default=None, help="Bearer token for HTTP authentication.")
@click.option(
    "--supermemory",
    is_flag=True,
    help="Regenerate supermemory canonicals (near-dedup) before syncing.",
)
def memory_sync(
    remote: str | None, http_url: str | None, http_key: str | None, supermemory: bool
) -> None:
    """Synchronize memory to a remote Git repository or HTTP endpoint."""
    from ..memory.sync import sync_memory_to_git, sync_memory_via_http

    try:
        if supermemory:
            click.echo("Running supermemory canonical regeneration...")
            import subprocess
            import sys

            from ..config import REPO_ROOT

            script = REPO_ROOT / "scripts" / "regenerate-supermemory-canonicals.py"
            subprocess.run([sys.executable, str(script), "--apply", "--quiet"], check=True)
            click.echo("Supermemory deduplication complete.")

        click.echo("Syncing memory...")
        if http_url:
            result = sync_memory_via_http(http_url, api_key=http_key)
        else:
            result = sync_memory_to_git(remote)
        click.echo(result)
    except Exception as exc:
        raise click.ClickException(f"Sync failed: {exc}") from exc
