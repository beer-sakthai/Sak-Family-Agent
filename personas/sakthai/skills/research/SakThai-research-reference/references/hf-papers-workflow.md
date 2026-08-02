# HF Papers of the Day — Workflow Reference

## Purpose
Daily cron job that surveys new ML research featured on Hugging Face's daily papers page (https://huggingface.co/papers) and captures the top findings.

## Step-by-step

### 1. Discover — Extract paper IDs
The HF papers page is client-rendered (Svelte), so `hf papers list` may not return full details. Scrape the HTML directly:

```bash
curl -sL "https://huggingface.co/papers" | grep -oP '/papers/[0-9]{4}\.[0-9]{5}' | sort -u
```

### 2. Fetch metadata — Extract from arXiv meta tags
For each arXiv ID, fetch structured data via HTML meta tags (no API key needed):

```bash
id="2607.19942"
title=$(curl -sL "https://arxiv.org/abs/$id" | grep -oP '(?<=citation_title" content=")[^"]*')
abstract=$(curl -sL "https://arxiv.org/abs/$id" | grep -oP '(?<=citation_abstract" content=")[^"]*')
```

Available citation meta tags: `citation_title`, `citation_author` (multiple), `citation_date`, `citation_abstract`, `citation_pdf_url`, `citation_arxiv_id`.

### 3. Read full abstracts (no truncation)
The meta tag gives the full abstract in one shot — no truncation. For multi-paper batches, parallelize via separate curl calls.

### 4. Read existing reference file for format consistency
Before writing, read the existing hf-papers.md to match its heading style, date-stamp pattern, and entry structure:

```bash
skill_view name=mlops/huggingface-hub file_path=references/hf-papers.md
```
or `cat ~/profiles/sakthai/skills/mlops/huggingface-hub/references/hf-papers.md`.

Note the time-of-day qualifier in the last entry's heading (e.g. `(Afternoon)`, `(Evening)`) — new entries should increment consistently. The heading is flush with the source page's current content set.

### 5. Report structure
Each paper entry includes:
- Title + HF link + arXiv link + GitHub star count (as popularity signal)
- 1-2 sentence summary of what it does
- "Why it matters" — key contribution or practical implication
- Shorter is better — aim for a digest, not a full paper review

### 6. Save findings
Use `skill_manage` to write the report (preferred over `cat >`):

```
skill_manage action=write_file name=mlops/huggingface-hub file_path=references/hf-papers.md file_content="..."
```

Output file is `mlops/huggingface-hub/references/hf-papers.md`.

### 7. Sync to GitHub
```bash
cd /opt/data/sakthai-skills-repo
cp -a ~/profiles/sakthai/skills/. .
git add -A
git diff --cached --stat          # review before commit
git commit -m "papers: YYYY-MM-DD — paper1, paper2, paper3"
git push origin main
```

## Pitfalls
- The HF papers page only shows ~15 papers per day. Use `grep` to extract all arXiv IDs from the HTML before picking top 3.
- Paper description meta tags on the HF page ("og:description") only say "Join the discussion on this paper page" — don't rely on them. Always fetch from arXiv.
- arXiv meta tags are in the HTML `<head>` — fast to extract via `grep -oP` with lookbehind assertions. If the lookbehind is too long, use `grep -oP` without lookbehind or `sed`.
- **Name collision with `research-reference`**: Two skills share this name in different categories. Use `skill_view(name='research/research-reference')` by the categorized path or use `skills_list(category='research')` to confirm the bare name resolves. `skill_manage` takes the bare name — only `skill_view` needs the longer path when ambiguous.
- **Format drift**: The hf-papers.md file accumulates entries over time with a running date-stamp. Always read the current file before writing a new entry to match the latest formatting conventions (heading style, entry structure, paper ordering).
