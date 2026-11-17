#!/usr/bin/env bash
# Initialize the Sak-Family-Agent repository structure safely.
# Default: create missing directories and validate required files.
# Optional: --runtime creates empty per-agent runtime directories; --bootstrap
# delegates dependency installation and doctor checks to scripts/bootstrap.sh.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK_ONLY=0
INIT_RUNTIME=0
RUN_BOOTSTRAP=0

usage() {
    cat <<'EOF'
Usage: scripts/initialize_repository.sh [options]

Initialize or validate the Sak-Family-Agent repository structure.

Options:
  --check       Validate only; do not create directories or runtime paths.
  --runtime     Create empty ~/.sakthai/<persona>/ runtime directories.
  --bootstrap   Run the existing scripts/bootstrap.sh after structure checks.
  -h, --help    Show this help.

The script never overwrites tracked files, .env, persona definitions, memory
 databases, or configuration. Dependency installation is opt-in via --bootstrap.
EOF
}

for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY=1 ;;
        --runtime) INIT_RUNTIME=1 ;;
        --bootstrap) RUN_BOOTSTRAP=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: unknown option: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

cd "$ROOT_DIR"

PERSONAS=(sakthai sakking saksee saksit saktan sakjules)
REQUIRED_DIRS=(
    "app"
    "apps"
    "automation"
    "data"
    "docs"
    "docs/images"
    "docs/images/personas"
    "docs/images/personas/realistic"
    "docs/schemas"
    "docs/soul-templates"
    "infra"
    "personas"
    "personas/shared"
    "scripts"
    "services"
    "tests"
    "training"
    "build/personas"
    "build/agent-repos"
)
REQUIRED_FILES=(README.md Makefile pyproject.toml .gitignore)

info() { printf '[initialize] %s\n' "$*"; }
warn() { printf '[initialize] WARNING: %s\n' "$*" >&2; }
fail() { printf '[initialize] ERROR: %s\n' "$*" >&2; exit 1; }

ensure_dir() {
    local path="$1"
    if [[ -d "$path" ]]; then
        return 0
    fi
    if (( CHECK_ONLY )); then
        warn "missing directory: $path"
    else
        mkdir -p "$path"
        info "created directory: $path"
    fi
}

check_file() {
    local path="$1"
    [[ -f "$path" ]] || fail "required file missing: $path"
}

info "repository root: $ROOT_DIR"
[[ -f .git/HEAD ]] || fail "run this script from a Git checkout"

for dir in "${REQUIRED_DIRS[@]}"; do
    ensure_dir "$dir"
done

for file in "${REQUIRED_FILES[@]}"; do
    check_file "$file"
done

for persona in "${PERSONAS[@]}"; do
    persona_root="personas/$persona"
    [[ -d "$persona_root" ]] || fail "persona directory missing: $persona_root"
    for file in SOUL.md PLAN.md CYCLE.md MEMORY.md HANDOFF.md BACKPACK.md; do
        check_file "$persona_root/$file"
    done
    for file in config/config.yaml config/mcp.json config/workspace.yaml; do
        check_file "$persona_root/$file"
    done
done

if (( INIT_RUNTIME )); then
    [[ -n "${HOME:-}" ]] || fail "HOME is not set; cannot initialize runtime directories"
    runtime_root="${SAKTHAI_HOME:-$HOME/.sakthai}"
    if (( CHECK_ONLY )); then
        info "runtime check requested: $runtime_root"
        for persona in "${PERSONAS[@]}"; do
            [[ -d "$runtime_root/$persona" ]] || warn "missing runtime directory: $runtime_root/$persona"
        done
    else
        mkdir -p "$runtime_root"
        chmod 700 "$runtime_root"
        for persona in "${PERSONAS[@]}"; do
            mkdir -p "$runtime_root/$persona"
            chmod 700 "$runtime_root/$persona"
        done
        info "initialized empty runtime directories under $runtime_root"
        info "no memory databases, credentials, or secrets were created"
    fi
fi

if (( CHECK_ONLY )); then
    if find . -maxdepth 1 -type f -name '.env' -print -quit | grep -q .; then
        info "existing .env preserved"
    elif [[ -f .env.example ]]; then
        warn ".env is absent; copy .env.example manually if needed"
    fi
    info "structure validation completed"
    exit 0
fi

if [[ ! -f .env && -f .env.example ]]; then
    cp .env.example .env
    chmod 600 .env
    warn "created .env from .env.example; review it before adding credentials"
fi

if (( RUN_BOOTSTRAP )); then
    info "delegating dependency setup to scripts/bootstrap.sh"
    ./scripts/bootstrap.sh
else
    info "structure initialization completed"
    info "next step: ./scripts/initialize_repository.sh --check"
    info "optional dependency setup: ./scripts/initialize_repository.sh --bootstrap"
fi
