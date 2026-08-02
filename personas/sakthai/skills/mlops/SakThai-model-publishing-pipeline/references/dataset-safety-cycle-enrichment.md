# Dataset Safety & Cycle Workflow Enrichment

Add safety guardrails and full 6-stage cycle workflows to tool-calling training datasets. Applied to `sakthai-combined-v7` on 2026-07-29.

## Gap Analysis (before enrichment)

| Category | Count | Target |
|----------|-------|--------|
| Safety refusals ("I can't help with that") | ~13 | 50+ |
| Full Dream→Growth cycles | 23 | 30+ |
| Capability gap declines | ~0 | 15+ |
| Harmful request refusals | ~0 | 10+ |

## What to add

### 1. Safety declines — 10+ examples
Gracefully decline out-of-scope requests. The model should say what it CAN do, not just "I can't":
> "I don't have real-time data access. I can search the HF Hub, manage memory, and work with files."

### 2. Harmful request refusals — 5+ examples
Firm refusal for illegal/unsafe requests:
> "I can't help with that. I follow ethical guidelines and won't assist with harmful requests."

### 3. Capability gap responses — 5+ examples
Acknowledge missing tools and offer alternatives:
> "I don't have email capabilities. I can save a draft to a file instead."

### 4. Full cycle workflows — 1 per energy stage
Each Dream→Hope→Care→Joy→Trust→Growth stage with proper tool calls:
- **Dream**: assess_energy(5-19) → rest, no action
- **Hope**: assess_energy(20-49) → light exploration (hf_search with limit=3)
- **Care**: assess_energy(50-79) → structured builds (model card, inference)
- **Joy**: assess_energy(80-100) → parallel search + creative work
- **Trust**: assess_energy(80-100) → capture_lesson + verify before close
- **Growth**: assess_energy(80-100) → capture_lesson × 2 + close_cycle

### 5. Honest/truthful responses — 2+ examples
Model admits uncertainty instead of overclaiming:
> "'Best' is subjective. For edge deployment this model excels. For complex reasoning, the larger model is stronger."

## Tool balance check

After enrichment, audit tool usage to ensure SakThai's actual tools are used:

| Tool | Low target (< 30) | Add patterns |
|------|-------------------|-------------|
| `learn` | ✅ if <30 | learn → recall multi-turn chains |
| `forget` | ✅ if <10 | forget → verify with recall |
| `read_file` | ✅ if <10 | read_file → learn (tool chain) |
| `send_message` | ✅ if <10 | notification patterns |
| `capture_lesson` | ✅ if <20 | always pair with close_cycle |
| `log_transition` | ✅ if <20 | always pair with assess_energy |

## Key mechanics

- **Use safe_render in notebooks**: `msgs = rec.get("messages") or rec.get("conversations") or []` — handles legacy v5 format
- **Normalize before upload**: Convert all `conversations` → `messages` before uploading to HF
- **Skipping is safer than crashing**: One bad row should not crash the entire training. Use `if safe_render(r): texts.append(...)` pattern
- **Verify all has messages**: After generation, run `all('messages' in r for r in rows)`
