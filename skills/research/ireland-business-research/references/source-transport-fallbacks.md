# Ireland Business Research — Source Transport & Fallbacks

Validated: 2026-06-21 maintenance run.

## Current transport status for core sources

| Source | web_search | web_extract |
|--------|-----------|-------------|
| cro.ie | works | fails — 402 BILLING_ERROR |
| businesses.ie | works but often returns homepage / tracking links | fails — 402 BILLING_ERROR |
| cso.ie | works | works |
| idaireland.com | works | works |
| enterpriseireland.com | works | works |
| company IR / SEC filings | works | works |

## Fallback hierarchy when CRO data is unavailable

1. **General web_search** with targeted terms: `"<company>" Ireland company registration number`, `"<company>" annual report directors`, `"<company>" CRO`.
   - Best results come from SEC filings (20-F), investor relations annual reports, and Wikipedia for large public companies.
2. **Search business.ie homepage** only confirms the service exists; it does not reliably surface a specific company profile.
3. **Do not fabricate** registration numbers, incorporation dates, or directors when direct extraction failed.
