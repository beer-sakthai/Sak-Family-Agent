# Sak-Family-Agent Repository Initialization Roadmap

**Status:** Draft implementation plan  
**Initializer:** [`scripts/initialize_repository.sh`](../scripts/initialize_repository.sh)  
**Existing dependency bootstrap:** [`scripts/bootstrap.sh`](../scripts/bootstrap.sh)

## Objective

Initialize a clean or partially provisioned Sak-Family-Agent checkout without overwriting persona definitions, memory databases, credentials, generated assets, or user configuration. The process must be repeatable on a new development machine and safe to rerun after an interrupted setup.

The deployment boundary is intentionally split:

- `initialize_repository.sh` creates missing repository directories and validates the expected six-agent structure.
- `bootstrap.sh` remains the owner of Python environment installation, `.env` seeding, and `sakthai doctor`.
- Runtime databases, credentials, external services, Telegram fleet processes, and dashboard deployment are opt-in follow-up operations.

## Phase 0 — Preflight and safety

**Goal:** Confirm that initialization is happening in the intended checkout.

```bash
git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
cd Sak-Family-Agent
git status --short --branch
./scripts/initialize_repository.sh --check
```

Acceptance criteria:

- The current directory is a Git checkout.
- `README.md`, `Makefile`, `pyproject.toml`, and `.gitignore` exist.
- All six persona directories exist.
- Each persona has `SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, `BACKPACK.md`, and the expected config files.
- No files are changed by `--check`.

If the check reports an unexpected repository state, stop and resolve it before running setup. Do not use `git clean`, `git reset --hard`, or a broad overwrite to repair initialization.

## Phase 1 — Initialize repository structure

**Goal:** Create only missing directories required by the repository layout.

```bash
./scripts/initialize_repository.sh
```

The initializer creates missing paths such as:

- `app/`, `apps/`, `automation/`, `data/`, `infra/`, `services/`, `training/`, and `tests/`
- `docs/images/personas/realistic/`, `docs/schemas/`, and `docs/soul-templates/`
- `build/personas/` and `build/agent-repos/`
- `personas/shared/` and `scripts/`

It does not overwrite any existing file and does not create memory databases or secrets.

## Phase 2 — Optional local runtime directories

**Goal:** Prepare private, empty per-agent runtime directories without inventing state.

```bash
./scripts/initialize_repository.sh --runtime
```

This creates:

```text
${SAKTHAI_HOME:-$HOME/.sakthai}/
├── sakthai/
├── sakking/
├── saktan/
├── saksee/
├── saksit/
└── sakjules/
```

The directories are created with mode `700`. The command does not create SQLite databases, credentials, tokens, or memory records. The runtime should create those through the normal CLI initialization path.

## Phase 3 — Install the reproducible Python environment

**Goal:** Install the package and development dependencies using the repository’s existing bootstrap owner.

```bash
./scripts/initialize_repository.sh --bootstrap
```

The delegated bootstrap performs these checks and actions:

1. Requires Python 3.11 or newer.
2. Requires `uv`.
3. Installs the editable package with development extras.
4. Creates `.env` from `.env.example` only when `.env` is absent.
5. Runs `sakthai doctor`.

Review `.env` locally. Never commit API keys, refresh tokens, memory databases, or client data.

## Phase 4 — Validate persona composition and repository quality

**Goal:** Confirm that the six-agent structure is internally usable before starting services.

```bash
./scripts/initialize_repository.sh --check
make compose-personas
make lint
make test
uv run mypy personas/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai
```

For a fast smoke check before the full suite:

```bash
uv run pytest tests/test_persona_structure_parity.py tests/test_repo_hygiene.py
uv run python scripts/diagnose_personas.py
```

Acceptance criteria:

- Persona structure parity passes.
- Composed skill trees are written only to `build/personas/`.
- Lint, tests, typing, and security checks meet repository gates.
- No generated build output or local credentials are staged unintentionally.

## Phase 5 — Initialize memory and agent identity

**Goal:** Let the runtime create agent state through supported commands rather than manual database manipulation.

Recommended order:

1. Initialize or verify SakThai’s core runtime and family-memory access.
2. Verify each per-agent memory shard can be read through `sakthai memory family`.
3. Record the current charge report, household charge summary, conservation mode, and deputy-chain state.
4. Run a read-only status check for each persona.
5. Record a first `cycle-interrupted` or `cycle-complete` state only when an actual cycle exists; do not fabricate history.

Validation examples:

```bash
sakthai doctor --json
sakthai status
sakthai memory family --tag charge-report --limit 20
sakthai memory family --tag deputy-chain --limit 5
sakthai eval personas
```

## Phase 6 — Enable optional services one at a time

**Goal:** Deploy external or long-running services only after local validation.

| Service | Owner | Prerequisites | Verification |
|---|---|---|---|
| Next.js dashboard | SakKing / repository owner | Python API and Node.js 22+ | `make dashboard-test`; then `make dashboard-dev` locally |
| Telegram fleet | SakJules | Reviewed env templates, tokens, systemd unit, approval | `scripts/verify_vm_telegram_agents.py` |
| Hugging Face inference endpoint | SakThai + SakJules | Budget, model, security review, explicit approval | Endpoint smoke test and `sakthai doctor --json` |
| Cron or GitHub schedules | SakTan → SakJules | `schedule-request` with reason and rollback | `schedule-confirmed` record plus dry run |
| External MCP servers | Owning persona | Pinned version, allowlist, credential isolation | MCP ping/tool discovery without secret exposure |

Do not enable all services in one step. Each service should have a clear owner, rollback path, health check, and durable handoff record.

## Phase 7 — Operational handoff and rollback

**Goal:** Leave the repository in a recoverable state for the next agent or operator.

Before declaring initialization complete:

- Run `git status --short` and review every untracked file.
- Confirm no `.env`, token, database, or client-data file is staged.
- Save the initialization result, validation commands, failures, and next action to the appropriate operator notes or handoff record.
- If a service failed, preserve logs and write a resumable checkpoint; do not repeatedly retry an external service without diagnosing the root cause.
- To roll back repository-only initialization, remove only empty directories created by the initializer. Do not delete runtime databases, user data, or generated artifacts automatically.

## One-command safe path

For a fresh checkout that already has Python and `uv` available:

```bash
./scripts/initialize_repository.sh \
  && ./scripts/initialize_repository.sh --check \
  && ./scripts/initialize_repository.sh --bootstrap \
  && make compose-personas \
  && uv run pytest tests/test_persona_structure_parity.py tests/test_repo_hygiene.py
```

For a structure-only validation in CI or a restricted environment:

```bash
./scripts/initialize_repository.sh --check
```

## Definition of done

Initialization is complete when:

- The repository structure validates without missing required paths or persona files.
- Python dependencies are installed only when explicitly requested and `sakthai doctor` passes.
- The six personas can be composed and their structure/parity checks pass.
- Local runtime directories, if requested, are private and empty of fabricated state.
- Optional services have not been enabled without owner, approval, health check, and rollback instructions.
- The final Git diff contains only intentional documentation, script, or generated-output changes.
