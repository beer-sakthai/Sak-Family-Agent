# Ireland Business Research — Source Transport & Fallbacks

Validated: 2026-06-21 maintenance run.

## Current transport status for core sources

| Source | web_search | web_extract |
|--------|-----------|-------------|
| cro.ie | works | fails — 402 BILLING_ERROR |
| businesses.ie | works but often returns homepage / tracking links | fails — 402 BILLING_ERROR |
| cso.ie | works | fails — 402 BILLING_ERROR |
| idaireland.com | works | fails — 402 BILLING_ERROR |
| enterpriseireland.com | works | fails — 402 BILLING_ERROR |
| company IR / SEC filings | works | fails — 402 BILLING_ERROR |

> **Note (2026-06-21):** `web_extract` is currently experiencing a global transport/charge-authorization failure (HTTP 402 Insufficient available balance). It returns billing errors on every tested domain — including SEC filings and company IR pages — not just Irish public sources. Live structured extraction is therefore unavailable until the transport balance is restored. Do not retry `web_extract` expecting different results during this window.

## Fallback hierarchy when CRO data is unavailable

1. **General web_search** with targeted terms: `"<company>" Ireland company registration number`, `"<company>" annual report directors`, `"<company>" CRO`.
   - Best results come from SEC filings (20-F), investor relations annual reports, and Wikipedia for large public companies.
2. **Search business.ie homepage** only confirms the service exists; it does not reliably surface a specific company profile.
3. **Do not fabricate** registration numbers, incorporation dates, or directors when direct extraction failed.
