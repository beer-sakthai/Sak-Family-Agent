#!/usr/bin/env python3
"""
CommonCrawl → Clean Text Pipeline (DataTrove template)

Reproducible pipeline template for processing CommonCrawl WARC dumps into
clean, filtered, deduplicated text ready for LLM training.

Usage:
    uv pip install datatrove[all]
    python3 commoncrawl-pipeline.py --input s3://my-bucket/cc_dump/ --output hf://buckets/myorg/clean-text/
"""
from __future__ import annotations

import argparse
import logging

from datatrove.executor import LocalPipelineExecutor, SlurmPipelineExecutor
from datatrove.pipeline.dedup import SentenceDedupFilter
from datatrove.pipeline.dedup.minhash import (
    MinhashConfig,
    MinhashDedupBuckets,
    MinhashDedupCluster,
    MinhashDedupFilter,
    MinhashDedupSignature,
)
from datatrove.pipeline.extractors import Trafilatura
from datatrove.pipeline.filters import (
    GopherQualityFilter,
    LanguageFilter,
    URLFilter,
    WordCountFilter,
)
from datatrove.pipeline.readers import WarcReader
from datatrove.pipeline.stats import DocStats, LangStats, WordStats
from datatrove.pipeline.writers import JsonlWriter


def build_pipeline(
    input_path: str,
    output_path: str,
    languages: list[str] | None = None,
    enable_minhash: bool = True,
    enable_sentence_dedup: bool = False,
    min_words: int = 50,
    max_words: int = 100_000,
) -> list:
    """Build a DataTrove pipeline for CommonCrawl processing.

    Args:
        input_path: Path to WARC files (local, S3, or HF bucket).
        output_path: Destination for cleaned JSONL output.
        languages: Language codes to keep (default: ['en']).
        enable_minhash: Run 4-stage MinHash deduplication.
        enable_sentence_dedup: Run sentence-level exact dedup after MinHash.
        min_words: Minimum word count filter.
        max_words: Maximum word count filter.

    Returns:
        List of pipeline blocks ready to pass to an executor.
    """
    if languages is None:
        languages = ["en"]

    blocks: list = [
        # ── 1. Read WARC files ──────────────────────────────────
        WarcReader(
            input_path,
            glob_pattern="*/warc/*.warc.gz",
            default_metadata={"source": "commoncrawl"},
        ),
        # ── 2. Extract text from HTML ────────────────────────────
        Trafilatura(
            prefer_links=False,       # strip all HTML
            include_comments=False,
            include_tables=False,
        ),
        # ── 3. Filters ──────────────────────────────────────────
        URLFilter(
            excluded_domains=[
                "spam.com", "doubleclick.net", "googleadservices.com",
            ],
        ),
        LanguageFilter(languages=languages),
        GopherQualityFilter(
            min_words=min_words,
            max_words=max_words,
            remove_empty=True,
        ),
        WordCountFilter(min_words=min_words, max_words=max_words),
    ]

    # ── 4. MinHash dedup (optional) ──────────────────────────
    if enable_minhash:
        blocks.append(
            MinhashDedupSignature(
                output_folder=f"{output_path}/_intermediate/sigs/",
            )
        )

    # ── 5. Stats before write ─────────────────────────────────
    blocks.extend([
        DocStats(),
        LangStats(),
        WordStats(),
    ])

    # ── 6. Writer ────────────────────────────────────────────
    blocks.append(
        JsonlWriter(
            output_path,
            output_filename="${language}/${rank}.jsonl.gz",
            compression="gzip",
        )
    )

    return blocks


def build_minhash_pipeline(
    input_path: str,
    intermediate_path: str,
    output_path: str,
    ngrams: int = 5,
    num_bands: int = 20,
    num_rows: int = 5,
) -> dict[str, list]:
    """Build a 4-stage MinHash dedup pipeline.

    Returns:
        Dict of {stage_name: pipeline_blocks} to run sequentially.
    """
    config = MinhashConfig(
        ngrams=ngrams,
        num_bands=num_bands,
        num_rows=num_rows,
        seed=42,
    )

    return {
        "signatures": [
            MinhashDedupSignature(
                output_folder=f"{intermediate_path}/sigs/",
            ),
        ],
        "buckets": [
            MinhashDedupBuckets(
                output_folder=f"{intermediate_path}/buckets/",
                config=config,
            ),
        ],
        "clusters": [
            MinhashDedupCluster(
                input_folder=f"{intermediate_path}/buckets/",
                output_folder=f"{intermediate_path}/clusters/",
            ),
        ],
        "filter": [
            MinhashDedupFilter(
                data_folder=input_path,
                clusters_folder=f"{intermediate_path}/clusters/",
                exclusion_writer=JsonlWriter(f"{output_path}/_removed/"),
            ),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process CommonCrawl data with DataTrove",
    )
    parser.add_argument("--input", required=True, help="Path to WARC files")
    parser.add_argument("--output", required=True, help="Output path for clean data")
    parser.add_argument(
        "--executor",
        choices=["local", "slurm"],
        default="local",
        help="Execution environment",
    )
    parser.add_argument("--tasks", type=int, default=100, help="Number of shards/tasks")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers")
    parser.add_argument("--languages", nargs="+", default=["en"], help="Languages to keep")
    parser.add_argument("--min-words", type=int, default=50)
    parser.add_argument("--max-words", type=int, default=100_000)
    parser.add_argument("--slurm-partition", default="hopper-cpu")
    parser.add_argument("--slurm-time", default="10:00:00")
    parser.add_argument("--no-minhash", action="store_true", help="Skip MinHash dedup")
    parser.add_argument(
        "--logging-dir",
        default="logs/commoncrawl",
        help="DataTrove logging directory",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    pipeline = build_pipeline(
        input_path=args.input,
        output_path=args.output,
        languages=args.languages,
        enable_minhash=not args.no_minhash,
        min_words=args.min_words,
        max_words=args.max_words,
    )

    if args.executor == "local":
        executor = LocalPipelineExecutor(
            pipeline=pipeline,
            logging_dir=args.logging_dir,
            tasks=args.tasks,
            workers=args.workers,
        )
    elif args.executor == "slurm":
        executor = SlurmPipelineExecutor(
            pipeline=pipeline,
            logging_dir=args.logging_dir,
            tasks=args.tasks,
            workers=args.workers,
            time=args.slurm_time,
            partition=args.slurm_partition,
        )

    logging.info("Starting pipeline: %s → %s", args.input, args.output)
    executor.run()
    logging.info("Pipeline complete")


if __name__ == "__main__":
    main()
