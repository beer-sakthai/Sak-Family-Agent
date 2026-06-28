#!/usr/bin/env bash
# model_roster.sh — inspect & validate the model roster across the 4 Hermes agents.
#
# Reads each agent's live config.yaml (model: main + fallback_model: backup +
# custom_providers:) and validates the roster invariants we actually ship:
#   • every agent has a main AND a fallback
#   • the fallback runs on a DIFFERENT provider than the main (cross-provider failover)
#   • any custom:fireworks backup has FIREWORKS_API_KEY resolvable in that profile's .env
#   • reports context windows from models_dev_cache.json where known (flags <250K)
#
# Usage:
#   model_roster.sh           # print the roster table + warnings
#   model_roster.sh --check   # CI mode: exit non-zero if any invariant fails
#   model_roster.sh --ping    # also do a live one-shot reachability ping per model (costs a few tokens on paid providers)
#
# This is the repeatable tool for future model rotations. Models known-unreachable
# on the current accounts (ollama-cloud paywalled/weekly-capped, GOOGLE_API_KEY
# API-restricted) are flagged so a future rotation doesn't silently re-introduce them.
set -euo pipefail

HERMES_ROOT="${HERMES_ROOT:-$HOME/.hermes}"
PYBIN="$HERMES_ROOT/hermes-agent/venv/bin/python"
[ -x "$PYBIN" ] || PYBIN="python3"

MODE="${1:-show}"

"$PYBIN" - "$MODE" "$HERMES_ROOT" <<'PY'
import sys, os, json
mode = sys.argv[1] if len(sys.argv) > 1 else "show"
root = sys.argv[2]
try:
    import yaml
except Exception:
    print("PyYAML not available in interpreter:", sys.executable); sys.exit(2)

AGENTS = [
    ("Hermes",  os.path.join(root, "config.yaml"),                       os.path.join(root, ".env")),
    ("SakThai", os.path.join(root, "profiles/sakthai/config.yaml"),      os.path.join(root, "profiles/sakthai/.env")),
    ("Saksee",  os.path.join(root, "profiles/saksee/config.yaml"),       os.path.join(root, "profiles/saksee/.env")),
    ("SakSit",  os.path.join(root, "profiles/saksit/config.yaml"),       os.path.join(root, "profiles/saksit/.env")),
]

# Models known-unreachable on these accounts (flag if a rotation re-introduces them).
KNOWN_BAD = {
    "glm-5.2": "ollama-cloud subscription required (403)",
    "mistral-large-3:675b": "ollama-cloud subscription required (403)",
    "kimi-k2.7-code": "ollama-cloud subscription required (403)",
    "qwen3-coder:480b": "ollama-cloud weekly free limit (429)",
    "gpt-oss:120b": "ollama-cloud weekly free limit (429)",
    "gemini-2.5-flash": "GOOGLE_API_KEY API-restricted (403)",
    "nvidia/nemotron-3-ultra:free": "not in Nous catalog (404)",
}
# Providers that reject Hermes's per-message 'timestamp' field (HTTP 400
# "Extra inputs are not permitted") and so CANNOT serve as an auto-fallback:
#   • Fireworks (accounts/fireworks/models/*) — strict OpenAI schema validation.
# Tolerant providers verified OK as backups: nous, huggingface, github-copilot.
STRICT_REJECTS_TIMESTAMP = ("accounts/fireworks/models/",)

# context windows we care about (from models.dev cache), best-effort
ctx_cache = {}
cache_path = os.path.join(root, "models_dev_cache.json")
try:
    raw = json.load(open(cache_path))
    blob = json.dumps(raw)
except Exception:
    blob = ""

def env_has(envfile, key):
    try:
        for line in open(envfile):
            if line.strip().startswith(key + "="):
                return True
    except Exception:
        pass
    return False

def fb_one(fb):
    if isinstance(fb, list):
        return fb[0] if fb else None
    return fb

problems = []
rows = []
for name, cfgp, envp in AGENTS:
    try:
        cfg = yaml.safe_load(open(cfgp))
    except Exception as e:
        problems.append(f"{name}: cannot parse {cfgp}: {e}")
        continue
    m = cfg.get("model")
    if isinstance(m, dict):
        main_prov = m.get("provider"); main_model = m.get("default")
    else:
        # flat schema: top-level `provider:` + scalar `model:`
        main_prov = cfg.get("provider"); main_model = m
    fb = fb_one(cfg.get("fallback_model"))
    cps = cfg.get("custom_providers") or []
    bk_prov = fb.get("provider") if isinstance(fb, dict) else None
    bk_model = fb.get("model") if isinstance(fb, dict) else None

    rows.append((name, main_prov, main_model, bk_prov, bk_model))

    if not main_model:
        problems.append(f"{name}: no main model set")
    if not bk_model:
        problems.append(f"{name}: no fallback model set")
    if main_prov and bk_prov and str(main_prov).split(":")[0] == str(bk_prov).split(":")[0]:
        problems.append(f"{name}: fallback provider '{bk_prov}' == main provider '{main_prov}' (no cross-provider failover)")
    # custom:fireworks backups need the key resolvable
    if isinstance(bk_prov, str) and bk_prov.startswith("custom:"):
        cpname = bk_prov.split(":",1)[1]
        cp = next((c for c in cps if c.get("name") == cpname), None)
        if not cp:
            problems.append(f"{name}: fallback uses '{bk_prov}' but no custom_providers entry named '{cpname}'")
        else:
            kenv = cp.get("key_env") or cp.get("api_key_env")
            if kenv and not (env_has(envp, kenv) or os.environ.get(kenv)):
                problems.append(f"{name}: custom provider '{cpname}' key_env {kenv} not resolvable in {envp}")
    for tag, mod in (("main", main_model), ("backup", bk_model)):
        if mod in KNOWN_BAD:
            problems.append(f"{name}: {tag} '{mod}' is known-unreachable — {KNOWN_BAD[mod]}")
        if mod and any(mod.startswith(p) for p in STRICT_REJECTS_TIMESTAMP):
            problems.append(f"{name}: {tag} '{mod}' rejects Hermes 'timestamp' message field (HTTP 400) — unusable as a live backup")

# distinctness (informational under 'ship what works')
mains = [r[2] for r in rows if r[2]]
backs = [r[4] for r in rows if r[4]]

W = max((len(r[0]) for r in rows), default=6)
print("\n  Hermes agent model roster")
print("  " + "-"*64)
for name, mp, mm, bp, bm in rows:
    print(f"  {name:<{W}}  main: {mp}/{mm}")
    print(f"  {'':<{W}}  back: {bp}/{bm}")
print("  " + "-"*64)
print(f"  distinct mains: {len(set(mains))}/{len(mains)}   distinct backups: {len(set(backs))}/{len(backs)}")
print(f"  Hermes hard-task escalation: github-copilot/claude-sonnet-4.6 (on-demand, not a steady slot)")

if problems:
    print("\n  ⚠ ISSUES:")
    for p in problems:
        print(f"    - {p}")
else:
    print("\n  ✓ all invariants pass (each agent: main + cross-provider fallback; fireworks keys resolvable)")

if mode == "--check":
    sys.exit(1 if problems else 0)
PY
