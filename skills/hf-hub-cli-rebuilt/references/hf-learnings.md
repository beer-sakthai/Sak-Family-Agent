# HF CLI Rebuilt: huggingface_hub v1.22–v1.24

**Skill name:** `hf-hub-cli-rebuilt`
**author:** SakThai
**license:** MIT

Covers the major CLI and API changes in huggingface_hub releases v1.22.0 (2026-07-03), v1.23.0 (2026-07-09), and v1.24.0 (2026-07-17).

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

## CLI Command Tree (Post-Rebuild)

```
hf
├── auth            login / logout / whoami / switch / token / list
├── buckets         cp / create / delete / info / list / move / remove / sync
├── cache           list / prune / rm / verify
├── collections     add-item / create / delete / delete-item / info / list / update / update-item
├── cp              (copy files via hf:// URIs)
├── datasets        card / info / leaderboard / list
├── discussions     edit / list
├── download        (single file, repo, revision, hf:// URI, dry-run, quiet)
├── endpoints       (inference endpoints)
├── env
├── extensions      update
├── jobs            ls / run / uv-run / ssh / scheduled / labels / wait / logs / cancel / ps
├── lfs-enable-largefiles
├── lfs-multipart-upload
├── models          list / info / card
├── papers          list / info
├── repos           create / delete / move / list
├── sandbox         create / exec / cp / kill / spawn / list / logs / proxy
├── skills          add / list
├── spaces          templates / list / info
└── upload          (folder, file, hf:// URI, regular-interval, commit-msg, PR)
```

## Code Patterns

### Sandboxes
```python
from huggingface_hub import Sandbox

# Dedicated VM
with Sandbox.create(image="python:3.12") as sbx:
    sbx.files.write("/app/main.py", "print(40 + 2)")
    print(sbx.run("python /app/main.py").stdout)  # 42

# Background process + port proxy
sbx = Sandbox.create(image="python:3.12")
proc = sbx.run("python -m http.server 8080", background=True)
print(sbx.proxy_url_for(8080))  # https://<sandbox-id>.sandbox.hf.space:8080
```

### Space Templates
```bash
# List available templates
hf spaces templates
# Create a Space from a template
hf repos create my-jupyterlab --type space --template jupyterlab
```

```python
from huggingface_hub import create_repo
create_repo("my-jupyterlab", repo_type="space", space_template="jupyterlab")
```

### Job Naming (v1.24+)
```bash
hf jobs run --name training-v2 python:3.12 python train.py
hf jobs labels <job_id> --name training-v2
hf jobs scheduled run @hourly --name hourly-task python:3.12 python -c 'print("ok")'
```

```python
from huggingface_hub import run_job
run_job("python:3.12", command=["python", "train.py"], name="training-v2")
```

## Deprecations & Breaking
- `upload_large_folder` deprecated → use `upload_folder`/`hf upload`
- Pattern matching now case-sensitive on all platforms
- Dead inference providers removed (black-forest-labs, clarifai, hyperbolic, nebius, nvidia, sambanova)
- Jobs no longer Pro-only (v1.22)
