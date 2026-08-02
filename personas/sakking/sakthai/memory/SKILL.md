---
name: supply-chain-forecast
category: business
description: "Forecast future supply chain events (e.g., demand, lead times) based on historical data from memory."
version: 1.0.0
author: Sak-Family-Agent
platforms: [linux, macos, windows]
metadata:
  sakthai:
    tags: [supply-chain, forecasting, business-intelligence, prediction]
    related_skills: [supply-chain-monitor, supply-chain-optimizer]
---

# Supply Chain Forecasting

This skill enables you to predict future supply chain metrics by analyzing historical data stored in your persistent memory.

## When to Use

Use this skill when you need to answer questions like:

- "What is the expected demand for Product X next month?"
- "Forecast the lead time for shipments from Supplier Y."
- "Are there any seasonal trends in our sales data?"

## How It Works

1. **Identify Target:** Determine the metric to be forecasted (e.g., `demand`, `lead_time`) and the entity (e.g., `ProductX`, `SupplierY`).
2. **Search Memory:** Use the `search` tool to find all relevant historical facts. The facts should be structured with a `kind` (e.g., `sale`, `shipment_arrival`) and a `key`.
    - Example search: `search "kind:sale key:ProductX"`
3. **Extract Data:** From the search results, extract the values and timestamps (`created_at`).
4. **Analyze Trend:** Perform a simple analysis on the data.
    - **For Demand:** Calculate the average weekly/monthly sales. Identify any growth trend (e.g., calculate the percentage change over the last few periods).
    - **For Lead Time:** Calculate the average and standard deviation of the duration between `shipment_ordered` and `shipment_arrival` facts.
5. **Generate Forecast:** Create a concise, actionable forecast based on the analysis.
6. **Store Observation:** Use the `learn` tool to save the forecast as a new `observation` for future reference. This creates a feedback loop.
    - Example: `learn "Forecast for ProductX: demand expected to be 100-120 units next month, based on 10% MoM growth." --kind forecast`

## Example Workflow: Forecasting Demand

**User:** "Forecast the demand for 'Blue Widget' for next quarter."

**Agent's Internal Steps:**

1. **Tool Call:** `search "kind:sale key:Blue Widget"`
2. **Analyze Results:**
    - *Fact 1: value=50, created_at=... (3 months ago)*
    - *Fact 2: value=55, created_at=... (2 months ago)*
    - *Fact 3: value=61, created_at=... (1 month ago)*
    - *Analysis: Average monthly sales ~55 units. Growth is ~10% month-over-month.*
3. **Formulate Forecast:**
    - *Next month's forecast: 61 * 1.1 = ~67 units.*
    - *Month 2 forecast: 67 * 1.1 = ~74 units.*
    - *Month 3 forecast: 74 * 1.1 = ~81 units.*
    - *Total for quarter: ~222 units.*
4. **Tool Call:** `learn "Forecast for Blue Widget: Q3 demand projected at ~222 units, based on consistent 10% MoM growth." --kind forecast`
5. **Respond to User:** "Based on sales data from the last three months, I forecast a demand of approximately 222 'Blue Widgets' for the next quarter, assuming the current 10% monthly growth trend continues."

## Data Structure for Memory

To make this skill effective, store data with consistent `kind` and `key` values.

```
# Storing a sale
learn "50" --kind sale --key "Blue Widget"

# Storing a shipment event
learn "Ordered from SupplierY" --kind shipment_ordered --key "PO-123"
learn "Arrived at warehouse" --kind shipment_arrival --key "PO-123"
```
