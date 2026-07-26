# Model Card Enrichment Workflow

Enrich all model cards in an HF account with consistent branding, family cross-links, benchmarks, and professional sections.

## Pattern

1. **Branding header** — Add "House of Sak" banner with profile + collection badges
2. **Family cross-link table** — Every card gets a full table of all models with sizes and download counts
3. **Benchmark comparison** — For LLM models, add a professional comparison vs similar-sized models using real published data (MMLU, BBH from papers) + your own BFCL tool-calling results
4. **Controlled comparison** — Run the base model side-by-side with your fine-tuned version on the same hardware
5. **Ollama guide** — Add Modelfile creation steps
6. **Hardware requirements** — RAM (min/recommended/disk) table
7. **Training details** — Method, base model, rank, dataset size, context length

## Execution

Iterate over ALL models under the author. Use `HfApi.upload_file()` to update each README.md. Check for existing content before adding to avoid duplicates.

## Pitfalls

- Preserve YAML frontmatter — always insert content AFTER the closing `---`
- Don't re-upload unchanged cards
- Use official tech report numbers for comparison tables, not estimates
- Spot-check 2-3 URLs after batch updates to confirm changes landed
