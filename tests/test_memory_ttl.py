"""Unit tests for memory TTL and --max-age filtering in FamilyMemoryView and MemoryStore."""

from __future__ import annotations

import shutil
import tempfile
import time
import unittest
from pathlib import Path

from sakthai.memory.merged import FamilyMemoryView
from sakthai.memory.store import MemoryStore


class TestMemoryTTL(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sakthai_ttl_test_"))
        self.saksee_db = self.temp_dir / "saksee.db"
        self.saksit_db = self.temp_dir / "saksit.db"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_facts_max_age_filters_stale_cache(self) -> None:
        now = time.time()
        with MemoryStore(self.saksee_db) as store:
            old_id = store.add_fact(
                value="Space status: degraded · retrieved_at=2026-11-26T12:00:00Z",
                tags=["monitoring-result", "space-1"],
            )
            # Artificially age the old fact to 3600s ago (1 hour)
            store._conn.execute(
                "UPDATE facts SET updated_at = ? WHERE id = ?", (now - 3600, old_id)
            )
            store._conn.commit()

            fresh_id = store.add_fact(
                value="Space status: running · retrieved_at=2026-11-26T12:55:00Z",
                tags=["monitoring-result", "space-1"],
            )
            # Set fresh fact to 60s ago
            store._conn.execute(
                "UPDATE facts SET updated_at = ? WHERE id = ?", (now - 60, fresh_id)
            )
            store._conn.commit()

        shard_paths = {"saksee": self.saksee_db, "saksit": self.saksit_db}
        with FamilyMemoryView(
            personas=["saksee"], shard_paths=shard_paths, include_unscoped=False
        ) as view:
            # Query without TTL -> returns both (most recent first)
            all_facts = view.find_facts(tags=["monitoring-result"])
            self.assertEqual(len(all_facts), 2)

            # Query with 30-min TTL (1800s) -> returns only the fresh fact
            fresh_facts = view.find_facts(tags=["monitoring-result"], max_age_seconds=1800)
            self.assertEqual(len(fresh_facts), 1)
            self.assertEqual(fresh_facts[0].fact.id, fresh_id)
            self.assertIn("running", fresh_facts[0].fact.value)

    def test_list_facts_and_top_observations_max_age(self) -> None:
        now = time.time()
        with MemoryStore(self.saksee_db) as store:
            f_id = store.add_fact(value="Stale fact", tags=["cache"])
            store._conn.execute("UPDATE facts SET updated_at = ? WHERE id = ?", (now - 5000, f_id))

            o_id = store.add_observation(summary="Stale observation", weight=0.9)
            store._conn.execute(
                "UPDATE observations SET created_at = ? WHERE id = ?", (now - 5000, o_id)
            )
            store._conn.commit()

        shard_paths = {"saksee": self.saksee_db}
        with FamilyMemoryView(
            personas=["saksee"], shard_paths=shard_paths, include_unscoped=False
        ) as view:
            facts = view.list_facts(max_age_seconds=1800)
            self.assertEqual(len(facts), 0)

            obs = view.top_observations(max_age_seconds=1800)
            self.assertEqual(len(obs), 0)

    def test_cli_memory_family_max_age_option(self) -> None:
        from click.testing import CliRunner

        from sakthai.cli.memory import memory_family

        runner = CliRunner()
        result = runner.invoke(memory_family, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--max-age", result.output)

    def test_search_and_store_direct_max_age(self) -> None:
        now = time.time()
        with MemoryStore(self.saksee_db) as store:
            f1 = store.add_fact(value="Fresh search term", tags=["tag1"])
            f2 = store.add_fact(value="Stale search term", tags=["tag1"])
            store._conn.execute("UPDATE facts SET updated_at = ? WHERE id = ?", (now - 5000, f2))

            o1 = store.add_observation(summary="Fresh search term obs")
            o2 = store.add_observation(summary="Stale search term obs")
            store._conn.execute(
                "UPDATE observations SET created_at = ? WHERE id = ?", (now - 5000, o2)
            )
            store._conn.commit()

            # Store level search_memory
            f_res, o_res = store.search_memory("search term", max_age_seconds=1800)
            self.assertEqual(len(f_res), 1)
            self.assertEqual(f_res[0].id, f1)
            self.assertEqual(len(o_res), 1)
            self.assertEqual(o_res[0].id, o1)

            # Store level search_by_tag
            tag_res = store.search_by_tag("tag1", max_age_seconds=1800)
            self.assertEqual(len(tag_res), 1)
            self.assertEqual(tag_res[0].id, f1)

        # View level search with query
        shard_paths = {"saksee": self.saksee_db}
        with FamilyMemoryView(
            personas=["saksee"], shard_paths=shard_paths, include_unscoped=False
        ) as view:
            f_view, o_view = view.search("search term", max_age_seconds=1800)
            self.assertEqual(len(f_view), 1)
            self.assertEqual(len(o_view), 1)

            # View level find_facts with query and tags
            found = view.find_facts(query="search term", tags=["tag1"], max_age_seconds=1800)
            self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
