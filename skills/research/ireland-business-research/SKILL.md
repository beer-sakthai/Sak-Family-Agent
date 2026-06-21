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
   - If a specific source (`web_extract`) is paywalled or returns no content, note the limitation clearly and exclude that source from the final facts, but still report what you did find from other sources.
   - Never fabricate filing numbers, incorporation dates, or director names when the registry search failed.