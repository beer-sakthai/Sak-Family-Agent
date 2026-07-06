#!/usr/bin/env bash
#
# evolve_agent.sh — Hermes self-evolution for the four sibling Telegram agents.
#
# Evolves ONE skill for ONE agent with DSPy + GEPA, then commits the evolved
# skill to that agent's OWN GitHub repo (one repo per agent) on a review branch
# and opens a PR. The live agent is left untouched unless you pass --apply.
#
#   agent     profile dir (HERMES_AGENT_REPO)          github repo
#   ------    --------------------------------------   -------------------------
#   hermes    ~/.hermes                                beer-sakthai/hermes-skills
#   sakthai   ~/.hermes/profiles/sakthai               beer-sakthai/sakthai-skills
#   saksee    ~/.hermes/profiles/saksee                beer-sakthai/saksee-skills
#   saksit    ~/.hermes/profiles/saksit                beer-sakthai/saksit-skills
#
# Usage:
#   ./evolve_agent.sh <hermes|sakthai|saksee|saksit> --skill <name> [opts...]
#   ./evolve_agent.sh saksit  --skill github-auth --iterations 8
#   ./evolve_agent.sh saksee  --skill arxiv --dry-run          # validate, $0 spend
#   ./evolve_agent.sh sakthai --skill arxiv --apply --merge    # evolve, apply live, auto-merge
#
# Flags handled by this wrapper:
#   --apply       also copy the evolved skill into the LIVE profile skills dir
#   --merge       auto-squash-merge the PR after pushing (default: open PR only)
#   --no-push     do everything locally; skip GitHub push/PR
#   --dry-run     passed through to evolve_skill (validate only, no API spend)
#   --bootstrap   only create the repo + push current skills as baseline, then exit
# Any other flag is forwarded verbatim to `python -m evolution.skills.evolve_skill`
# (e.g. --iterations, --optimizer-model, --eval-source, --run-tests).
#
# Env overrides: GH_OWNER (default beer-sakthai), HERMES_SKILLS_REPO_ROOT
# (default ~/hermes-agent-skills), GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL,
# REPO_VISIBILITY (private|public, default private).

set -euo pipefail

EVO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_REPO_ROOT="${HERMES_SKILLS_REPO_ROOT:-$HOME/hermes-agent-skills}"
GH_OWNER="${GH_OWNER:-beer-sakthai}"
GIT_NAME="${GIT_AUTHOR_NAME:-SakThai Agents}"
GIT_EMAIL="${GIT_AUTHOR_EMAIL:-gensandee@gmail.com}"
REPO_VISIBILITY="${REPO_VISIBILITY:-private}"

die() { echo "error: $*" >&2; exit 1; }

AGENT="${1:-}"; shift || true
case "$AGENT" in
  hermes)  PROFILE_REPO="$HOME/.hermes";                      REPO="hermes-skills";;
  sakthai) PROFILE_REPO="$HOME/.hermes/profiles/sakthai";     REPO="sakthai-skills";;
  saksee)  PROFILE_REPO="$HOME/.hermes/profiles/saksee";      REPO="saksee-skills";;
  saksit)  PROFILE_REPO="$HOME/.hermes/profiles/saksit";      REPO="saksit-skills";;
  *) echo "usage: $0 <hermes|sakthai|saksee|saksit> --skill <name> [opts]"; exit 2;;
esac
FULL_REPO="$GH_OWNER/$REPO"

APPLY=0; PUSH=1; MERGE=0; DRYRUN=0; BOOTSTRAP=0; SKILL=""; PASS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --apply)     APPLY=1;;
    --merge)     MERGE=1;;
    --no-push)   PUSH=0;;
    --bootstrap) BOOTSTRAP=1;;
    --dry-run)   DRYRUN=1; PASS+=("$1");;
    --skill)     SKILL="$2"; PASS+=("$1" "$2"); shift;;
    --skill=*)   SKILL="${1#*=}"; PASS+=("$1");;
    *)           PASS+=("$1");;
  esac
  shift
done

[ -d "$PROFILE_REPO/skills" ] || die "no skills dir at $PROFILE_REPO/skills"

# Never let agent secrets/state leak into a skills repo — only ship skill text.
RSYNC_EXCL=(--exclude='.env' --exclude='*.key' --exclude='*.pem'
            --exclude='auth*' --exclude='*token*' --exclude='*secret*'
            --exclude='__pycache__/' --exclude='.git/')

# ── ensure the per-agent GitHub repo exists with a `main` baseline ──────────
ensure_repo() {
  local local_dir="$SKILLS_REPO_ROOT/$AGENT"
  mkdir -p "$SKILLS_REPO_ROOT"
  if [ ! -d "$local_dir/.git" ]; then
    if gh repo view "$FULL_REPO" >/dev/null 2>&1; then
      gh repo clone "$FULL_REPO" "$local_dir" >/dev/null
    else
      git init -q -b main "$local_dir"
    fi
  fi
  ( cd "$local_dir"
    git config user.name "$GIT_NAME"; git config user.email "$GIT_EMAIL"
    git checkout -q main 2>/dev/null || git checkout -q -B main
    mkdir -p skills
    rsync -a --delete "${RSYNC_EXCL[@]}" "$PROFILE_REPO/skills/" skills/
    if [ -z "$(git status --porcelain)" ] && git rev-parse HEAD >/dev/null 2>&1; then
      :  # baseline already up to date
    else
      git add -A
      git commit -q -m "baseline: $AGENT skills snapshot" \
        -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" || true
    fi
    if [ "$PUSH" = 1 ]; then
      if ! gh repo view "$FULL_REPO" >/dev/null 2>&1; then
        gh repo create "$FULL_REPO" --"$REPO_VISIBILITY" \
          --description "Self-evolving Hermes skills for the $AGENT agent (GEPA)." >/dev/null
      fi
      git remote get-url origin >/dev/null 2>&1 || \
        git remote add origin "https://github.com/$FULL_REPO.git"
      git push -q -u origin main
    fi
  )
  echo "$local_dir"
}

# ── venv + framework deps (idempotent) ─────────────────────────────────────
# System python3 (3.14) has no working ensurepip here; prefer uv with py3.11.
setup_venv() {
  local venv="$EVO_DIR/.venv"
  if [ ! -d "$venv" ]; then
    if command -v uv >/dev/null 2>&1; then uv venv --python 3.11 "$venv" >/dev/null
    else python3 -m venv "$venv"; fi
  fi
  # shellcheck disable=SC1091
  source "$venv/bin/activate"
  if ! python -c "import dspy" 2>/dev/null; then
    if command -v uv >/dev/null 2>&1; then uv pip install -q -e "$EVO_DIR"'[dev]'
    else pip install -q -e "$EVO_DIR"'[dev]'; fi
  fi
}

LOCAL="$(ensure_repo)"
echo "[ok] $AGENT repo ready → $FULL_REPO ($LOCAL)"
[ "$BOOTSTRAP" = 1 ] && { echo "[bootstrap] baseline pushed; done."; exit 0; }

[ -n "$SKILL" ] || die "--skill <name> required (skip with --bootstrap to just sync the baseline)"

setup_venv
cd "$EVO_DIR"
echo "[run] evolving '$SKILL' for $AGENT (profile: $PROFILE_REPO)"
python -m evolution.skills.evolve_skill --hermes-repo "$PROFILE_REPO" "${PASS[@]}"

[ "$DRYRUN" = 1 ] && { echo "[dry-run] validated, nothing committed."; exit 0; }

# newest evolved variant for this skill
OUT="$(ls -dt "$EVO_DIR/output/$SKILL"/*/ 2>/dev/null | head -1 || true)"
EVOLVED="${OUT%/}/evolved_skill.md"
[ -f "$EVOLVED" ] || die "no evolved_skill.md under output/$SKILL/ (evolution may not have improved it); nothing to push"

# locate the live SKILL.md whose dir name == the skill name
LIVE_SKILL=""
while IFS= read -r f; do
  [ "$(basename "$(dirname "$f")")" = "$SKILL" ] && { LIVE_SKILL="$f"; break; }
done < <(find "$PROFILE_REPO/skills" -name SKILL.md)
[ -n "$LIVE_SKILL" ] || die "could not locate live SKILL.md for '$SKILL' under $PROFILE_REPO/skills"
REL="${LIVE_SKILL#"$PROFILE_REPO"/}"   # e.g. skills/github/github-auth/SKILL.md

# ── commit evolved skill to the agent repo on a review branch ───────────────
cd "$LOCAL"
rsync -a --delete "${RSYNC_EXCL[@]}" "$PROFILE_REPO/skills/" skills/   # refresh baseline
cp "$EVOLVED" "$LOCAL/$REL"                                            # overlay evolved variant
mkdir -p .evolution/"$SKILL"
cp "${OUT%/}/metrics.json"        ".evolution/$SKILL/metrics.json"        2>/dev/null || true
cp "${OUT%/}/baseline_skill.md"   ".evolution/$SKILL/baseline_skill.md"   2>/dev/null || true

BR="evolve/$SKILL-$(date +%Y%m%d-%H%M%S)"
git checkout -q -B "$BR"
git add -A
if git diff --cached --quiet; then echo "[skip] evolved variant identical to live skill; nothing to commit"; exit 0; fi
git commit -q -m "evolve($AGENT): $SKILL via GEPA" \
  -m "Evolved with DSPy+GEPA from hermes-agent-self-evolution. Review the diff before merge." \
  -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

if [ "$PUSH" = 1 ]; then
  git push -q -u origin "$BR"
  PR_URL="$(gh pr create --repo "$FULL_REPO" --head "$BR" --base main \
    --title "evolve: $SKILL" \
    --body "Automated GEPA evolution of \`$SKILL\` for **$AGENT**. See \`.evolution/$SKILL/metrics.json\` for fitness deltas. Review the diff before merging." \
    2>/dev/null || true)"
  echo "[pr] ${PR_URL:-opened}"
  if [ "$MERGE" = 1 ]; then
    gh pr merge "$BR" --repo "$FULL_REPO" --squash --delete-branch || echo "[warn] auto-merge failed; merge manually"
  fi
else
  echo "[local] committed on $BR (no push)"
fi

if [ "$APPLY" = 1 ]; then
  cp "$EVOLVED" "$LIVE_SKILL"
  echo "[apply] evolved '$SKILL' written into LIVE profile: $LIVE_SKILL"
fi
echo "[done] $AGENT / $SKILL"
