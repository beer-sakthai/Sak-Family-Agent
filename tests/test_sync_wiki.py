"""Unit tests for GitHub Wiki synchronizer helper."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.sync_wiki import (
    generate_sidebar,
    main,
    sanitize_wiki_filename,
    sync_docs_to_wiki,
)


def test_sanitize_wiki_filename() -> None:
    assert sanitize_wiki_filename("architecture-overview.md") == "Architecture Overview.md"
    assert sanitize_wiki_filename("docs/core_rules.md") == "Core Rules.md"


def test_generate_sidebar(tmp_path: Path) -> None:
    doc1 = tmp_path / "architecture.md"
    doc2 = tmp_path / "capabilities.md"
    doc3 = tmp_path / "home.md"
    doc1.touch()
    doc2.touch()
    doc3.touch()

    sidebar = generate_sidebar([doc1, doc2, doc3], tmp_path)
    assert "- [[Home]]" in sidebar
    assert "[[Architecture|architecture]]" in sidebar
    assert "[[Capabilities|capabilities]]" in sidebar
    # home.md should be skipped in the list since it's the home page
    assert "[[Home|home]]" not in sidebar


def test_sync_docs_to_wiki(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    wiki_dir = tmp_path / "wiki"

    (docs_dir / "getting-started.md").write_text(
        "# Getting Started\n\nSee [Architecture](./architecture.md).",
        encoding="utf-8",
    )
    (docs_dir / "architecture.md").write_text(
        "# Architecture\n\nDetails here.",
        encoding="utf-8",
    )

    synced = sync_docs_to_wiki(docs_dir, wiki_dir)
    assert "getting-started.md" in synced
    assert "architecture.md" in synced
    assert "Home.md" in synced
    assert "_Sidebar.md" in synced

    # Check content rewrite
    content = (wiki_dir / "getting-started.md").read_text(encoding="utf-8")
    assert "[[architecture|Architecture]]" in content


def test_sync_docs_missing_dir(tmp_path: Path) -> None:
    non_existent = tmp_path / "non_existent"
    with pytest.raises(FileNotFoundError):
        sync_docs_to_wiki(non_existent, tmp_path / "wiki")


def test_main_cli(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide", encoding="utf-8")
    wiki_dir = tmp_path / "wiki"

    ret = main(["--docs-dir", str(docs_dir), "--wiki-dir", str(wiki_dir)])
    assert ret == 0
    assert (wiki_dir / "guide.md").exists()
