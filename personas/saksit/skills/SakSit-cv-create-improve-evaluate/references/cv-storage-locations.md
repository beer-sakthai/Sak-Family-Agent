# Beer's CV Storage Locations

Discovered 2026-07-09. Search both locations when asked "where is my CV".

## Local Filesystem (`~/home/house-of-sak/`)

| File | Last Modified | Type |
|------|:------------:|------|
| `cv-draft-2026-expanded.md` | **2026-07-17** | Master — expanded (real work history, all fixes) |
| `cv-draft-2026.md` | **2026-07-17** | Short AI draft (real work history) |
| `cv-ai-skills-2026.md` | **2026-07-17** | Skills-first AI variant (real work history) |
| `cv-ai-skills-2026.html` | **2026-07-17** | AI CV HTML (regenerated) |
| `cv-ai-skills-2026.pdf` | **2026-07-17** | AI CV PDF (regenerated) |
| `cv-business-2026.md` | **2026-07-17** | Business/ops CV (real work history) |
| `cv-business-2026.html` | **2026-07-17** | Business CV HTML (regenerated) |
| `cv-business-2026.pdf` | **2026-07-17** | Business CV PDF (regenerated) |

## Google Drive (`beernanthasit@gmail.com`)

| File | Type | Last Modified | ID |
|------|------|:------------:|----|
| `Nanthasit Burankum — AI Agent Developer (AI Skills + Proof)` | Google Doc | **2026-07-25** ← rewritten: professional structure, correct dates (May 2026), grammar checked | `1B812Wv9Gzc5_xslZlsapP42e_UkiJVxSSb_DquV3_5I` |
| `Nanthasit Burankum — Operations & Business Manager (Business CV)` | Google Doc | 2026-07-17 | `1PdN2J4nJ7dwbtFG2yALHUnB4c2x0b8Tbl9B7GVQBM4s` |
| *(superseded)* AI Skills CV (old) | Google Doc | 2026-07-17 | `1MLV64h7r-AsviaA9z_Fshv4crx5I5_g1Td6MVt71Wv4` |
| `nanthasit_burankum_resume` | Google Doc | 2026-07-15 | `1NuSmA5R4JK4oXLRk9hrmTnhvB4Tn1cjAe_swXvJF_mI` |
| `Nanthasit_Burankum_CV_2026_expanded` | Google Doc | 2026-07-05 | `1TfJ2ZiuWCTWYG_UQYJADSpnWhUN0HYmVYvJDYo_q-kE` |
| 📁 `My CV` folder | Folder | — | `1KLQr9vLesJArreszbo6HTU10NUzaig_o` |
| `Create update new cv @Google Docs` | Google Doc | 2026-05-06 | `1jTJm4sgviaj0RJUGmrNURsk-2O_TGYwvzEcX7Kwuc0I` |
| `Nanthasit_Burankum_CV` | Google Doc | 2026-05-03 | `1y7ZwOyk1vkIlLCGVFDkx3y1y7FMXh8jhpuXa61ka6R4` |
| `Nanthasit_Burankum_CV.pdf` | PDF | 2026-04-02 | `18q9c5G8WQf5SsBsN3taEfrnqK3B5ggZ6` |

## Rules

- **Latest versions:**
  - AI Skills CV (Jul 25) — rewritten with professional structure, correct dates (May 2026 HoS start), grammar checked, delivered as Google Doc
  - Business CV (Jul 17) — real work history with all improvements
  - Previous combined `nanthasit_burankum_resume` (Jul 15) is superseded
  - Old AI Skills CV (ID `1MLV64h7r...`, Jul 17) is superseded by new Jul 25 version
- **Canonical work history** is in `references/work-history.md` under this skill — use as source of truth for all experience sections.
- **All experience locations are Ireland-only** — never Bangkok or Thailand.
- When creating HTML+PDF exports, use `scripts/generate-cv-pdf.py` in this skill.
- Always run Phase 0 before modifying any CV.
- **When user says "send file" or "send it to me" — deliver as a Google Doc, not as a .md file.** Beer clarified (Jul 25): `.md` files are not useful on Telegram. Create the CV as a Google Doc via `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN`, place it in the `My CV` folder (`1KLQr9vLesJArreszbo6HTU10NUzaig_o`), and share the edit link. The markdown source is for version control; the Google Doc is the deliverable.
