# HF CLI Rebuilt: huggingface_hub v1.22–v1.24 — Deep Dive

**Skill name:** `hf-hub-cli-rebuilt`
**author:** SakThai
**license:** MIT

Covers the major CLI and API changes in huggingface_hub releases v1.22.0 (2026-07-03), v1.23.0 (2026-07-09), and v1.24.0 (2026-07-17), plus **empirically discovered** details of the skills marketplace and extensions ecosystem.

---

## Key Features by Version

### v1.22.0 (2026-07-03)
- **Sandboxes** — isolated cloud machines on top of Jobs (`Sandbox.create`, `SandboxPool`, `hf sandbox create/exec/cp/kill/spawn`)
- **Tree cache** — `snapshot_download` caches file listings on disk under `trees/`, eliminating per-file metadata requests
- **CLI rebuilt on Click** — entire `hf` CLI migrated from Typer to Click 8.x (byte-identical `--help`, native shell completion)
- `hf discussions edit` — edit discussion/PR comments from CLI
- `hf cache ls/prune` — surface and remove incomplete `.incomplete` downloads
- `hf jobs scheduled trigger` — trigger scheduled jobs on demand
- `sync_job_volume` helper + local paths in `hf jobs -v`
- `upload_large_folder` / `hf upload-large-folder` deprecated (use `upload_folder`/`hf upload`)
- Case-sensitive pattern matching on all platforms (breaking on Windows)
- `http_backoff` now honors standard `Retry-After` header

### v1.23.0 (2026-07-09)
- **Space templates** — seed Spaces from official templates (`hf spaces templates`, `hf repos create --type space --template`, `create_repo(..., space_template=...)`)
- **CLI extensions update** — `hf extensions update` command
- **Smoother Xet downloads** — improved download stability

### v1.24.0 (2026-07-17)
- **Job naming** — optional `--name` flag on CLI, `name` parameter on Python API, `hf jobs labels <id> --name`
- **CLI-first README** — standalone installer and terminal quick start prioritized
- **Xet download rate fix** — shows summed speed, not per-file

---

## CLI Command Tree (Post-Rebuild — Full Empirically Verified)

Tested with `hf --help` on huggingface_hub v1.24.0 running Python 3.14.4 on Linux 6.8.0:

```
hf
├── auth                 login / logout / whoami / switch / token / list
├── buckets              cp / create / delete / info / list / move / remove / sync
├── cache                list / prune / rm / verify
├── collections          add-item / create / delete / delete-item / info / list / update / update-item
├── cp                   (copy via hf:// URIs)
├── datasets             card / info / leaderboard / list / parquet / sql
├── discussions          close / comment / create / diff / edit / info / list
├── download             (file, repo, revision, hf:// URI, dry-run, quiet)
├── endpoints            (inference endpoints — subcommands not exposed in --help)
├── env
├── extensions           exec / install / list / remove / search / update
├── jobs                 ls / run / uv-run / ssh / scheduled / labels / wait / logs / cancel / ps
├── lfs-enable-largefiles
├── lfs-multipart-upload
├── models               list / info / card
├── papers               list / info
├── repos                create / delete / move / list
├── sandbox              create / exec / cp / kill / spawn / list / logs / proxy
├── skills               add / list / preview / update
├── spaces               templates / list / info
├── sync                 (bucket sync)
├── upload               (folder, file, hf:// URI, regular-interval, commit-msg, PR)
├── upload-large-folder  [Deprecated — use `hf upload`]
└── update               (update CLI to latest version)
```

**CLI version check:** `hf --version` → `1.24.0`
**huggingface-cli is deprecated:** Running `huggingface-cli` prints a deprecation message redirecting to `hf`.

**Key API now live (`hf models list` verified):**
```
hf models list --search "gemma" --limit 5
→ google/gemma-4-31B-it, unsloth/gemma-4-26B-A4B-it-qat-GGUF, ...
hf datasets list --search "sakthai" --limit 10
→ Nanthasit/sakthai-toolcalling-v1, Nanthasit/sakthai-combined-v1, ... (7 datasets)
hf collections list --owner Nanthasit
→ sakthai-model-family, sakthai-context, sakthai-models (4 collections)
```

**Environment (`hf env` verified):**
```
huggingface_hub version: 1.24.0
Platform: Linux-6.8.0-134-generic-x86_64-with-glibc2.41
Python version: 3.14.4
Has saved token: True (user: Nanthasit)
ENDIF: https://huggingface.co
HF_HUB_CACHE: /opt/data/.cache/huggingface/hub
HF_HUB_DISABLE_XET: False
HF_XET_HIGH_PERFORMANCE: False
```

---

## `hf skills` Marketplace — Complete Reference

The `hf skills` system is a **new feature in v1.24.0** that provides a marketplace of curated skills for AI assistants (Claude Code, etc.). Skills are markdown files that describe how to use specific HF features.

### Commands

| Command | Description |
|---------|-------------|
| `hf skills list` | List available marketplace skills (25 available in v1.24.0) |
| `hf skills add [name]` | Install a skill to `.agents/skills/` (or `~/.agents/skills/` with `--global`) |
| `hf skills preview` | Print the generated `hf-cli` skill to stdout |
| `hf skills update [name]` | Update installed marketplace skills |

### Output Formats

All skills commands support `--format [auto|human|agent|json|quiet]`:
- `--json`: Full JSON output
- `--quiet` / `-q`: One name per line (for scripting)
- `--format agent`: Optimized for AI consumption

### All 25 Marketplace Skills (v1.24.0, empirically listed)

| # | Skill Name | Description |
|---|-----------|-------------|
| 1 | `hf-cli` | Built-in: covers all `hf` CLI commands. Auto-generated from installed version. |
| 2 | `hf-cloud-aws-context-discovery` | Discover user's local AWS context at start of any AWS task |
| 3 | `hf-cloud-python-env-setup` | Set up isolated Python env for SageMaker / AWS |
| 4 | `hf-cloud-sagemaker-deployment-planner` | Plan/coordinate model deployment to SageMaker |
| 5 | `hf-cloud-sagemaker-iam-preflight` | Ensure usable SageMaker execution role exists |
| 6 | `hf-cloud-sagemaker-production-defaults` | SageMaker endpoint with autoscaling, CloudWatch, tagging |
| 7 | `hf-cloud-serving-image-selection` | Pick right serving container for SageMaker |
| 8 | `hf-mem` | Estimate memory to load Safetensors/GGUF model weights |
| 9 | `huggingface-best` | Find best/top/recommended model for a task |
| 10 | `huggingface-community-evals` | Run evaluations with inspect-ai and lighteval |
| 11 | `huggingface-datasets` | Dataset Viewer API workflows |
| 12 | `huggingface-gradio` | Build Gradio web UIs and demos |
| 13 | `huggingface-llm-trainer` | Train/fine-tune with TRL or Unsloth on HF Jobs |
| 14 | `huggingface-local-models` | Run models locally with llama.cpp + GGUF |
| 15 | `huggingface-lora-space-builder` | Build/publish Gradio demo for a LoRA |
| 16 | `huggingface-paper-publisher` | Publish/manage research papers on HF Hub |
| 17 | `huggingface-papers` | Look up/read HF paper pages |
| 18 | `huggingface-spaces` | Build/deploy/maintain Gradio/Docker/Static Spaces |
| 19 | `huggingface-tool-builder` | Build tools/scripts using HF API data |
| 20 | `huggingface-trackio` | Track/visualize ML experiments with Trackio |
| 21 | `huggingface-vision-trainer` | Train vision models (D-FINE, RT-DETR, SAM, etc.) on HF Jobs |
| 22 | `huggingface-zerogpu` | AI demos with ZeroGPU on Gradio Spaces |
| 23 | `train-sentence-transformers` | Train SentenceTransformer / CrossEncoder / SparseEncoder |
| 24 | `transformers-js` | Run ML models in JS/TS with Transformers.js |
| 25 | `trl-training` | Train/fine-tune with TRL (Transformers RL) |

### How Skills Work

1. **Entry point:** `hf skills add` installs the `hf-cli` skill (auto-generated)
2. **Install location:** Project-level `.agents/skills/` or global `~/.agents/skills/`
3. **Claude integration:** `--claude` flag symlinks into Claude's legacy skills directory
4. **Skill format:** Markdown with YAML frontmatter (name, description) and command reference
5. **Regeneration:** Run `hf skills add --force` to regenerate the `hf-cli` skill from current CLI version
6. **Preview:** `hf skills preview` prints the generated SKILL.md to stdout without installing

### Key Insight

The `hf-cli` skill is **auto-generated** from the installed `huggingface_hub` version at build time. Running `hf skills add --force` regenerates it with your exact version's command tree. This means the skill is always in sync with the installed CLI — no stale documentation.

---

## `hf extensions` Ecosystem — Complete Reference

The extensions system allows third-party developers to extend the `hf` CLI with custom commands. Extensions are GitHub repositories tagged with the `hf-extension` topic.

### Commands

| Command | Description |
|---------|-------------|
| `hf extensions install REPO_ID` | Install extension from GitHub (e.g., `hf-claude`, `alvarobartt/hf-mem`) |
| `hf extensions exec NAME [args]` | Execute installed extension (prefix auto-detected: `hf-` or bare name) |
| `hf extensions list` | List installed extensions |
| `hf extensions remove NAME` | Remove installed extension |
| `hf extensions search` | Search GitHub for extensions tagged `hf-extension` |
| `hf extensions update [name]` | Update installed extension(s) to latest version |

### All 18 Discovered Extensions (empirically found via `hf extensions search`)

| # | Name | Repo | Stars | Description |
|---|------|------|-------|-------------|
| 1 | `mem` | `alvarobartt/hf-mem` | 938 | Estimate inference memory for HF models |
| 2 | `agents` | `huggingface/hf-agents` | 426 | Run local coding agent with llmfit + llama.cpp |
| 3 | `sandbox` | `huggingface/hf-sandbox` | 156 | Modal-style sandbox API on top of HF Jobs |
| 4 | `discover` | `huggingface/hf-discover` | 34 | Agentic resource discovery client/server |
| 5 | `speedtest` | `julien-c/hf-speedtest` | 25 | How fast can you pull from HF? |
| 6 | `claude` | `hanouticelina/hf-claude` | 8 | Launch Claude Code with HF Inference Providers |
| 7 | `bsh` | `torrid-fish/hf-bsh` | 5 | Interactive bucket shell for HF Hub |
| 8 | `inference` | `huggingface/hf-inference` | 4 | Run inference with HF Inference Providers |
| 9 | `claw` | `burtenshaw/hf-claw` | 4 | Backup/publish/install OpenClaw agents on HF Hub |
| 10 | `gradio` | `gradio-app/hf-gradio` | 3 | Interact with Gradio Spaces and Apps |
| 11 | `docs` | `Wauplin/hf-docs` | 3 | Answer questions about HF documentation via agentic workflow |
| 12 | `image` | `huggingface/hf-image` | 1 | Fast, Xet-native push/pull for HF container registry |
| 13 | `cloud` | `ehcalabres/hf-cloud` | 1 | Deploy HF models directly from Hub |
| 14 | `save-on-storage` | `abidlabs/hf-save-on-storage` | 1 | Analyze S3 costs, migrate to HF Storage Buckets |
| 15 | `ds` | `davanstrien/hf-ds` | 1 | Datasets library: no-download inspect, streaming preview, folder→Hub |
| 16 | `mount` | `mishig25/hf-mount` | 0 | `hf mount` wrapper around `huggingface/hf-mount` |
| 17 | `jobsx` | `davanstrien/hf-jobsx` | 0 | Job selectors + dense live monitor with sparklines |
| 18 | `pi-sync` | `tengomucho/hf-pi-sync` | 0 | Sync pi agent config across VMs via HF Buckets |

### Installation Pattern

```bash
# Install by shorthand (assumes huggingface/hf-<name>)
hf extensions install hf-claude
# Install from specific owner
hf extensions install hanouticelina/hf-claude
# Install by repo name (no hf- prefix)
hf extensions install alvarobartt/hf-mem
```

### Execution Pattern

```bash
# Run installed extension (with or without hf- prefix)
hf extensions exec mem -- --help
hf extensions exec claude --model google/gemma-4-31B-it
# Pass extra args after --
hf extensions exec inference --endpoint /v1/chat/completions
```

### Usage Notes (Empirically Verified)

- **Security warning:** CLI prints a warning on `extensions install`: "extensions are third-party executables or Python packages. Install only from sources you trust."
- **No installed extensions by default:** `hf extensions list` returns "No results found" on fresh install
- **GitHub topic tag required:** Extensions must be tagged `hf-extension` on GitHub to appear in `search`
- **Extensions are not the same as skills** — skills are markdown files for AI assistants; extensions are executable CLI plugins

---

## `hf datasets sql` — DuckDB SQL from CLI

A new subcommand under `hf datasets` that executes raw SQL queries with DuckDB against dataset Parquet URLs.

### Syntax

```bash
hf datasets sql "SELECT COUNT(*) AS rows FROM read_parquet('<parquet-url>')"
hf datasets sql "SELECT * FROM read_parquet('<parquet-url>') LIMIT 5" --format json
```

### Parameters

| Flag | Description |
|------|-------------|
| `SQL` | (positional) Raw SQL query |
| `--token` | HF token for gated datasets |
| `--format` | Output format: auto/human/agent/json/quiet |

### Known Limitation

Requires **DuckDB Python package** (`pip install duckdb`). Without it, returns:
```
Error: DuckDB is required for `hf datasets sql`. Install the Python package with `pip install duckdb`
```

### Usage Pattern

The `read_parquet()` function accepts:
- Direct Parquet URLs from `hf datasets parquet <dataset>`
- Multiple URLs as a list: `read_parquet(['url1', 'url2'])`
- Glob patterns if supported by the HTTP server

---

## CLI Format System

All `hf` CLI commands that return data support a **unified format system**:

| Format | Flag | Use Case |
|--------|------|---------|
| `auto` | (default) | Picks `agent` or `human` based on terminal detection |
| `human` | `--format human` | Readable tables, truncation |
| `agent` | `--format agent` | Machine-optimized for AI consumption |
| `json` | `--json` | Full JSON output |
| `quiet` | `-q` or `--format quiet` | One item per line, no headers (for scripting) |

Verified working on: `hf models list`, `hf datasets list`, `hf collections list`, `hf skills list`, `hf extensions search`, `hf cache list`, and all `--format` variants.

---

## Deprecations & Breaking
- `upload_large_folder` deprecated → use `upload_folder`/`hf upload`
- Pattern matching now case-sensitive on all platforms
- Dead inference providers removed (black-forest-labs, clarifai, hyperbolic, nebius, nvidia, sambanova)
- Jobs no longer Pro-only (v1.22)
- `huggingface-cli` is fully deprecated — only `hf` works
