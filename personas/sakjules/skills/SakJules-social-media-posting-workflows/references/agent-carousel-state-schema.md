# Agent Carousel State File Schema

Used by the **Sequential Posting via Cron** workflow to track which agent profiles have been posted across Instagram, LinkedIn, and Facebook.

## File Location

```
~/profiles/saksit/scripts/<series-name>-state.json
```

Example: `agent-carousel-state.json`

## JSON Schema

```json
{
  "agents": [
    {
      "name": "SakKing",
      "role": "The Architect",
      "description": "The one who holds it all together. Infrastructure, strategy, the big picture.",
      "emoji": "🏛️",
      "drive_file_id": "1Vvy8TnPbl7st2Zhn4HYbfPTH4f3Czg_S",
      "posted_ig": true,
      "posted_li": true,
      "posted_fb": true
    }
  ],
  "next_index": 1,
  "posted": ["SakKing"],
  "total": 6
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `agents` | Array | Ordered list of agent profiles (0-indexed). |
| `agents[].name` | String | Agent display name (e.g. "SakThai"). |
| `agents[].role` | String | Role tagline (e.g. "The Growth Partner"). |
| `agents[].description` | String | Short bio (1-2 sentences). |
| `agents[].emoji` | String | Single emoji character. |
| `agents[].drive_file_id` | String | Google Drive file ID for the profile image. |
| `agents[].posted_ig` | Boolean | Posted to Instagram? |
| `agents[].posted_li` | Boolean | Posted to LinkedIn? |
| `agents[].posted_fb` | Boolean | Posted to Facebook? |
| `next_index` | Integer | **0-based** index of the next agent to post. Start at 0 for first, increment after posting succeeds on all 3 platforms. |
| `posted` | Array[String] | Names of agents fully posted (all 3 platforms). Used for history / idempotency check. |
| `total` | Integer | Total number of agents in the series (e.g. 6). |

## Update Pattern (per cron tick)

After successfully posting agent `N` to all 3 platforms:

1. Set `agents[N].posted_ig = true`
2. Set `agents[N].posted_li = true`
3. Set `agents[N].posted_fb = true`
4. Increment `next_index` by 1 (so next tick picks up `N+1`)
5. Append `agents[N].name` to `posted` array
6. Write full JSON back to disk

## Completion Check

When `next_index >= total` (or `next_index >= len(agents)`), all agents are done. Emit success message and stop — no more cron ticks needed.

## Pitfalls

- **Use absolute paths in cron context.** Cron runs from a minimal working directory. Always use the full path (`/opt/data/profiles/saksit/scripts/...` or `~/.hermes/profiles/saksit/scripts/...`).
- **0-based vs 1-based:** `next_index` is 0-based. When the first agent (index 0) is already posted manually, set `next_index = 1` to start the cron from the second agent.
- **Per-agent flags** (`posted_ig`, `posted_li`, `posted_fb`) mirror the `posted` array but at finer granularity — useful if a single platform fails and needs retry without re-posting the other two.
- **`write_file` not `execute_code` for cron updates.** `execute_code` is blocked for cron jobs (requires interactive approval mode). Use `write_file` or `patch` to update the state file from cron context.
