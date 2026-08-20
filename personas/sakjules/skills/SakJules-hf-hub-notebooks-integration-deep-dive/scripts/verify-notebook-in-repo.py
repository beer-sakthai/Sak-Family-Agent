#!/usr/bin/env python3
"""Verify whether a HF repo has notebook files and custom notebook.ipynb.

Usage:
    python verify-notebook-in-repo.py <repo_id> [--repo-type model|dataset|space]

Examples:
    python verify-notebook-in-repo.py google/gemma-3-4b-it
    python verify-notebook-in-repo.py NousResearch/Genstruct-7B
    python verify-notebook-in-repo.py bigcode/the-stack-v2 --repo-type dataset
"""

import sys
import argparse
from huggingface_hub import list_repo_files, repo_exists

def check_notebooks(repo_id: str, repo_type: str = "model"):
    if not repo_exists(repo_id, repo_type=repo_type):
        print(f"❌ Repo '{repo_id}' (type={repo_type}) does not exist.")
        return False

    files = list_repo_files(repo_id, repo_type=repo_type)
    notebooks = [f for f in files if f.endswith(".ipynb")]
    has_custom = "notebook.ipynb" in files

    print(f"📓 Repo: {repo_id} (type={repo_type})")
    print(f"   Total files: {len(files)}")
    print(f"   Notebook files: {len(notebooks)}")
    print(f"   Custom notebook.ipynb: {'✅ YES' if has_custom else '❌ No'}")

    if notebooks:
        print("\n   Notebooks found:")
        for nb in sorted(notebooks):
            marker = " ← custom Colab/Kaggle notebook" if nb == "notebook.ipynb" else ""
            print(f"     • {nb}{marker}")

    return True

def main():
    parser = argparse.ArgumentParser(description="Check HF repo for notebook files")
    parser.add_argument("repo_id", help="Hugging Face repo ID (e.g. user/model)")
    parser.add_argument("--repo-type", default="model",
                        choices=["model", "dataset", "space"],
                        help="Repository type (default: model)")
    args = parser.parse_args()

    success = check_notebooks(args.repo_id, args.repo_type)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
