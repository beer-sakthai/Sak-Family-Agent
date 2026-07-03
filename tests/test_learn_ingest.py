"""Unit tests for the document ingest parser (``sakthai.learn.ingest``).

These exercise ``_facts_from_markdown_or_text`` and ``_facts_from_csv`` directly,
plus ``ingest_document`` end-to-end against a real on-disk ``MemoryStore`` — the
parser was previously only reached through the ``ingest_document`` agent tool.
"""

from __future__ import annotations

from pathlib import Path

from sakthai.learn.ingest import (
    _facts_from_csv,
    _facts_from_markdown_or_text,
    ingest_document,
)
from sakthai.memory.store import MemoryStore


def test_markdown_parser_skips_headings_and_blank_lines() -> None:
    text = "# Title\n\n## Section\n\nA plain sentence.\n"
    assert _facts_from_markdown_or_text(text) == ["A plain sentence."]


def test_markdown_parser_strips_all_bullet_markers() -> None:
    text = "- dash item\n* star item\n+ plus item\n"
    assert _facts_from_markdown_or_text(text) == ["dash item", "star item", "plus item"]


def test_markdown_parser_strips_numbered_list_prefixes() -> None:
    text = "1. first thing\n2. second thing\n"
    assert _facts_from_markdown_or_text(text) == ["first thing", "second thing"]


def test_markdown_parser_keeps_dotted_lines_that_are_not_numbered_lists() -> None:
    # "3.14" is a digit-dot-digit run, not a "<n>. " list prefix, so it stays.
    text = "3.14 is pi\nversion 1.2 shipped\n"
    assert _facts_from_markdown_or_text(text) == ["3.14 is pi", "version 1.2 shipped"]


def test_markdown_parser_handles_mixed_content() -> None:
    text = (
        "# Price book\n"
        "\n"
        "- Website audit: $250\n"
        "Custom quotes scoped after discovery.\n"
        "  \n"  # whitespace-only line
        "1. Support plan: $99/month\n"
    )
    assert _facts_from_markdown_or_text(text) == [
        "Website audit: $250",
        "Custom quotes scoped after discovery.",
        "Support plan: $99/month",
    ]


def test_csv_parser_happy_path() -> None:
    text = "question,answer\nHow long?,2 days\nSupport?,Yes\n"
    assert _facts_from_csv(text) == ["How long? -> 2 days", "Support? -> Yes"]


def test_csv_parser_returns_empty_for_header_only() -> None:
    assert _facts_from_csv("question,answer\n") == []


def test_csv_parser_returns_empty_for_single_column() -> None:
    assert _facts_from_csv("question\nHow long?\n") == []


def test_csv_parser_skips_rows_with_blank_or_missing_cells() -> None:
    text = "q,a\n,orphan answer\nHas question,\nGood,Row\n"
    assert _facts_from_csv(text) == ["Good -> Row"]


def test_ingest_document_routes_markdown_into_store(store: MemoryStore, tmp_path: Path) -> None:
    doc = tmp_path / "notes.md"
    doc.write_text("# Notes\n\n- alpha\n- beta\n", encoding="utf-8")

    ids = ingest_document(doc, store=store)

    assert len(ids) == 2
    facts = store.list_facts()
    assert {f.value for f in facts} == {"alpha", "beta"}
    assert {f.kind for f in facts} == {"fact"}


def test_ingest_document_routes_csv_by_suffix(store: MemoryStore, tmp_path: Path) -> None:
    doc = tmp_path / "faq.csv"
    doc.write_text("q,a\nPing?,Pong\n", encoding="utf-8")

    ingest_document(doc, store=store)

    facts = store.list_facts()
    assert [f.value for f in facts] == ["Ping? -> Pong"]


def test_ingest_document_treats_plain_text_as_markdown(store: MemoryStore, tmp_path: Path) -> None:
    doc = tmp_path / "notes.txt"
    doc.write_text("Custom project quotes are scoped after discovery.", encoding="utf-8")

    ingest_document(doc, store=store)

    facts = store.list_facts()
    assert [f.value for f in facts] == ["Custom project quotes are scoped after discovery."]


def test_ingest_document_decodes_invalid_bytes_with_replacement(
    store: MemoryStore, tmp_path: Path
) -> None:
    # Invalid UTF-8 bytes must not raise; ``errors="replace"`` swaps in U+FFFD.
    doc = tmp_path / "broken.txt"
    doc.write_bytes(b"- caf\xe9 special\n")

    ids = ingest_document(doc, store=store)

    assert len(ids) == 1
    (fact,) = store.list_facts()
    assert fact.value.startswith("caf")
    assert "special" in fact.value


def test_ingest_document_accepts_str_path(store: MemoryStore, tmp_path: Path) -> None:
    doc = tmp_path / "notes.md"
    doc.write_text("- only line\n", encoding="utf-8")

    ids = ingest_document(str(doc), store=store)

    assert len(ids) == 1
    assert [f.value for f in store.list_facts()] == ["only line"]
