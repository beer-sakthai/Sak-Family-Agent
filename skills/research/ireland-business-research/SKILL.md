---
name: ireland-business-research
description: Structured Ireland business research workflow for company verification, market analysis, sector intelligence, and regulatory context.
---

# Ireland Business Research Skill

Use this skill anytime the task involves Ireland-focused business research: validating company information, analyzing sectors, reviewing market data, or checking regulatory/trade context for Ireland.

## Workflow
1. Parse the exact Irish business entity or topic from the request.
2. Use `web_search` with Ireland-specific queries: add `site:.ie`, `Ireland`, `companies registration office Ireland`, `IDA`, `Enterprise Ireland`, `CSO Ireland`, and `Central Bank Ireland` as relevant. `Forfás` is defunct and no longer an active agency.
3. Use `web_extract` on authoritative sources: CRO (`cro.ie`), CSO (`cso.ie`), IDA Ireland (`idaireland.com`), Financial Regulators, enterprise bodies, company websites, and filings.
   - CRO `web_extract` may fail with a 402/BILLING_ERROR. Graceful fallback: search `site:businesses.ie <company name>` — businesses.ie mirrors daily-verified CRO data (company search, directors, filings) and is reliable for structured facts when CRO direct access is unavailable. Note that `web_extract` on businesses.ie may also return billing errors under the same charge-authorization failure; if both fail, use general `web_search` queries for the company (e.g., `"<company name>" Ireland company registration number`, `"<company name>" annual report directors`) or investor relations / SEC filings for structured facts. Do not fabricate CRO numbers, incorporation dates, or director names from training data.
4. Capture structured facts:
   - Company name + registration number
   - Registered address + legal form
   - Directors and company secretary
   - Incorporation date, latest accounts, and filing status
   - Nature of business / NACE codes
   - Ownership / parent company / subsidiaries
5. Assess business health signals:
   - Revenue trend (latest filed accounts)
   - Employees count
   - Credit indicators and insolvency risk
6. Summarize sector and regulatory context:
   - Relevant Irish/EU regulations
   - Tax and incentive regimes (IDA, R&D tax credits)
   - Market concentration and competitive landscape
   - Economic indicators from CSO
7. Save durable findings with `memory(target='user', action='add', content=...)` for multi-job retention.
8. Tool transport check and graceful degradation:
   - Before heavy web validation, probe `web_search` with a lightweight Ireland query (for example, `site:.ie Ireland business`). If it returns a `BILLING_ERROR` or transport failure, stop, report that live source validation was skipped due to tool unavailability, and do not guess company facts from stale training data.
   - If `web_extract` returns a `BILLING_ERROR` with HTTP 402 / `Insufficient available balance`, treat it as an unresolvable transport failure: do not retry in the same workflow, note the limitation clearly, and rely only on `web_search` results and cached/archived snapshots.
   - If `web_extract` is unavailable (e.g., billing error, charge authorization failure, or no content returned), fall back to `web_search` results and cached/archived snapshots. Do not fabricate filing numbers, incorporation dates, or director names when direct extraction failed.
   - Always note the limitation clearly and exclude failed sources from final facts, but still report validated findings from working sources.

## References
- `references/source-transport-fallbacks.md` — validated transport status and fallback hierarchy for Ireland business sources as of 2026-06-21.