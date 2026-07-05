---
name: service-quoting
description: Use when constructing a customer quote from stored pricing facts and when deciding whether to capture a lead instead of answering from memory.
category: business
tags: [quoting, pricing, customer, sales]
---

# Service Quoting

Use this skill when a potential customer asks about pricing or wants a quote for House of Sak services.

## Process

1. **Check Active Leads**: Search memory for any existing lead context for this person/business
2. **Pricing Reference**: Load service pricing from the appropriate source
3. **Construct Quote**: Build the quote with clear scope boundaries
4. **Save Lead**: Capture the lead in memory for follow-up

## Where to Store Leads

```
Memory target: user (user profile)
Key format: "lead-{business-name}"
Content example: "Lead: TechStartup Inc — interested in QA Shield and Agent Builder. Contact: john@example.com. Quoted €450–€800. Status: warm (2026-07-04)"
```

## Pricing Reference

| Service | Price Range |
|---------|-------------|
| QA Shield | €200–€500 |
| Agent Builder | €300–€800 |
| Social Pulse | €100–€300/month |
| Fast Prototype | €150–€400 |
| Trust Check | €150–€300 |
| Full House Bundle | €600–€1,600 |

## Principles

- Always deliver firm quote after free scope (not ranges)
- No upfront payment for first-time clients
- Priced for people who struggle — adjust downward when the client genuinely can't pay standard rates
- Save ALL leads, even if they don't convert immediately