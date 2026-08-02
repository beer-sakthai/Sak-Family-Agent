# `hf` CLI – Quirks & Patterns

Collected from real usage. Update as new quirks surface.

## `--author` vs `--owner`

**The `hf` CLI uses `--author`, NOT `--owner`.**

The Hub API URL path uses `owner` (e.g. `/api/models?author=Nanthasit` → actually the API uses `author` too... the confusion comes from other tools that call it `owner`). Passing `--owner` silently ignores the filter and returns all items.

```bash
# ✅ Correct
hf models list --author Nanthasit
hf datasets list --author Nanthasit --format json

# ❌ Wrong — silently returns everything
hf models list --owner Nanthasit
```

## `--format json`

Without it, `hf models list` and `hf datasets list` return a human-readable table.
With `--format json`, output is machine-parseable:

```bash
hf models list --author Nanthasit --format json | jq '.[] | {id, downloads, lastModified}'
```

## PATH

The installer puts `hf` at `~/.local/bin/hf`. This directory is **not** in default PATH on this machine:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Or use the full symlink path: `/opt/data/.local/bin/hf`.

## Auth precedence

1. `HF_TOKEN` env var (highest)
2. Stored token (`hf auth login`)
3. Interactive prompt (fallback)

For automation scripts, always set `HF_TOKEN` explicitly:

```bash
export HF_TOKEN="hf_..."
hf models list --author Nanthasit  # uses HF_TOKEN automatically
```

## `hf upload` — PATH_IN_REPO Required For Rename

**Pitfall:** `hf upload REPO_ID LOCAL_PATH` uploads the file **with its local filename**, not `README.md`.

This is the most common mistake — uploading a locally-named file expecting it to become `README.md`:

```bash
# ❌ Wrong — creates coder-readme.md instead of README.md
hf upload user/model ./coder-readme.md

# ✅ Correct — explicitly set PATH_IN_REPO
hf upload user/model ./coder-readme.md README.md
```

**Rule:** When the remote filename should differ from the local filename, pass `PATH_IN_REPO` as the third argument:

```bash
hf upload REPO_ID LOCAL_PATH [PATH_IN_REPO]
```

Also use `--commit-message "..."` to set a descriptive commit title.

**Cleanup:** If you accidentally uploaded a file, delete it with a separate commit using `hf upload` with `--delete`:

```bash
hf upload user/model . --delete wrong-name.md --commit-message "Remove accidental file"
```

Note: `--delete` requires a `local_path` argument (`.` or any valid directory), and may upload local files if not careful. Prefer `hf repos delete-files` or `HfApi.delete_file()` for precise removal.
