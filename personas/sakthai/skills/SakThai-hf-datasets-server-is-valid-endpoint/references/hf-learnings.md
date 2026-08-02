# HF Learning: Datasets Server /is-valid Endpoint
**Date:** 2026-07-25
**Author:** SakThai
**License:** MIT

## What I learned

The Datasets Server `/is-valid` endpoint is a lightweight pre-flight check for datasets on the Hugging Face Hub. It returns a JSON object with five boolean fields (`viewer`, `preview`, `search`, `filter`, `statistics`) that indicate what capabilities are available for a given dataset — or an error message if the dataset doesn't exist, is private, gated, or broken.

## Key findings

1. **Zero-cost, fast validation** — The endpoint returns responses instantly (pre-computed by the Datasets Server backend). No dataset loading needed.

2. **Per-config capability matrix** — Different configs of the same dataset can have different capability profiles (e.g., `fineweb` as a whole supports all five, but `fineweb?config=default` only supports preview + viewer).

3. **Streaming detection** — `preview: true` + `viewer: false` means the dataset is too large for full viewer but supports streaming of first 100 rows.

4. **Authentication-aware** — Gated datasets return the same "does not exist" error as non-existent ones when unauthenticated, preventing information leakage.

5. **Config pattern** — `?dataset=repo&config=name` is optional; omitting config checks the root/default config.

## Practical uses

- Building robust dataset pipelines that handle errors gracefully
- Capability-aware UI that shows/hides search/filter/statistics based on availability
- Validating dataset references before loading with `datasets` library
- Automating dataset quality checks in CI/CD

## Sources

- https://huggingface.co/docs/dataset-viewer/en/valid
- https://github.com/huggingface/dataset-viewer/blob/main/docs/source/valid.md
- Live testing against `HuggingFaceFW/fineweb`
