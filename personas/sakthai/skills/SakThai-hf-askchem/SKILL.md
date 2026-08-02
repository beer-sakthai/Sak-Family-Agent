---
name: SakThai-hf-askchem
author: SakThai
license: MIT
description: "Complete reference on AskChem (bing-yan/askchem) — claim-centered chemistry literature retrieval infrastructure: 2.44M atomic claims / 147K papers, 9 hierarchical views, AskChem-Bench, REST + SDK + MCP access, and the claim-level retrieval paradigm."
version: 1.0.0
category: mlops
tags: [huggingface, chemistry, knowledge-graph, retrieval, claims, mcp, benchmark, dataset]
platforms: [linux]
---

# AskChem — Claim-Centered Chemistry Literature Infrastructure

Scan date 2026-07-31 (arXiv:2607.28618, 70 upvotes, top uncovered daily paper). Authors: Bing Yan, Gregory Wolfe, Stefano Martiniani, Kyunghyun Cho (NYU). Live at https://askchem.org. Code: github.com/bingyan4science/structure_the_universe (MIT).

## Core paradigm

AskChem changes the unit of scientific retrieval from the **paper** to the **provenance-carrying claim**: each paper is converted into atomic, typed claims, each grounded by a source DOI + verbatim quote or explicit evidence locator. Over a shared claim store it exposes: a stabilized faceted taxonomy (hierarchical retrieval/browsing), an evidence graph (relations between claims), and an exploratory living taxonomy.

## Dataset facts (bing-yan/askchem)

- License CC-BY-4.0 (software MIT), 139 downloads at scan, modified 2026-07-31
- 2,442,810 claims / 146,627 papers / 9 views / 208,721 tree nodes
- Files: askchem.db (21.7 GB SQLite + FTS5 — same DB as the live API), claims.jsonl (3.79 GB), sources.jsonl (98 MB), paper_classifications.json (24.5 MB), embeddings_v2/ (FAISS), benchmark/, hierarchy/, taxonomy/
- **Pitfall:** `v2_backup_20260406/` holds 4,215 of 4,244 siblings (99%) — an old chemtree backup. Live artifacts are top-level.
- README's "~25.44 GB" for askchem.db ≠ actual 21.7 GB (tree API is ground truth).

## Extraction pipeline

- gpt-5-mini (abstracts) + gemini-3.1-pro deep full-paper extraction (Vertex AI Batch)
- gemini-3.1-pro batch classification (paper-level + claim-level) into 9 simultaneous views
- 13 claim types: reaction, property, method, mechanism, comparison, computational_result, limitation, hypothesis, surprising_finding, scope_entry, future_direction, experimental_design, structure
- Taxonomy versions tracked per claim (`taxonomy_migrations` maps old → new view paths; current taxonomy-v4-2026-07)

## Claim schema (verified from real rows)

`claim_id` (16-hex), `claim_type`, `classification` (5+ views), `conditions` (structured: additives/atmosphere/catalyst/concentration/solvent/temperature/time), `confidence` (high/medium), `extraction_model`/`extraction_version`, `is_key_result`, `location_in_paper` (e.g. "Table 1, entry 1"), `outcomes` (yield/ee/dr/TON/selectivity), `products`/`reactants` (name/role/SMILES), `reaction_type`, `source_doi`, `source_paper_title`, `taxonomy_migrations`, `taxonomy_version`, `verbatim_quote`, `view_paths` (7+ views). Property claims: `property_name`, `property_category`, `value`, `subject`, `measurement_method`.

## AskChem-Bench (verified)

30 questions, tasks CA/CS/TC, aggregate.json (gpt-5.4). Grounding lifts: CA doi_existence 0.546→0.985, citation_density 2.6→14.4; CS doi_existence 0.653→1.0, citation_density 3.0→11.1; TC 0.905→0.982, 9.7→16.6. Paper headline (GPT-5.5 reader): 100% resolvable DOIs vs 88.3% without retrieval, highest citation density of 5 systems.

## Access

- REST: `curl "https://askchem.org/api/search?q=suzuki+coupling&limit=5"` (verified live 2026-07-31)
- SDK + MCP server: documented on askchem.org, downloadable `askchem_mcp.py` (verified present)
- Local: load the SQLite DB directly or stream claims.jsonl

## Reuse for the house

- MCP-server pattern for agent-native retrieval over a large structured corpus (claims with provenance beats doc ranking for RAG synthesis).
- Full-stack release pattern: one dataset repo ships DB + JSONL + embeddings + benchmark + versioned taxonomy.
- Provenance-auditable LLM extraction: confidence + extraction_model + verbatim_quote on every row.
