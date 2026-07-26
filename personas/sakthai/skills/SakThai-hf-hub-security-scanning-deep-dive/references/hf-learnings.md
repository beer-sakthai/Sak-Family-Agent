# HF Learnings — Hugging Face Hub Security Scanning Deep Dive

## 2026-07-25: hf-hub-security-scanning-deep-dive — Hub Security Scanning Architecture and Workflows (Topic #185)

### Summary

Deep dive into Hugging Face Hub's security scanning infrastructure — the automated pipeline that scans every model, dataset, and Space upload for malware, secrets, unsafe content, and license violations. Covers the four scanning layers (Pickle scanning, ClamAV antivirus, secrets detection, safety moderation), how scan results are displayed as badges on repo pages, API access to scan status, handling of scan failures and false positives, and best practices for secure model publishing. This is critical knowledge for anyone publishing or consuming models on the Hub, especially in the context of supply chain security.

---

### 1. Scanning Architecture Overview

The Hub's security scanning operates as a multi-layered pipeline that activates on every upload (push/commit) to any model, dataset, or Space repository:

```
Upload → Pickle Scan → ClamAV Scan → Secrets Scan → Safety Moderation → Badge Updates
   │         │              │              │                │
   │    .pkl/.pt/      All files      Config files,     Image/text    Repo page
   │    .bin/.h5                      .env, code        content       badges
   ▼
Quarantine (if critical) or Warning (if moderate)
```

**Key principles:**
- Scanning is **automatic** — no opt-out for public repos
- Results are **publicly visible** as badges on repo pages
- Critical findings (confirmed malware) trigger **automatic quarantine** (repo hidden from searches, downloads blocked until resolved)
- Low/moderate findings show as **warnings** — repo remains accessible but flagged
- Scanning runs on **every commit** — not just initial upload

---

### 2. Detection Layers

#### 2.1 Pickle Malware Scanning

**What it scans:** All files with pickle-related extensions: `.pkl`, `.pt`, `.pth`, `.bin`, `.h5`, `.joblib`, `.pickle`

**Why it matters:** Python's pickle format allows arbitrary code execution during deserialization. Malicious pickle files can execute system commands, steal credentials, or install backdoors when loaded with `torch.load()`, `pickle.load()`, or `joblib.load()`.

**Detection method:** Uses **PickleScan** (open-source tool from Trail of Bits, integrated as `picklescan` library). PickleScan statically analyzes pickle opcodes without executing them, detecting dangerous patterns:

- `REDUCE` opcodes with `os.system`, `subprocess.call`, `__import__`
- `GLOBAL` opcodes referencing `builtins.exec`, `builtins.__import__`
- Suspicious `STACK_GLOBAL` patterns
- Known CVE patterns in pickle serialization

**Output:** Severity rating (CRITICAL, HIGH, MEDIUM, LOW) + list of detected dangerous opcodes with line references.

**Handling:**
| Severity | Action |
|----------|--------|
| CRITICAL | Repo quarantined — hidden from search, downloads blocked. Owner notified via email + Hub notification |
| HIGH | Repo flagged with visible warning badge. Downloads still allowed but users warned |
| MEDIUM | Warning badge shown. May be suppressed if model is from trusted author |
| LOW | Logged internally. No visible badge unless accumulated with other findings |

#### 2.2 ClamAV Antivirus Scanning

**What it scans:** All uploaded files — model weights, config files, documentation, images, archives

**Detection method:** **ClamAV** (open-source antivirus engine) with up-to-date virus definitions. Scans file contents for known malware signatures, trojans, worms, and other malicious patterns.

**Output:** Clean / Infected (with virus name if detected)

**False positives:** ClamAV can flag model weight files that statistically resemble known malware signatures (especially compressed formats). Common false positives:
- `.safetensors` files with specific weight distributions
- Archives (`.zip`, `.tar.gz`) containing model files
- Pickle files with legitimate but complex opcode sequences

**Handling:** Infected files trigger quarantine. False positives can be reported through Hub support (reviewed within 1-2 business days).

#### 2.3 Secrets Detection

**What it scans:** Configuration files, `.env` files, code files, documentation, Jupyter notebooks, and any text-based file

**Detection method:** Regex-based pattern matching for common credential formats:

| Pattern | Examples Detected |
|---------|------------------|
| `hf_...` | Hugging Face API tokens |
| `sk-...` | OpenAI API keys |
| `ghp_...`, `gho_...` | GitHub personal access tokens |
| `AKIA...` | AWS access keys |
| `-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----` | SSH/RSA private keys |
| `password=...` (in config files) | Plain-text passwords |
| `SLACK_BOT_TOKEN=...` | Slack tokens |
| `DISCORD_TOKEN=...` | Discord bot tokens |
| Generic `Bearer ` patterns | JWT and auth tokens |
| Database connection strings | `postgresql://user:pass@...`, `mongodb://...` |

**Output:** List of detected secrets with file paths and line numbers. Secrets are **automatically redacted** from public view — the file remains but the secret value is replaced with `[REDACTED]` strings in the Hub viewer.

**Important:** Redaction only affects the Hub's file viewer and API responses (when fetching raw content through Hub APIs). The actual committed file in Git LFS/object storage still contains the secret. Users must **rotate compromised credentials** and re-upload cleaned files.

#### 2.4 Safety Moderation

**What it scans:** Repository metadata (README, model card, dataset card), uploaded images, and file names

**Detection method:**
- **Text:** Automated content moderation for hate speech, harassment, violent content, sexual content, and spam
- **Images:** CSAM detection (hash-based matching against known databases), NSFW content flagging
- **CSAM hash matching:** Images are hashed and checked against the **National Center for Missing & Exploited Children (NCMEC)** hash database
- **Gated content:** Models/datasets containing sensitive content are flagged for **gating** — the author is prompted to add access restrictions

**Output:** Flagged / Clean. Flagged content may result in:
- Repo set to private
- Content removed (for CSAM — mandatory reporting to NCMEC)
- Author account restricted (repeated violations)
- Gating recommendation (for adult content not legal in all jurisdictions)

---

### 3. Security Badges on Repository Pages

Scan results are displayed as badges on every model/dataset/Space page:

| Badge | Meaning | Details |
|-------|---------|---------|
| ✅ **Pickle scan: OK** | No dangerous pickle opcodes detected | Normal for all clean models |
| ⚠️ **Pickle scan: Warning** | Suspicious opcodes found but below critical threshold | Review the scan report before loading |
| ❌ **Pickle scan: Danger** | Critical pickle exploit detected | Do NOT load this model — repo likely quarantined |
| ✅ **Antivirus: OK** | ClamAV scan passed | No malware signatures found |
| ⚠️ **Antivirus: Flagged** | ClamAV detected a potential threat | May be false positive — review |
| ✅ **Secrets: OK** | No credentials detected | Clean configuration |
| ⚠️ **Secrets: Found** | Credentials detected and redacted | Rotate the exposed credentials |
| ✅ **Safety: OK** | Content moderation passed | No policy violations |
| ⚠️ **Safety: Flagged** | Content requires review | May need gating or removal |

Badges link to detailed scan reports showing which files were flagged and why.

---

### 4. API Access to Scan Results

Scan results are accessible via the Hub API for automated pipelines and CI/CD:

```python
from huggingface_hub import HfApi

api = HfApi()

# Get scan status for a repo
repo_info = api.repo_info(
    repo_id="username/my-model",
    repo_type="model",
    expand=["securityScanStatus"]
)

# Access security scan info
security = repo_info.security_scan_status
print(f"Pickle scan: {security.pickle_scan.status}")   # "ok" | "warning" | "danger"
print(f"ClamAV scan: {security.clamav_scan.status}")   # "ok" | "flagged"
print(f"Secrets scan: {security.secrets_scan.status}")  # "ok" | "found"
print(f"S惡意 scan: {security.safety_scan.status}")      # "ok" | "flagged"

# Get detailed report URL
if hasattr(security, 'report_url'):
    print(f"Full report: {security.report_url}")
```

**REST API endpoint:**

```
GET https://huggingface.co/api/models/{repo_id}?expand[]=securityScanStatus
```

Returns the security scan information nested in the response.

---

### 5. Handling Scan Failures and False Positives

#### For Repository Owners

1. **Quarantined repo:** Your repo is hidden and downloads blocked. Follow the instructions in the email/notification to:
   - Review the scan report
   - Remove or fix flagged files
   - Request a re-scan (automatically triggers on next push)

2. **False positive:** If you believe a detection is incorrect:
   - Open a support ticket via https://huggingface.co/support
   - Include the repo ID, file path, and reason why it's a false positive
   - Hub security team reviews within 1-2 business days
   - For pickle false positives: Provide context about the opcode usage (e.g., "We use `__import__` for dynamic model architecture loading, documented here")

3. **Secrets redaction:**
   - Redaction is automatic and immediate
   - **CRITICAL:** Rotate the exposed credential immediately — redaction only hides it from the Hub viewer, the raw Git object still exists
   - Push a cleaned version of the file without the credential
   - Verify the redaction was applied successfully

4. **Preventing issues:**
   - Use `.safetensors` format instead of pickle — safetensors only stores tensor data, no code execution possible
   - Use `.gitignore` to exclude credential files from commits
   - Use environment variables or `.env` files that are `.gitignore`d
   - Add a `.gitattributes` file to properly handle large files with Git LFS

#### For Consumers (Downloading Models)

1. **Check badges before loading:** Always review security badges on the model page before loading
2. **Pickle warnings:** For models with pickle scan warnings:
   - Prefer `.safetensors` weights if available (compatible with most modern libraries)
   - Use `torch.load(..., weights_only=True)` (PyTorch 2.x+) to restrict pickle operations
   - Load in sandboxed/isolated environment first
3. **Handle quarantined repos:**
   - You cannot download from quarantined repos through normal means
   - If you need the model urgently, contact the author to resolve the scan issue
   - Never try to bypass quarantine (e.g., direct Git LFS download) — the issue exists for good reason

---

### 6. Best Practices for Secure Publishing

#### For Model Creators

| Practice | Why |
|----------|-----|
| **Use safetensors format** | Eliminates pickle-based code execution risk entirely |
| **Remove secrets before commit** | Use `git-secrets`, `talisman`, or pre-commit hooks |
| **Add `.gitignore` for credentials** | Prevents accidental `.env`/credentials file commits |
| **Use a `.gitattributes` file** | Ensures proper Git LFS handling for large weight files |
| **Pin dependencies in requirements** | Prevents supply-chain attacks via transitive dependencies |
| **Verify scan passes on CI** | Use Hub API to check scan status in your CI pipeline |
| **Respond to scan flags promptly** | Quarantined repos lose user trust and discoverability |
| **Document architecture decisions** | If using pickle for legitimate reasons, document why in README |

#### For Dataset Creators

| Practice | Why |
|----------|-----|
| **No executable content** | Avoid `.py`, `.sh`, `.exe` files in datasets |
| **Review image content** | Ensure no CSAM, NSFW, or violent imagery without proper gating |
| **Add license metadata** | Helps license compliance scanning and builds trust |
| **Use Parquet for tabular data** | Safer than pickle-based DataFrame formats |
| **Set appropriate gating** | Adult/controversial content should use gated repositories |

#### For Space Creators

| Practice | Why |
|----------|-----|
| **Scan dependencies for CVEs** | Use `pip-audit`, `safety`, or Dependabot |
| **Use Docker for isolation** | Recommended Space runtime for production apps |
| **Don't hardcode secrets** | Use Space Secrets (Settings → Repository Secrets) |
| **Pin base image versions** | Avoid `latest` tags in Dockerfiles for reproducible builds |
| **Enable auto-pause** | Reduces attack surface when Space is not in use |

---

### 7. Supply Chain Security Context

HF Hub's security scanning is part of a broader supply chain security strategy:

**For model consumers:**
- Scan badges provide immediate trust indicators
- Pickle scan prevents loading of trojaned models
- No additional tooling needed — Hub scanning is built-in

**For ecosystem security:**
- Hugging Face participates in the **OpenSSF** (Open Source Security Foundation)
- Model signing via cryptographic signatures is available for verified publishers
- Security advisories (similar to GitHub's) are displayed for affected repositories
- The Hub publishes transparency reports on security actions taken

**Relationship to other security measures:**
| Measure | Scope | Automated |
|---------|-------|:---------:|
| Security scanning | All uploads | ✅ |
| Gated repos | Author-defined | Manual |
| Model signing | Verified publishers | Semi-automated |
| Vulnerability advisories | Known CVEs | Report-driven |
| Sandbox execution (ZeroGPU/Sandboxes) | Inference | ✅ |
| Hardware isolation (Docker) | Spaces | Configurable |

---

### 8. Scan Status Lifecycle

```
Upload happens
     │
     ▼
Pending scan (badge shows "scanning...")
     │
     ├──► All scans pass → badges show ✅
     │
     ├──► Non-critical issue → badges show ⚠️ warnings
     │    Repo stays public
     │
     └──► Critical issue → badges show ❌
          Repo quarantined
          Owner notified
               │
               ├──► Owner fixes issue, re-uploads
               │    → Re-scan triggers automatically
               │
               └──► Owner appeals false positive
                    → Reviewed by security team
                    → If confirmed FP, repo un-quarantined
```

---

### 9. Key Takeaways

1. **Default to safetensors.** It's the only format that guarantees no code execution during model loading. Popular frameworks (Transformers, Diffusers, PEFT) all support it.

2. **Check badges before trust.** A model with a pickle scan warning might be benign, but it's worth understanding why before loading it into your production pipeline.

3. **Redaction ≠ removal.** If secrets were committed, the credential is still in the Git history. Rotate credentials first, then clean the file.

4. **Quarantine is reversible.** If your repo gets flagged, don't panic — fix the issue, push a clean version, and it will be re-scanned automatically.

5. **Security scanning is a shared responsibility.** Publishing safe models protects the entire HF ecosystem from supply chain attacks.

### Skill Created

`hf-hub-security-scanning-deep-dive/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md covering scanning architecture, detection layers, badges, API access, false positives, and best practices.

### Sources

- Hugging Face Hub security documentation
- PickleScan (Trail of Bits) — https://github.com/trailofbits/picklescan
- ClamAV — https://www.clamav.net/
- Hugging Face security best practices guides
- OpenSSF best practices for ML supply chain security
