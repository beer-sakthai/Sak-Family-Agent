# Research Routing & Workflow Playbook

Comprehensive guidelines for research request intake, specialist delegation, and fallback search execution.

## 1. Specialist Registry & Routing Signals
| Specialist | Trigger Keywords & Signals | Target Output |
|---|---|---|
| `pulse` | sentiment, reddit, x, trending, "what's people saying" | Social & trend synthesis |
| `grants` | NIH, grant, R01, K-award, RePORTER, NOSI | Funding opportunity brief |
| `litreview` | literature review, PICO, SPIDER, meta-analysis | Peer-reviewed academic synthesis |
| `syllabus` | curriculum, reading list, course outline | Academic reading plan |
| `patent` | prior art, patent, FTO, invention landscape | IP & novelty report |
| `dossier` | due diligence, background check, competitor research | Decision-grade entity brief |

## 2. Intake Protocol (Grill-Me)
- **Q1 (Core Question)**: Force a specific, 1-2 sentence inquiry. Reject vague queries ("AI in medicine").
- **Q2 (Output Format)**: Quick briefing (markdown) vs standalone document (.docx or rich report).
- **Q3 (Disambiguation)**: If intent maps to multiple domains, ask user to select specialist or general fallback.
- **Q4 (Depth Budget)**: Quick scan ($\le 5$ searches) vs Deep scan ($15+$ searches).

## 3. Fallback Search Execution Discipline
- Sequential searches with 1 query/sec pacing.
- Never cite unreturned sources; explicitly tag pre-training knowledge.
- Track 3 counts: Queries issued, sources retrieved, sources cited.
- Halt and escalate after 3 consecutive search failures.

## 4. Synthesis & Deliverable Format
- Executive Summary (1 paragraph, bottom-line upfront).
- Key Findings (bulleted with inline citations).
- Contradictions & Gaps (areas of uncertainty or conflicting data).
- Actionable Recommendations.
