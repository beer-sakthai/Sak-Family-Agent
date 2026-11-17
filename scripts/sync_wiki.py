"""GitHub Wiki synchronization helper for House of Sak."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def sanitize_wiki_filename(filename: str) -> str:
    """Sanitize a filename for GitHub Wiki."""
    name = Path(filename).stem
    # Replace dashes/underscores with spaces or preserve clean naming
    clean = name.replace("-", " ").replace("_", " ").title()
    return f"{clean}.md"


def generate_sidebar(doc_files: list[Path], docs_root: Path) -> str:
    """Generate Markdown for GitHub Wiki _Sidebar.md."""
    lines = [
        "## House of Sak Documentation",
        "",
        "- [[Home]]",
        "",
        "### Core Guides",
    ]

    sorted_files = sorted(doc_files, key=lambda p: p.name.lower())
    for doc in sorted_files:
        if doc.name.lower() in {"readme.md", "_sidebar.md", "_footer.md", "home.md"}:
            continue
        rel = doc.relative_to(docs_root)
        display_name = rel.stem.replace("-", " ").replace("_", " ").title()
        wiki_target = rel.stem
        lines.append(f"- [[{display_name}|{wiki_target}]]")

    lines.append("")
    return "\n".join(lines)


def sync_docs_to_wiki(docs_dir: Path, wiki_dir: Path) -> list[str]:
    """Copy and transform Markdown files from docs_dir to wiki_dir."""
    if not docs_dir.exists():
        raise FileNotFoundError(f"Source docs directory not found: {docs_dir}")
    wiki_dir.mkdir(parents=True, exist_ok=True)

    synced_files: list[str] = []
    markdown_files = list(docs_dir.glob("**/*.md"))

    for doc in markdown_files:
        dest_filename = f"{doc.stem}.md"
        dest_path = wiki_dir / dest_filename
        content = doc.read_text(encoding="utf-8")

        # Rewrite standard relative markdown links [text](./other.md) -> [[other|text]] or [text](other)
        rewritten = re.sub(
            r"\[([^\]]+)\]\((?:\./)?([a-zA-Z0-9_\-]+)\.md\)",
            r"[[\2|\1]]",
            content,
        )

        dest_path.write_text(rewritten, encoding="utf-8")
        synced_files.append(dest_filename)

    # Generate Home.md if not explicitly present
    home_file = wiki_dir / "Home.md"
    if not home_file.exists():
        docs_readme = docs_dir / "README.md"
        if docs_readme.exists():
            home_file.write_text(docs_readme.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            home_content = (
                "# House of Sak — Agent Workspace\n\n"
                "Welcome to the official **House of Sak** documentation wiki.\n\n"
                "> Dream → Hope → Care → Joy → Trust → Growth\n\n"
                "Please navigate using the sidebar on the right.\n"
            )
            home_file.write_text(home_content, encoding="utf-8")
        synced_files.append("Home.md")

    # Generate _Sidebar.md
    sidebar_file = wiki_dir / "_Sidebar.md"
    sidebar_content = generate_sidebar(markdown_files, docs_dir)
    sidebar_file.write_text(sidebar_content, encoding="utf-8")
    synced_files.append("_Sidebar.md")

    return sorted(set(synced_files))


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for wiki synchronizer."""
    parser = argparse.ArgumentParser(description="Synchronize repository docs to GitHub Wiki.")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Source directory containing Markdown documentation (default: docs).",
    )
    parser.add_argument(
        "--wiki-dir",
        type=Path,
        required=True,
        help="Target directory where .wiki.git is cloned.",
    )
    args = parser.parse_args(argv)

    synced = sync_docs_to_wiki(args.docs_dir, args.wiki_dir)
    print(f"Successfully synced {len(synced)} documentation pages to wiki: {args.wiki_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
