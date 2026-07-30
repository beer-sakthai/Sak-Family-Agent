# Learn One New HF Topic — Recurring Cron Workflow

Sibling to the trending-model crawl. Instead of picking a trending model, this workflow systematically expands coverage of the Hugging Face ecosystem by researching one new topic per run and creating a corresponding skill.

## Trigger

Cron job at `~profiles/sakthai/cron/jobs.json` with entry `hf-learn-topic`. Runs autonomously — no user present, no questions possible.

## Step-by-step

### 1. Check what's already covered

Read the topic tracker and compare against existing skills in one pass:

```bash
# The canonical tracker
cat /opt/data/profiles/sakthai/cron/hf-topics-covered.json

# Available skills — cross-reference to avoid blind spots
skills_list    # or check ~/profiles/sakthai/skills/
```

The tracker is a JSON array of topic slugs. It lives at `~profiles/sakthai/cron/hf-topics-covered.json` and has several sync copies across the repo structure.

**Key check:** A topic may exist as a fully-developed skill file while NOT appearing in the tracker. Both sources must be consulted before picking a topic.

### 2. Find a gap

Pick something NOT in the tracker AND not already a complete skill. Sources:

- **HF blog** (`huggingface.co/blog`) — latest features, announcements, guides
- **HF changelog** (`huggingface.co/changelog`) — recent Hub changes
- **HF docs sidebar** (`huggingface.co/docs/hub/en/index`) — all documented features, some never covered
- **HF Learn portal** (`huggingface.co/learn`) — lists 13+ courses (LLM, CV, Audio, Agents, Deep RL, Diffusion, Smol, Robotics, ML for 3D, ML for Games, Context, Audio, Cookbook). Several courses are NOT covered: CV, Deep RL, Smol, ML for Games. Great for finding substantial, well-documented topics.
- **Skills list** — if a skill exists but isn't in the tracker, that's a sync gap, not a new topic. Also check if a skill by the proposed name already exists — if so, update it via `action='edit'` instead of creating a new one.

**Good candidates:** Tools or features that are:
- Part of the HF ecosystem (libraries, Hub features, SDKs)
- Documented and stable enough to create a durable skill for
- NOT trivial one-offs (a single config flag, a single API endpoint)

**Bad candidates:**
- Environment-specific issues (missing binaries, package install problems)
- Session-specific transient errors
- Features already covered under another name
- Pure Enterprise features (SSO, storage regions, network security) — too niche

### 3. Research via web

Use HF's own documentation as the primary source. The browser tool works for docs.huggingface.io and docs.argilla.io type sites.

**Recommended approach: `browser_navigate` + `browser_console` for text extraction.**

The standard `browser_snapshot(full=True)` output is often truncated on long documentation pages (element limits ~150, character truncation ~8K). Instead, navigate to the target page, then extract the full text via `browser_console`:

```python
# Step 1: navigate to the documentation page
browser_navigate(url="https://huggingface.co/docs/diffusers/en/using-diffusers/controlnet")

# Step 2: extract the page body text with a character limit
browser_console(expression="document.body.innerText.substring(0, 15000)")
# Increase to 25000 for longer pages. The full body can be 30K+ chars.

# Step 3: for API reference pages, extract just the main content area
browser_console(expression="document.querySelector('main').innerText.substring(0, 20000)")

# Step 4: scroll to reveal more of the page if content is JS-lazy-loaded
browser_scroll(direction="down")

# Step 5: re-extract after scrolling
browser_console(expression="document.body.innerText.substring(0, 25000)")
```

**Why this works better than `browser_snapshot`:**
- The snapshot is truncated at element counts (~150 elements) and char limits
- `browser_console` returns the raw text without element truncation
- Extracts code examples, parameter tables, and section headings that the snapshot collapses
- Works on React/Svelte pages where DOM inspection is needed

**⚠️ `browser_console` + DOM queries on React-heavy pages:** When using `browser_console(expression='document.querySelectorAll("h4")')`, the return value will be `null` because the structured clone algorithm cannot serialize DOM element objects. Always wrap DOM queries with `JSON.stringify()` and `.map()` to extract text:

```javascript
// WRONG — returns null
document.querySelectorAll("h4")

// CORRECT — returns array of heading texts
JSON.stringify([...document.querySelectorAll("h4")].map(h => h.textContent.trim()))
```

For simple full-page text extraction, `document.body.innerText.substring(0, N)` is safest — it needs no serialisation because it returns a primitive string.

**For plain-text endpoints** (API responses, raw markdown files, JSON endpoints), do NOT use the browser — use `curl` via `terminal()`:

```bash
curl -s --connect-timeout 10 "https://huggingface.co/api/models?author=Nanthasit&limit=5"
```

**Research checklist** — gather for the skill:
- One-line description and positioning
- Deployment / setup options
- Core API objects and their relationships
- Complete CRUD workflow example
- HF Hub integration points
- Advanced features (webhooks, vectors, custom layouts)
- Known pitfalls (storage, auth, schema immutability)
- Reference links (docs, GitHub, API docs, templates)

**Research technique: extracting course/structure nav data.** HF Learn course pages embed the full sidebar navigation as JSON in a `<script>` tag inside the page HTML. After navigating to the course page, extract the unit/section structure by inspecting the page's React props:

```javascript
// Find the JSON data embedded in the page
// Look for a script tag with JSON content containing the nav tree
let scripts = document.querySelectorAll('script[type="application/json"]');
for (let s of scripts) {
    let data = JSON.parse(s.textContent);
    // The navigation structure often lives in the page props
    if (data.props?.pageProps?.nav || data.sections) {
        console.log(JSON.stringify(data.props.pageProps.nav || data.sections, null, 2));
    }
}
```

Alternatively, extract the sidebar text from the main DOM:
```javascript
let nav = document.querySelector('nav');
console.log(nav.innerText);
```

This is much faster than clicking through every unit link and works even when client-side routing makes direct URL navigation to sub-pages fail with 404s (as happens with HF Learn course pages).

### 4. Create or update the skill

```python
# In cron mode: use skill_manage(action='create') directly via tool call
# execute_code is BLOCKED by Tirith security scanner in cron mode
# write_file also works for creating SKILL.md directly

# Check if skill already exists
skills_list    # or browse ~/profiles/sakthai/skills/

# If it EXISTS: update it (don't create a duplicate)
skill_manage(action="edit", name="hf-<topic>",
    content="""---\nname: hf-<topic>\n...\n---\n\n# Full SKILL.md content
    """)

# If it DOES NOT EXIST: create it
skill_manage(action="create", name="hf-<topic>", category="mlops",
    content="""---\nname: hf-<topic>\n...\n---\n\n# Full SKILL.md content
    """)
```

**⚠️ Cron mode restriction:** The `execute_code` tool is blocked by the Tirith security scanner when running as a scheduled cron job. You cannot use `from hermes_tools import write_file, terminal, ...` inside a script block. Instead:
- Use **`write_file(path, content)` as a direct tool call** to create the SKILL.md file at the skill directory path
- Use **`skill_manage(action='create')`** as a direct tool call (preferred — auto-creates the directory, validates frontmatter)
- Use **`terminal()`** with Python one-liners for batch operations (tracker updates, verification)

Do NOT rely on `execute_code` at any point in the cron workflow — it will always be blocked.

**Naming convention:** `hf-<topic>` in lowercase, hyphens for spaces. Category should be `mlops` for HF ecosystem tools.

**Required sections in every skill:**
1. Overview — what it is, GitHub stars, docs link, license, stack
2. Deployment / Setup — how to get started, zero-cost options first
3. Core Concepts — SDK objects, parameters, tables
4. Workflow — end-to-end example (copy-pasteable)
5. HF Integration — how it connects to the Hub
6. Advanced Features — less common but powerful capabilities
7. Use Cases — table showing what each domain looks like in this tool
8. Pitfalls — must-read before using in production
9. Reference — all links

### 5. Update tracker

Read the canonical tracker, append the new topic slug, then sync all copies. Use a batch Python script via `terminal()` — this is faster than patching each file individually.

```python
import json

# Read and update the primary tracker
with open("/opt/data/profiles/sakthai/cron/hf-topics-covered.json") as f:
    data = json.load(f)
data.append("hf-<topic>")
data.sort()
with open("/opt/data/profiles/sakthai/cron/hf-topics-covered.json", "w") as f:
    json.dump(data, f, indent=2)
```

### 6. Sync copies — all 15 known locations

The topic tracker file (`hf-topics-covered.json`) is replicated across **15 independent file paths** — NOT symlinks. Each is an independent JSON file that must be individually updated. However, different workflows maintain different subsets, so the files have different entry counts. **Never use `cp` to overwrite one copy with another** — that destroys intentionally different subsets.

**Complete inventory of all 15 copies (verified 2026-07-26):**

| # | Path | Typical entries | Maintained by |
|---|------|-----------------|---------------|
| 1 | `/opt/data/profiles/sakthai/skills/hf-topics-covered.json` | ~401 | Profile skills tracker |
| 2 | `/opt/data/profiles/sakthai/cron/hf-topics-covered.json` | ~411 | Cron HF learn topic workflow |
| 3 | `/opt/data/profiles/sakthai/skills/references/hf-topics-covered.json` | ~399 | Skills reference tracker |
| 4 | `/opt/data/Sak-Family-Agent/hf-topics-covered.json` | ~411 | Family repo root tracker |
| 5 | `/opt/data/Sak-Family-Agent/skills/hf-topics-covered.json` | ~397 | Family repo skills copy |
| 6 | `/opt/data/Sak-Family-Agent/skills/references/hf-topics-covered.json` | ~397 | Family repo references copy |
| 7 | `/opt/data/Sak-Family-Agent/personas/sakthai/skills/hf-topics-covered.json` | ~386 | Persona skills tracker |
| 8 | `/opt/data/Sak-Family-Agent/personas/sakthai/skills/references/hf-topics-covered.json` | ~390 | Persona references tracker |
| 9 | `/opt/data/sakthai-skills-repo/hf-topics-covered.json` | ~409 | Skills repo copy |
| 10 | `/opt/data/sakthai-skills-repo/cron/hf-topics-covered.json` | ~92 | Skills repo cron subset |
| 11 | `/opt/data/sakthai-skills-repo/skills/hf-topics-covered.json` | ~399 | Skills repo nested copy |
| 12 | `/opt/data/sakthai-skills-repo/skills/references/hf-topics-covered.json` | ~399 | Skills repo references copy |
| 13 | `/opt/data/sakthai-skills/hf-topics-covered.json` | ~409 | Skills backup copy |
| 14 | `/opt/data/sakthai-skills/cron/hf-topics-covered.json` | ~93 | Skills backup cron subset |
| 15 | `/opt/data/sakthai-skills/skills/references/hf-topics-covered.json` | ~61 | Skills backup references |

**Canonical approach — batch Python script via `terminal()`:**

This is faster and more reliable than patching each file individually, especially since there are 15 copies to update. The approach: iterate over all known paths, skip missing ones, insert the new topic, and write back.

```bash
python3 -c "
import json

topic = 'hf-<topic>'

paths = [
    '/opt/data/profiles/sakthai/skills/hf-topics-covered.json',
    '/opt/data/profiles/sakthai/cron/hf-topics-covered.json',
    '/opt/data/profiles/sakthai/skills/references/hf-topics-covered.json',
    '/opt/data/Sak-Family-Agent/hf-topics-covered.json',
    '/opt/data/Sak-Family-Agent/skills/hf-topics-covered.json',
    '/opt/data/Sak-Family-Agent/skills/references/hf-topics-covered.json',
    '/opt/data/Sak-Family-Agent/personas/sakthai/skills/hf-topics-covered.json',
    '/opt/data/Sak-Family-Agent/personas/sakthai/skills/references/hf-topics-covered.json',
    '/opt/data/sakthai-skills-repo/hf-topics-covered.json',
    '/opt/data/sakthai-skills-repo/cron/hf-topics-covered.json',
    '/opt/data/sakthai-skills-repo/skills/hf-topics-covered.json',
    '/opt/data/sakthai-skills-repo/skills/references/hf-topics-covered.json',
    '/opt/data/sakthai-skills/hf-topics-covered.json',
    '/opt/data/sakthai-skills/cron/hf-topics-covered.json',
    '/opt/data/sakthai-skills/skills/references/hf-topics-covered.json',
]

for p in paths:
    try:
        with open(p) as f:
            data = json.load(f)
        if topic not in data:
            data.append(topic)
            data.sort()
            with open(p, 'w') as f:
                json.dump(data, f, indent=2)
    except FileNotFoundError:
        pass  # file may have been moved/deleted between runs
"
```

**⚠ Never use `cp` between copies** — the sakthai-skills cron copies (#10, #14) have only ~92 entries because they track a different, smaller set. Overwriting them with the 400+ entry version from Sak-Family-Agent would contaminate that workflow's state. The sakthai-skills references copy (#15) has only ~61 entries — even smaller. Always use targeted insertion.

**⚠ Sync failure is not critical** — each cron workflow reads from its own primary copy. If you miss a secondary copy, the next run of that workflow will pick it up when it updates its own primary. Missing the primary copies (#1 and #2) IS critical — those are what the cron jobs read.

### 7. Verify

```bash
python3 -c "
import json

topic = 'hf-<topic>'
paths = [
    '/opt/data/profiles/sakthai/cron/hf-topics-covered.json',
    '/opt/data/profiles/sakthai/skills/hf-topics-covered.json',
]
all_ok = True
for p in paths:
    data = json.load(open(p))
    ok = topic in data and len(set(data)) == len(data)
    print(f'  [{\"PASS\" if ok else \"FAIL\"}] {p} ({len(data)} entries)')
    all_ok = all_ok and ok
print(f'Verification: {\"PASSED\" if all_ok else \"FAILED\"}')
\"
```

### 8. Report

Output a concise summary of what was learned and delivered. No `[SILENT]` — the user always gets a report when a new topic was covered. Only `[SILENT]` if nothing was done (all topics covered already — which should not happen as long as the ecosystem grows).

## Common pitfalls

| Pitfall | Symptom | Mitigation |
|---------|---------|------------|
| HF docs use client-side routing | Direct URL navigation returns 404 | Navigate to a known-good page first (e.g. `/en/index`), then click links in the sidebar |
| Tracker has stale entries | Topic skill exists but not in tracker | Add it to tracker instead of picking as "new" — or note it as a sync gap |
| Multiple cron jobs modify tracker concurrently | Entries out of order, divergence between copies | Always read from the primary copy, patch, then sync; the batch Python script makes atomic edits per file |
| Browser tool blocked / limited | Can't navigate to doc pages | Use `curl` for plain-text endpoints (raw `.md` files) or API responses; browser for interactive pages |
| `execute_code` blocked in cron | Script-based tool calls fail mid-workflow | Use direct tool calls (`write_file`, `skill_manage`, `terminal()`) instead; never rely on `execute_code` in cron mode |
| `browser_snapshot` truncates doc page text | Missing sections, code blocks, parameter tables | Switch to `browser_console(expression="document.body.innerText.substring(0, 15000)")` for raw text extraction |
