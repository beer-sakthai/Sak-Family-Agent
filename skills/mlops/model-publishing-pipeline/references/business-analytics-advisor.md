# Business Analytics Advisor — Small GGUF for KPI Recommendations

Deploy a lightweight LLM (0.5B GGUF) as a REST API that consumes structured business KPIs and returns actionable recommendations. Used by Food-Penguin-Limited for sales/operations advice.

## Use Case

Not chat. Not agent. **Structured analytics**: POST metrics → GET recommendations.

The model receives:
- Sales (€), COGS (% of sales), Waste (% of COGS)
- Production items completed / target
- Health score (/100)

And returns 3 bullet-point operational recommendations.

## Why 0.5B Works Here

| Requirement | Why 0.5B fits |
|-------------|---------------|
| Low latency | ~24 tok/s on 2-core CPU |
| Small footprint | 380 MB — runs alongside main app |
| Precision not critical | Trends and heuristics are acceptable |
| Structured output | Prompt enforces strict format |
| Cost | $0 — runs on same machine as dashboard |

## Prompt Design

The prompt is the key — it controls format, not the model:

```
System: You are SakThai, an operational advisor for Food Penguin.
Answer with exactly 3 short bullet points. Each bullet must start
with '- ' and be one sentence. No numbering, no bold, no markdown.

User: Branch: Cork City Centre
Sales: €2840.50
COGS: 32.5% of sales
Waste: 8.1% of COGS
Production: 142 / 160 items
Health: 87 / 100
Question: Give 3 recommendations for tomorrow
```

## Temperature Settings

| Parameter | Value | Reason |
|-----------|-------|--------|
| temperature | 0.35 | Low enough for consistency, high enough for variety |
| top_p | 0.8 | Focus on likely tokens |
| repeat_penalty | 1.25 | Prevent looping recommendations |

## Post-processing

Strip markdown, deduplicate, return max 3 bullets.

## Architecture

```
Browser (React) -> Vercel (Express + Gemini) -> GPT API
                                     Fallback: Local 0.5B GGUF
```

## Pitfalls

- 0.5B may refuse if prompt implies real-time data — frame as data analysis
- Cold start delay on first request
- Dedup logic is essential (model repeats itself)
- Model knows nothing about the business — all context in prompt
