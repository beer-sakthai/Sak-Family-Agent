# Workbench Code Snippets — GA4 → Sheets

## Parse GA4 rows into a DataFrame

```python
def rows_to_df(d):
    dh = [h.get('name') for h in d.get('dimensionHeaders', [])]
    mh = [h.get('name') for h in d.get('metricHeaders', [])]
    out = []
    for r in d.get('rows', []) or []:
        row = {}
        dims = r.get('dimensionValues', []) or []
        mets = r.get('metricValues', []) or []
        for i, h in enumerate(dh):
            row[h] = dims[i].get('value') if i < len(dims) else ''
        for i, h in enumerate(mh):
            v = mets[i].get('value') if i < len(mets) else '0'
            try:
                row[h] = float(v)
            except:
                row[h] = v
        out.append(row)
    return out
```

## Write data to Google Sheets

```python
def write_sheet(sheet_id, sheet_name, headers, rows):
    """Write column headers + data rows to a Google Sheet tab."""
    values = [headers] + rows
    
    result, error = run_composio_tool("GOOGLESHEETS_UPDATE_CELLS", {
        "spreadsheetId": sheet_id,
        "range": f"'{sheet_name}'!A1",
        "values": values
    })
    if error:
        print(f"Sheets write error: {error}")
    else:
        print(f"Wrote {len(rows)} rows to {sheet_name}")
    return result, error
```