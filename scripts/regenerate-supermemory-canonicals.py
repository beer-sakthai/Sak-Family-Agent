"""Regenerate supermemory canonicals — pairwise near-dedup of memory entries.

Compares every pair of facts (and every pair of observations) for string
similarity, groups near-duplicates above a configurable threshold using
Union-Find, and selects one "canonical" entry per group:

  * facts:        most recently updated entry wins
  * observations: highest weight, then confidence, then most recent

All other entries in each group are removed (or just reported in --dry-run).

The default threshold (0.85) is intentionally conservative.  Lower it to
catch broader near-matches; raise it toward 1.0 to restrict to near-identical
text.

Usage
-----
    python scripts/regenerate-supermemory-canonicals.py            # dry-run
    python scripts/regenerate-supermemory-canonicals.py --apply    # commit changes
    python scripts/regenerate-supermemory-canonicals.py --threshold 0.9 --apply
    python scripts/regenerate-supermemory-canonicals.py --help
"""

from __future__ import annotations

import argparse
import sys
from difflib import SequenceMatcher
from pathlib import Path

# Allow running from the repo root without pip-installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sakthai.memory.store import Fact, MemoryStore, Observation  # noqa: E402


# ---------------------------------------------------------------------------
# Similarity helpers
# ---------------------------------------------------------------------------

def _similarity(a: str, b: str) -> float:
    """Return SequenceMatcher similarity ratio in [0, 1] (case-insensitive)."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _fact_text(f: Fact) -> str:
    """Canonical text representation of a fact used for similarity comparison."""
    parts = [f.kind, f.key or "", f.value]
    return " ".join(p for p in parts if p)


def _obs_text(o: Observation) -> str:
    return o.summary


# ---------------------------------------------------------------------------
# Union-Find grouping
# ---------------------------------------------------------------------------

def _find_groups(items, text_fn, threshold: float) -> list[list[int]]:
    """Return index-groups of near-duplicates using Union-Find.

    Each group contains at least two indices into *items*.  Items below the
    threshold with every other item appear in their own singleton group and
    are excluded from the returned list.
    """
    n = len(items)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        parent[find(x)] = find(y)

    texts = [text_fn(item) for item in items]
    for i in range(n):
        for j in range(i + 1, n):
            if _similarity(texts[i], texts[j]) >= threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    return [g for g in groups.values() if len(g) > 1]


# ---------------------------------------------------------------------------
# Canonical selection
# ---------------------------------------------------------------------------

def _canonical_fact(group: list[Fact]) -> Fact:
    """Most recently updated fact wins; tie-break by highest id."""
    return max(group, key=lambda f: (f.updated_at, f.id))


def _canonical_obs(group: list[Observation]) -> Observation:
    """Highest weight → confidence → newest → highest id."""
    return max(group, key=lambda o: (o.weight, o.confidence, o.created_at, o.id))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        metavar="RATIO",
        help="Similarity ratio [0–1] above which two entries are near-duplicates (default: 0.85).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Delete non-canonical duplicates. Without this flag the script only reports.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress per-group detail; print only the summary line.",
    )
    args = parser.parse_args()

    dry_run = not args.apply

    print(
        f"regenerate-supermemory-canonicals  "
        f"threshold={args.threshold}  "
        f"mode={'dry-run' if dry_run else 'APPLY'}"
    )
    print()

    with MemoryStore() as store:
        facts = store.list_facts(limit=100_000)
        observations = store.top_observations(limit=100_000)

        # ---- Facts --------------------------------------------------------
        fact_groups = _find_groups(facts, _fact_text, args.threshold)
        fact_ids_to_delete: list[int] = []

        for group_indices in fact_groups:
            group = [facts[i] for i in group_indices]
            canon = _canonical_fact(group)
            dupes = [f for f in group if f.id != canon.id]
            fact_ids_to_delete.extend(f.id for f in dupes)

            if not args.quiet:
                canon_text = _fact_text(canon)
                print(f"  [FACT] canonical id={canon.id} [{canon.kind}]  {canon_text[:70]!r}")
                for f in dupes:
                    verb = "would remove" if dry_run else "removing"
                    print(f"         {verb}  id={f.id} [{f.kind}]  {_fact_text(f)[:70]!r}")
                print()

        if not fact_groups:
            print("  No near-duplicate facts found.")
            print()

        # ---- Observations -------------------------------------------------
        obs_groups = _find_groups(observations, _obs_text, args.threshold)
        obs_ids_to_delete: list[int] = []

        for group_indices in obs_groups:
            group = [observations[i] for i in group_indices]
            canon = _canonical_obs(group)
            dupes = [o for o in group if o.id != canon.id]
            obs_ids_to_delete.extend(o.id for o in dupes)

            if not args.quiet:
                print(
                    f"  [OBS]  canonical id={canon.id}  "
                    f"w={canon.weight}  {canon.summary[:70]!r}"
                )
                for o in dupes:
                    verb = "would remove" if dry_run else "removing"
                    print(
                        f"         {verb}  id={o.id}  "
                        f"w={o.weight}  {o.summary[:70]!r}"
                    )
                print()

        if not obs_groups:
            print("  No near-duplicate observations found.")
            print()

        # ---- Apply --------------------------------------------------------
        if not dry_run:
            for fid in fact_ids_to_delete:
                store.forget_fact(fid)
            for oid in obs_ids_to_delete:
                store.forget_observation(oid)

    total_f = len(fact_ids_to_delete)
    total_o = len(obs_ids_to_delete)
    action = "would remove" if dry_run else "removed"
    print(f"Summary: {action} {total_f} fact(s) and {total_o} observation(s).")
    if dry_run and (total_f or total_o):
        print("Re-run with --apply to commit the deletions.")


if __name__ == "__main__":
    main()
