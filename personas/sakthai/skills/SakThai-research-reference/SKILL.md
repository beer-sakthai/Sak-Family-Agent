---
name: SakThai-research-reference
author: SakThai
license: MIT
description: "Capture, organize, and document academic paper references in project directories. Search arXiv, download PDFs, write structured reference indexes with BibTeX, and link back to your project's README."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Arxiv, Papers, References, BibTeX, Academic]
    related_skills: [arxiv, ocr-and-documents]
---

# Academic Reference Capture

Workflow for finding relevant academic papers, downloading them, and integrating
them as structured references inside a project directory.

Designed to follow the `arxiv` skill's Complete Research Workflow: after you've
discovered and assessed papers, this skill captures them permanently alongside
the project they informed.

## When This Skill Activates

Use this skill when the user says:
- "Save/fetch these papers"
- "Add references to [project]"
- "Download these arXiv IDs"
- "Create a references section in the README"
- "Record these papers in v6 / the dataset / the project"

Also use it proactively: after searching arXiv and selecting relevant papers,
this skill governs the *what next* step that the `arxiv` skill doesn't cover.

## Workflow

### Step 1: Create the references directory

```bash
mkdir -p project/references
```

### Step 2: Download the PDFs

Fetch each paper from `https://arxiv.org/pdf/{ID}`. Name files by their arXiv ID.

```bash
curl -sL -o project/references/2312.10793.pdf "https://arxiv.org/pdf/2312.10793"
sleep 4   # Respect arXiv rate limit (~1 req/3 sec)
curl -sL -o project/references/2601.19280.pdf "https://arxiv.org/pdf/2601.19280"
```

**Parallel downloads are fine** when using separate concurrent tool calls
(each runs its own curl). Only put sequential `sleep` delays between fetches
that run inside the same terminal command.

### Step 3: Write the REFERENCES.md index

Create `project/references/REFERENCES.md` with one section per paper. Each
section must include:

| Field | Always Required |
|-------|:--------------:|
| arXiv ID + URL link | Yes |
| Full title | Yes |
| Full author list | Yes |
| Publication date | Yes |
| **Relevance note** (2-4 sentences) | Yes — connects the paper to the project's decisions |
| BibTeX citation | Yes |
| Local PDF path | Yes |

### Relevance note format

The relevance note is the most important field. It states *why this paper
matters for this specific project*, not what the paper says in general. Good:

> "This paper found that instruction types compete during fine-tuning — coding
> data improves coding but harms chat. This informed our decision to balance 71
> tool schemas across 7 categories to minimize cross-task interference."

Bad:

> "This paper discusses instruction tuning for LLMs."

### Step 4: Link from the project README

Add a summary matrix in the project's README that references the details file:

```markdown
## References

| arXiv ID | Topic | Project Impact |
|----------|-------|----------------|
| [2312.10793](https://arxiv.org/abs/2312.10793) | Instruction mixing | Schema balance to avoid cross-task interference |

See `references/REFERENCES.md` for full summaries and BibTeX.
```

### Step 5: Verify

- Check all PDFs downloaded correctly: `ls -lh project/references/*.pdf`
- Check REFERENCES.md parses as valid markdown
- Confirm the README links are correct
- Verify BibTeX entries have no syntax errors

## References Directory Structure

```
project/
├── references/
│   ├── REFERENCES.md         ← Index with summaries, BibTeX, relevance notes
│   ├── 2312.10793.pdf        ← Paper PDFs (named by arXiv ID)
│   ├── 2601.19280.pdf
│   └── ...
└── README.md                 ← Links to references/
```

## Pitfalls

- **Rate limits**: arXiv allows ~1 request per 3 seconds. When downloading
  sequentially in a single shell command, add `sleep 4` between fetches.
  Parallel curl calls via separate tool calls don't need delays — Hermes
  terminal sessions are independent.
- **Broken links**: arXiv IDs change format across years. New format:
  `2402.03300`. Old format: `hep-th/0601001`. Always test the PDF URL.
- **Withdrawn papers**: Papers can be withdrawn after submission. Check the
  arXiv `<summary>` field for "withdrawn" or "retracted" before recording.
- **Version drift**: Use versioned IDs (`1706.03762v7`) in BibTeX citations
  to prevent citation drift when later versions change content.
- **BibTeX syntax**: Watch for special characters in titles (&, {, }, ~, \\)
  that need escaping in BibTeX strings.

## Reference Files

- `references/references-index.md` — template for the REFERENCES.md entry format
- `references/composio-web-research.md` — web research via Exa/Composio (narrative answers, full-text extraction, batched queries)
- `references/hf-papers-workflow.md` — daily HF papers survey workflow

## Related Skills

- `arxiv` — search and discover papers (run this first)
- `ocr-and-documents` — extract text from downloaded PDFs
- `llm-wiki` — capture paper insights into a persistent knowledge base
