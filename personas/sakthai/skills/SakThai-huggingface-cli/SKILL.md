---
name: SakThai-huggingface-cli
description: "Use when working with Hugging Face Hub via the hf CLI — auth, upload, download, jobs, repos, endpoints, and SakThai pipeline operations."
---

# Hugging Face CLI (`hf`)

## Auth

```bash
hf auth login                          # Login with token
hf auth whoami                         # Show current user
hf auth list                           # List stored tokens
hf auth switch                         # Switch tokens
hf auth logout                         # Logout
```

## Repos & Files

```bash
hf repo create my-model                # Create model repo
hf repo create my-dataset --type dataset  # Create dataset repo
hf upload user/repo local/file remote/path    # Upload file
hf download user/repo remote/path      # Download file
hf repo-files list user/repo           # List repo files
```

## Inference

```bash
# Via HF Inference API (your custom models)
curl https://api-inference.huggingface.co/models/user/model \
  -H "Authorization: Bearer $(cat ~/.cache/huggingface/token)" \
  -d '{"inputs":"Hello"}'

# Via Inference Providers (supported models)
curl https://router.huggingface.co/hf/v1/chat/completions \
  -H "Authorization: Bearer $(cat ~/.cache/huggingface/token)" \
  -d '{"model":"microsoft/Phi-4","messages":[{"role":"user","content":"Hi"}]}'
```

## Jobs (SakThai Automation)

```bash
hf jobs run --config .opencode/scripts/sakthai-jobs.yaml  # Run all jobs
hf jobs list                                                # List running jobs
hf jobs logs <job-id>                                       # View job logs
```

## Endpoints

```bash
hf endpoints list                        # List inference endpoints
hf endpoints create --name my-endpoint --model user/model
hf endpoints delete my-endpoint
```

## SakThai Pipeline Commands

From opencode TUI:
- `/sakthai` — full pipeline (health → eval → cards)
- `/sakthai-eval` — run benchmark eval
- `/sakthai-health` — health check
- `/sakthai-cards` — update model cards
- `/sakthai-bench-v3` — generate v3 benchmark

Or from bash:
```bash
bash .opencode/scripts/sakthai-do-all.sh --publish
# Or per-step:
uv run .opencode/scripts/run-eval.py --model Nanthasit/sakthai-context-1.5b-merged --publish
uv run .opencode/scripts/health-check.py --publish
uv run .opencode/scripts/update-model-cards.py
uv run .opencode/scripts/run-benchmark-v3.py
```

## Env & Debug

```bash
hf env                                 # Print environment info
hf version                             # Print version
hf cache                               # Manage cache
