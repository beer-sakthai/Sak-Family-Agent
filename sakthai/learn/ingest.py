"""Ingest documents into memory as explicit facts."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from ..memory.store import MemoryStore
from .capture import learn as learn_fact


def _facts_from_markdown_or_text(text: str) -> list[str]:
    facts: list[str] = []
    for raw in text.splitlines():
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
            facts.append(line)
    return facts


def _facts_from_csv(text: str) -> list[str]:
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 2 or len(rows[0]) < 2:
        return []
    facts: list[str] = []
    for row in rows[1:]:
        cells = [cell.strip() for cell in row]
        if len(cells) < 2 or not cells[0] or not cells[1]:
            continue
        facts.append(f"{cells[0]} -> {cells[1]}")
    return facts


def ingest_document(path: str | Path, *, store: MemoryStore | None = None) -> list[int]:
    """Parse a document and store each extracted fact in memory."""
    document = Path(path)
    text = document.read_text(encoding="utf-8", errors="replace")
    facts = _facts_from_csv(text) if document.suffix.lower() == ".csv" else _facts_from_markdown_or_text(text)
    stored: list[int] = []
    for fact in facts:
        stored.append(learn_fact(fact, kind="fact", store=store))
    return stored
