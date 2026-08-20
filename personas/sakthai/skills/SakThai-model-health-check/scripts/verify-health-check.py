#!/usr/bin/env python3
"""Ad-hoc verification for a health-check YAML after upload to HF Hub.
Usage:
    uv run python3 scripts/verify-health-check.py <local_yaml_path> <model_id> [expected_downloads]

Exits 0 on all-pass, 1 on any failure. Prints a checkmark report.

Supports five YAML schemas (auto-detected by top-level keys):
  - NEW schema (2026-07+): metadata, core_metrics, model_artifacts|file_inventory, health_score (LLM/TTS/embedding variants)
  - OLD schema (pre-2026-07): target_model, popularity, files, card_content, assessment
  - SLIM schema (LoRA adapter): health_check, usage, base_model, files, card_metadata, tags_count
  - GENERIC schema (sakthai-model-health-check cron): model, metadata, age, popularity, repo_content, assessment
  - LLM_CRON schema (text-generation cron): target_model, architecture, repo_summary, benchmarks, card_quality, health_score, sibling_comparison, eval_metadata

Requires pyyaml (via uv) for full YAML validation. Falls back to
line-grep if unavailable.
"""

import json, os, sys, urllib.request, urllib.error

LOCAL_PATH = sys.argv[1] if len(sys.argv) > 1 else None
MODEL_ID = sys.argv[2] if len(sys.argv) > 2 else None
EXPECTED_DL = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else None

errors = []

# --- 1. Local file ---
if LOCAL_PATH:
    if not os.path.exists(LOCAL_PATH):
        errors.append(f"NOT_FOUND: {LOCAL_PATH}")
    else:
        sz = os.path.getsize(LOCAL_PATH)
        if sz < 500:
            errors.append(f"TOO_SMALL: {sz}B")
        print(f"1/5 local file: {sz}B")

# --- 2. YAML validity + required keys ---
SCHEMA = None  # 'slim', 'new', 'old', or 'generic' after detection

if LOCAL_PATH and not errors:
    try:
        import yaml
        with open(LOCAL_PATH) as f:
            d = yaml.safe_load(f)

        # Detect schema by checking for new-style top-level keys
        if 'metadata' in d and 'core_metrics' in d:
            SCHEMA = 'new'
            # Embedding variant: uses file_inventory instead of model_artifacts
            if 'file_inventory' in d or 'model_artifacts' in d:
                required_keys = ['metadata', 'core_metrics', 'health_score']
            else:
                required_keys = ['metadata', 'core_metrics', 'health_score', 'model_artifacts']
        elif 'health_check' in d:
            SCHEMA = 'slim'
            required_keys = ['health_check', 'usage', 'base_model', 'files', 'card_metadata', 'tags_count']
        elif 'target_model' in d and 'health_score' in d and 'sibling_comparison' in d:
            # llm_cron: text-generation cron schema with componentized health_score and sibling comparison.
            # Detected BEFORE plain 'target_model' check because both have target_model,
            # but llm_cron has health_score where old schema has assessment.
            SCHEMA = 'llm_cron'
            required_keys = ['target_model', 'architecture', 'repo_summary', 'benchmarks',
                             'card_quality', 'health_score', 'sibling_comparison', 'eval_metadata']
        elif 'target_model' in d:
            SCHEMA = 'old'
            required_keys = ['target_model', 'popularity', 'files', 'card_content',
                             'architecture', 'multimodal', 'assessment', 'eval_metadata']
        elif 'model' in d and 'assessment' in d and 'popularity' in d:
            SCHEMA = 'generic'
            required_keys = ['model', 'timestamp', 'metadata', 'age', 'popularity', 'repo_content', 'assessment']
        else:
            required_keys = []

        for k in required_keys:
            if k not in d or d[k] is None:
                errors.append(f"MISSING_KEY: {k}")
        if not errors:
            print(f"2/5 yaml valid ({SCHEMA or 'generic'} schema): {required_keys}")
    except ImportError:
        # pyyaml not available — fallback to grep
        print("2/5 yaml: pyyaml unavailable, grep fallback")
        for k in ['metadata:', 'core_metrics:', 'model_artifacts:', 'benchmarks:', 'health_score:',
                   'health_check:', 'usage:', 'base_model:', 'tags_count:',
                   'target_model:', 'popularity:', 'assessment:',
                   'model:', 'age:', 'repo_content:',
                   'architecture:', 'repo_summary:', 'card_quality:', 'sibling_comparison:', 'eval_metadata:']:
            with open(LOCAL_PATH) as f:
                if not any(k in line for line in f):
                    errors.append(f"MISSING_SECTION: {k}")
    except Exception as e:
        errors.append(f"YAML_ERROR: {e}")

# --- 3. Model identity ---
def _get_identity_and_score(d, schema):
    """Extract model identity and score from any schema. Returns (model_id, score, scale_str)."""
    if schema == 'new':
        mid = d.get('metadata', {}).get('model_id', '') or (d.get('model') if isinstance(d.get('model'), str) else d.get('model', {}).get('id', ''))
        raw_score = d.get('health_score', -1)
        if isinstance(raw_score, dict):
            score = raw_score.get('overall', raw_score.get('weighted_score', -1))
        else:
            score = raw_score
        scale = '100' if isinstance(raw_score, dict) and raw_score.get('overall', 0) > 10 else '10'
        return mid, score, scale
    elif schema == 'old':
        mid = d.get('target_model', {}).get('id', '')
        score = d.get('assessment', {}).get('score', 0)
        return mid, score, str(type(d.get('assessment', {}).get('score', 0)).__name__)
    elif schema == 'slim':
        hc = d.get('health_check', {})
        mid = hc.get('model_id', '')
        score = hc.get('score', 0)
        return mid, score, '100'
    elif schema == 'generic':
        mid = d.get('model', '')
        raw = d.get('assessment', {})
        status = raw.get('status', '?')
        score = raw.get('score', 0)
        return mid, status, 'GREEN/RED scale'
    elif schema == 'llm_cron':
        mid = d.get('target_model', {}).get('id', '')
        hs = d.get('health_score', {})
        score = hs.get('overall') if hs.get('overall') is not None else hs.get('final_score', 0)
        return mid, score, '100'
    else:
        return d.get('model') or d.get('target_model', {}).get('id', ''), None, '?'

if LOCAL_PATH and not errors and 'yaml' in sys.modules:
    mid, score, scale = _get_identity_and_score(d, SCHEMA)
    if MODEL_ID and mid != MODEL_ID:
        errors.append(f"ID_MISMATCH: {mid} != {MODEL_ID}")
    print(f"3/5 identity: {mid} | assessment={score}/{scale}" if MODEL_ID else f"3/5 identity: assessment={score}/{scale}")

# --- 4. Value sanity ---
def _get_metrics(d, schema):
    """Extract download count and file size from any schema."""
    if schema == 'new':
        dl = d.get('core_metrics', {}).get('downloads', 0)
        arts = d.get('model_artifacts', d.get('file_inventory', {}))
        if isinstance(arts, list):
            weight = next((a for a in arts if 'safetensors' in a.get('path','') or 'gguf' in a.get('path','') or 'bin' in a.get('path','')), {})
            size = weight.get('size_bytes', 0) or arts[0].get('size_bytes', 0) if arts else 0
        elif isinstance(arts, dict):
            size = arts.get('model_file_size_bytes', 0) or arts.get('model_safetensors_bytes', 0)
        else:
            size = 0
        return dl, size
    elif schema == 'llm_cron':
        tm = d.get('target_model', {})
        rs = d.get('repo_summary', {})
        dl = tm.get('downloads', 0) or rs.get('downloads', 0)
        total_gb = rs.get('total_gb', 0)
        size = int(total_gb * 1024**3)
        return dl, size
    elif schema == 'old':
        pop = d.get('popularity', {})
        files = d.get('files', {})
        size = files.get('gguf_weight_size_bytes', 0) or files.get('total_weight_bytes', 0)
        return pop.get('downloads', 0), size
    elif schema == 'slim':
        usage = d.get('usage', {})
        f = d.get('files', {})
        return usage.get('downloads', 0), f.get('total_size_bytes', 0) or f.get('total_size_mb', 0) * 1024 * 1024
    elif schema == 'generic':
        pop = d.get('popularity', {})
        rc = d.get('repo_content', {})
        return pop.get('downloads', 0), rc.get('model_weights_total_bytes', 0) or rc.get('total_repo_bytes', 0)
    else:
        return 0, 0

if LOCAL_PATH and not errors and 'yaml' in sys.modules:
    dl, size = _get_metrics(d, SCHEMA)
    if EXPECTED_DL is not None and dl != EXPECTED_DL:
        errors.append(f"DL_MISMATCH: {dl} != {EXPECTED_DL}")
    # Size may legitimately be 0 for day-zero models (< 24h) or skeleton repos (no weights)
    # Skip this check when core_metrics.has_weights is false (new schema) or model_type is skeleton
    is_skeleton = False
    if SCHEMA == 'new':
        cm = d.get('core_metrics', {})
        if cm.get('has_weights') is False or 'skeleton' in str(cm.get('model_type', '')).lower():
            is_skeleton = True
    elif SCHEMA == 'old':
        tm = d.get('target_model', {})
        if tm.get('model_type') == 'skeleton' or tm.get('weight_status') == 'MISSING':
            is_skeleton = True
    if size <= 0 and SCHEMA and SCHEMA != 'generic' and not is_skeleton:
        errors.append("MODEL_FILE_SIZE_ZERO")
    print(f"4/5 values: dl={dl} size={size}B" + (" (day-zero, expected)" if size <= 0 else ""))

# --- 5. HF Hub accessibility ---
if MODEL_ID and not errors:
    token = os.environ.get('HF_TOKEN', '')
    if not token:
        try:
            token = open(os.path.expanduser('~/.cache/huggingface/token')).read().strip()
        except:
            pass
    # Infer remote repo path from local path.
    # Files under .eval_results/ or other repo subdirs must keep that prefix
    # when checking the remote URL — os.path.basename strips it, causing 404.
    if LOCAL_PATH:
        for prefix in ['.eval_results/', 'eval_results/']:
            if prefix in LOCAL_PATH:
                idx = LOCAL_PATH.index(prefix)
                remote_path = LOCAL_PATH[idx:]
                break
        else:
            remote_path = os.path.basename(LOCAL_PATH)
    else:
        remote_path = ".eval_results/health-check.yaml"
    url = f"https://huggingface.co/{MODEL_ID}/raw/main/{remote_path}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        if resp.status != 200:
            errors.append(f"HF_HTTP_{resp.status}")
        cl = resp.headers.get('Content-Length', '?')
        print(f"5/5 hf hub: HTTP {resp.status} ({cl}B)")
    except urllib.error.HTTPError as e:
        errors.append(f"HF_HTTP_{e.code}: {url}")
    except Exception as e:
        errors.append(f"HF_NETWORK: {e}")

# --- Report ---
print()
if errors:
    print(f"FAIL ({len(errors)}):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("PASS")
