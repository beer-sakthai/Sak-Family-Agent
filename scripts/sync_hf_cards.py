#!/usr/bin/env python3
"""Batch Model & Dataset Card Synchronizer for House of Sak Hugging Face Ecosystem.

Usage:
    python scripts/sync_hf_cards.py --dry-run
    python scripts/sync_hf_cards.py --repo Nanthasit/context-1.5b-merged --dry-run
    python scripts/sync_hf_cards.py --all
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure personas/sakthai is on sys.path for editable import resolution
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.hub import (
    AssetType,
    HubCardSynchronizer,
    HubEcosystemScanner,
    ModelCardValidator,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_hf_cards")


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize canonical House of Sak model & dataset cards.")
    parser.add_argument("--author", default="Nanthasit", help="HF organization or user namespace.")
    parser.add_argument("--repo", help="Target a specific repo ID (e.g. Nanthasit/context-1.5b-merged).")
    parser.add_argument("--all", action="store_true", help="Process all models and datasets.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview rendered cards without uploading.")
    parser.add_argument("--force-upload", action="store_true", help="Upload rendered cards to Hugging Face Hub.")

    args = parser.parse_args()

    scanner = HubEcosystemScanner(author=args.author)
    validator = ModelCardValidator()
    synchronizer = HubCardSynchronizer()

    logger.info("Scanning ecosystem assets for author '%s'...", args.author)
    report = scanner.scan_ecosystem()
    logger.info("Discovered %d models, %d datasets, %d spaces.", report.total_models, report.total_datasets, report.total_spaces)

    assets_to_process = report.assets
    if args.repo:
        assets_to_process = [a for a in report.assets if a.repo_id == args.repo or a.name == args.repo]
        if not assets_to_process:
            logger.error("Specified repo '%s' not found in ecosystem scan.", args.repo)
            return 1

    success_count = 0
    failure_count = 0

    print("\n" + "=" * 80)
    print(" 🏛️ HOUSE OF SAK — MODEL & DATASET CARD QUALITY AUDIT")
    print("=" * 80)

    for asset in assets_to_process:
        if asset.type == AssetType.SPACE:
            continue

        rendered_card = synchronizer.render_model_card(asset)
        validation = validator.validate_card(asset.repo_id, rendered_card)

        status_badge = "✅ PASSED" if validation.valid else "❌ FAILED"
        print(f"\n[{status_badge}] {asset.type.value.upper()}: {asset.repo_id} (Quality Score: {validation.score}/100)")

        if validation.issues:
            for iss in validation.issues:
                print(f"   - [{iss.severity.upper()}] {iss.rule}: {iss.message}")

        if args.dry_run:
            print(f"   Preview length: {len(rendered_card)} chars (dry-run mode, skipping upload)")
            success_count += 1
        elif args.force_upload:
            logger.info("Uploading card to %s on Hugging Face Hub...", asset.repo_id)
            # Safe upload stub using huggingface_hub if available
            try:
                from huggingface_hub import HfApi
                api = HfApi()
                api.upload_file(
                    path_or_fileobj=rendered_card.encode("utf-8"),
                    path_in_repo="README.md",
                    repo_id=asset.repo_id,
                    repo_type=asset.type.value,
                    commit_message="docs: synchronize canonical House of Sak card",
                )
                logger.info("Successfully uploaded card to %s", asset.repo_id)
                success_count += 1
            except Exception as err:
                logger.error("Upload failed for %s: %s", asset.repo_id, err)
                failure_count += 1

    print("\n" + "=" * 80)
    print(f" Audit Complete: {success_count} processed, {failure_count} errors.")
    print("=" * 80 + "\n")

    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
