"""Evolution Checkpoint and Lineage Registry with Rollback."""

from __future__ import annotations

import os
import sqlite3
import threading
import uuid
from pathlib import Path

from sakthai.evolution.models import (
    EvolutionCheckpoint,
    EvolutionVariant,
    MutationScore,
)


class EvolutionRegistry:
    """Stores prompt mutations and manages versioned persona checkpoints with rollback."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_env = os.getenv("SAKTHAI_EVOLUTION_DB")
            self.db_path = (
                Path(db_env) if db_env else Path.home() / ".sakthai" / "evolution.sqlite3"
            )
        elif str(db_path) == ":memory:":
            self.db_path = Path(":memory:")
        else:
            self.db_path = Path(db_path)

        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._shared_conn: sqlite3.Connection | None = None
        if str(self.db_path) == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False, timeout=30.0)
            self._shared_conn.row_factory = sqlite3.Row

        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS evolution_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    active_prompt TEXT NOT NULL,
                    composite_score REAL NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evolution_variants (
                    variant_id TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    parent_checkpoint_id TEXT NOT NULL,
                    prompt_diff TEXT NOT NULL,
                    mutated_prompt TEXT NOT NULL,
                    mutation_rationale TEXT NOT NULL,
                    accuracy_score REAL,
                    tool_discipline_score REAL,
                    conciseness_score REAL,
                    composite_score REAL,
                    passed_safety_gate INTEGER,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_evo_persona ON evolution_checkpoints(persona, is_active);
                """
            )

    def initialize_persona(
        self, persona: str, base_prompt: str, base_score: float = 0.85
    ) -> EvolutionCheckpoint:
        """Initialize generation 0 baseline checkpoint for a persona."""
        active = self.get_active_checkpoint(persona)
        if active:
            return active

        checkpoint = EvolutionCheckpoint(
            checkpoint_id=f"chk_{persona.lower()}_g0_{uuid.uuid4().hex[:6]}",
            persona=persona.lower(),
            generation=0,
            active_prompt=base_prompt.strip(),
            composite_score=base_score,
            is_active=True,
        )

        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO evolution_checkpoints (
                    checkpoint_id, persona, generation, active_prompt, composite_score, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?);
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.persona,
                    checkpoint.generation,
                    checkpoint.active_prompt,
                    checkpoint.composite_score,
                    checkpoint.created_at,
                ),
            )

        return checkpoint

    def get_active_checkpoint(self, persona: str) -> EvolutionCheckpoint | None:
        """Get the currently active prompt checkpoint for a persona."""
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT checkpoint_id, persona, generation, active_prompt, composite_score, is_active, created_at
                FROM evolution_checkpoints
                WHERE persona = ? AND is_active = 1
                ORDER BY generation DESC
                LIMIT 1;
                """,
                (persona.lower(),),
            ).fetchone()

            if not row:
                return None

            return EvolutionCheckpoint(
                checkpoint_id=row["checkpoint_id"],
                persona=row["persona"],
                generation=row["generation"],
                active_prompt=row["active_prompt"],
                composite_score=row["composite_score"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    def save_variant(self, variant: EvolutionVariant) -> None:
        """Store an evaluated candidate mutation."""
        with self._lock, self._get_connection() as conn:
            score = variant.score
            conn.execute(
                """
                INSERT INTO evolution_variants (
                    variant_id, persona, generation, parent_checkpoint_id, prompt_diff, mutated_prompt,
                    mutation_rationale, accuracy_score, tool_discipline_score, conciseness_score,
                    composite_score, passed_safety_gate, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    variant.variant_id,
                    variant.persona.lower(),
                    variant.generation,
                    variant.parent_checkpoint_id,
                    variant.prompt_diff,
                    variant.mutated_prompt,
                    variant.mutation_rationale,
                    score.accuracy_score if score else None,
                    score.tool_discipline_score if score else None,
                    score.conciseness_score if score else None,
                    score.composite_score if score else None,
                    1 if (score and score.passed_safety_gate) else 0,
                    variant.status,
                    variant.created_at,
                ),
            )

    def list_variants(self, persona: str, limit: int = 20) -> list[EvolutionVariant]:
        """List recent candidate mutations for a persona."""
        with self._lock, self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT variant_id, persona, generation, parent_checkpoint_id, prompt_diff, mutated_prompt,
                       mutation_rationale, accuracy_score, tool_discipline_score, conciseness_score,
                       composite_score, passed_safety_gate, status, created_at
                FROM evolution_variants
                WHERE persona = ?
                ORDER BY created_at DESC
                LIMIT ?;
                """,
                (persona.lower(), limit),
            ).fetchall()

            return [
                EvolutionVariant(
                    variant_id=r["variant_id"],
                    persona=r["persona"],
                    generation=r["generation"],
                    parent_checkpoint_id=r["parent_checkpoint_id"],
                    prompt_diff=r["prompt_diff"],
                    mutated_prompt=r["mutated_prompt"],
                    mutation_rationale=r["mutation_rationale"],
                    score=MutationScore(
                        accuracy_score=r["accuracy_score"] or 0.0,
                        tool_discipline_score=r["tool_discipline_score"] or 0.0,
                        conciseness_score=r["conciseness_score"] or 0.0,
                        composite_score=r["composite_score"] or 0.0,
                        passed_safety_gate=bool(r["passed_safety_gate"]),
                    )
                    if r["composite_score"] is not None
                    else None,
                    status=r["status"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def promote_variant(self, variant_id: str) -> EvolutionCheckpoint:
        """Promote an evaluated variant to be the new active checkpoint."""
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM evolution_variants WHERE variant_id = ?;",
                (variant_id,),
            ).fetchone()

            if not row:
                raise ValueError(f"Variant {variant_id} not found")

            persona = row["persona"]
            new_gen = row["generation"]
            score = float(row["composite_score"] or 0.85)

            # Deactivate previous active checkpoints
            conn.execute(
                "UPDATE evolution_checkpoints SET is_active = 0 WHERE persona = ?;",
                (persona,),
            )

            new_checkpoint = EvolutionCheckpoint(
                checkpoint_id=f"chk_{persona}_g{new_gen}_{uuid.uuid4().hex[:6]}",
                persona=persona,
                generation=new_gen,
                active_prompt=row["mutated_prompt"],
                composite_score=score,
                is_active=True,
            )

            conn.execute(
                """
                INSERT INTO evolution_checkpoints (
                    checkpoint_id, persona, generation, active_prompt, composite_score, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?);
                """,
                (
                    new_checkpoint.checkpoint_id,
                    new_checkpoint.persona,
                    new_checkpoint.generation,
                    new_checkpoint.active_prompt,
                    new_checkpoint.composite_score,
                    new_checkpoint.created_at,
                ),
            )

            conn.execute(
                "UPDATE evolution_variants SET status = 'promoted' WHERE variant_id = ?;",
                (variant_id,),
            )

            return new_checkpoint

    def rollback_to_generation(self, persona: str, target_generation: int) -> EvolutionCheckpoint:
        """Rollback persona prompt to a specific previous generation."""
        with self._lock, self._get_connection() as conn:
            target_row = conn.execute(
                """
                SELECT checkpoint_id, persona, generation, active_prompt, composite_score, is_active, created_at
                FROM evolution_checkpoints
                WHERE persona = ? AND generation = ?;
                """,
                (persona.lower(), target_generation),
            ).fetchone()

            if not target_row:
                raise ValueError(
                    f"Checkpoint for persona {persona} at generation {target_generation} not found"
                )

            # Deactivate current
            conn.execute(
                "UPDATE evolution_checkpoints SET is_active = 0 WHERE persona = ?;",
                (persona.lower(),),
            )
            # Activate target
            conn.execute(
                "UPDATE evolution_checkpoints SET is_active = 1 WHERE checkpoint_id = ?;",
                (target_row["checkpoint_id"],),
            )

            return EvolutionCheckpoint(
                checkpoint_id=target_row["checkpoint_id"],
                persona=target_row["persona"],
                generation=target_row["generation"],
                active_prompt=target_row["active_prompt"],
                composite_score=target_row["composite_score"],
                is_active=True,
                created_at=target_row["created_at"],
            )
