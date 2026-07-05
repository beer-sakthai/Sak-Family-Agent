---
name: saksit-ga4-to-sheets-dashboard
title: GA4 Analytics → Google Sheets Dashboard
description: Pull Google Analytics 4 metrics into Google Sheets for live business reporting. One-shot or cron-ready.
---

# GA4 → Sheets Analytics Pipeline

Pull daily/weekly metrics from Google Analytics 4 into structured Google Sheets for live business dashboards. Uses Beer's existing Composio connections — zero setup.

## When to use

- Beer asks for a **business dashboard** or **analytics report**
- You need to **pull GA data into a spreadsheet** for him
- You want to **schedule recurring analytics** via cron (daily/weekly pulse)
- You're setting up **KPI tracking** for a campaign or product

## Prerequisites

- Active `google_analytics` + `googlesheets` connections (both connected ✓)
- Know the GA4 property ID (run `LIST_ACCOUNT_SUMMARIES` if unknown)

## Workflow

### Step 1: Discover the property

If property ID is unknown, use:
```json
COMPOSIO_MULTI_EXECUTE_TOOL
tool_slug: GOOGLE_ANALYTICS_LIST_ACCOUNT_SUMMARIES
arguments: {}
```

Response includes `properties/{property_id}` for each account. Save the numeric property_id.

### Step 2: Define what to pull (choose a template)

**Template A — Weekly Pulse** (traffic + engagement + conversions)
```
dimensions: [{"name": "date"}]
metrics: [
  {"name": "activeUsers"},
  {"name": "newUsers"},
  {"name": "sessions"},
  {"name": "engagedSessions"},
  {"name": "bounceRate"},
  {"name": "averageSessionDuration"},
  {"name": "screenPageViews"},
  {"name": "eventCount"},
  {"name": "conversions"}
]
```

**Template B — Channel Breakdown**
```
dimensions: [{"name": "sessionDefaultChannelGroup"}]
metrics: [
  {"name": "activeUsers"},
  {"name": "sessions"},
  {"name": "engagedSessions"},
  {"name": "conversions"},
  {"name": "totalRevenue"}
]
```

**Template C — Page Performance (top 20)**
```
dimensions: [{"name": "pagePath"}, {"name": "pageTitle"}]
metrics: [
  {"name": "screenPageViews"},
  {"name": "activeUsers"},
  {"name": "averageSessionDuration"},
  {"name": "bounceRate"}
]
orderBys: [{"desc": true, "metric": {"metricName": "screenPageViews"}}]
```

### Step 3: Run the report

```json
COMPOSIO_MULTI_EXECUTE_TOOL
tool_slug: GOOGLE_ANALYTICS_RUN_REPORT
arguments: {
  "property": "properties/{property_id}",
  "dateRanges": [{"startDate": "30daysAgo", "endDate": "yesterday"}],
  "dimensions": [...],
  "metrics": [...]
}
```

### Step 4: Create or update the Sheet

**First run:** Create a new spreadsheet:
```json
COMPOSIO_MULTI_EXECUTE_TOOL
tool_slug: GOOGLESHEETS_CREATE_GOOGLE_SHEET1
arguments: {"title": "GA4 Business Dashboard"}
```
Save the spreadsheet ID from the response.

**Subsequent runs:** Use the stored spreadsheet ID.

Use the Composio Remote Workbench to write headers + data rows to the sheet. See `/references/workbench-snippets.md` for exact code.

### Step 5: Optional — Schedule as cron

```bash
cronjob action=create \
  schedule="0 8 * * 1" \
  name="ga4-weekly-pulse" \
  deliver="origin" \
  prompt="Run the GA4 Weekly Pulse dashboard update and summarize key changes compared to the previous period."
```

## Pitfalls

- **Rate limits:** Google Sheets has 60 reads/min + 60 writes/min. For big datasets, batch writes.
- **Date ranges:** Use relative dates (`30daysAgo`, `yesterday`) in cron jobs so they stay current.
- **Compatibility:** Not all dimensions + metrics combine. Use `GOOGLE_ANALYTICS_CHECK_COMPATIBILITY` if you get a 400 error.
- **Zero rows:** GA omits zero-volume rows. Don't assume missing = error.
- **Row limits:** Default 10K rows, max 250K. Paginate with `offset` if needed.

## Verification

After running, open the spreadsheet URL to confirm data landed correctly. Summarize top-line metrics for Beer:
- Users / Sessions / Pageviews (Δ from prev period)
- Top 5 channels by conversions
- Bounce rate trend