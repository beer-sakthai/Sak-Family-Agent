---
name: hf-knowledge-curation
description: "Autonomous Hugging Face knowledge curation — learning-loop pattern for cron jobs and agents: discover new HF subtopics, avoid duplicates, research from external sources, and author class-level skills. Covers fallback strategies when primary scraping paths fail."
category: mlops
---

# Hugging Face Knowledge Curation

Use this skill when asked to run a learning loop: periodically pick a fresh, specific Hugging Face / AI subtopic, research it, and save a reusable class-level skill.

## Workflow

1. **Deduplicate and validate viability first**
   - List existing skills (`skills_list`, `find .../SKILL.md`) in the target profile.
   - Search Supermemory (`mcp_supermemory_recall query="hf ..."`) for prior sessions on the topic.
   - Do NOT create a skill that already exists.
   - **Check project health**: Before investing in a full skill, verify the upstream project is actively maintained (check GitHub README/archived status, last commit date, PyPI version recency). If a project is deprecated/archived, capture it as a memory note or add a deprecation subsection to an existing related skill rather than building a full class-level skill around it.

2. **Pick a novel, class-level subtopic**
   - Prefer class-level umbrellas over one-off narrative skills.
   - Good: "Hugging Face Optimum" (library), "Inference Providers", "XET protocol".
   - Bad: "How I debugged X today", "Summary of paper Y", "Fix error Z on 2026-06-21".

3. **Research with graceful fallback**
   - Prefer `web_search` to find authoritative sources (docs.huggingface.co, GitHub, DeepWiki).
   - Use `web_extract` for clean markdown content.
   - **Billing-error fallback**: If `web_extract` returns HTTP 402 / `BILLING_ERROR` / `Charge authorization failed`, do not retry. Switch immediately to `web_search` for alternate hosts or `curl` against `raw.githubusercontent.com` / `raw.gitmirror.com`.
   - If `web_extract` fails twice on similar domains (billing errors, loop-warning, or repeated timeouts), pivot:
     - Try `browser_navigate` + `browser_snapshot` on the same URL or a GitHub raw path.
     - Use `web_search` to find an alternate host (e.g., DeepWiki, `raw.githubusercontent.com`, Blogs).
   - Do not continue the same failing path after a loop-warning.

4. **Author class-level skills**
   - Target shape: umbrella SKILL.md + `references/`, `templates/`, `scripts/` directories.
   - New skill path: `~/.hermes/profiles/<profile>/skills/<category>/hf-<slug>/SKILL.md`.
   - After non-trivial research or a non-obvious workaround, save the technique as a skill rather than just a memory entry.
   - **Cross-profile writes**: The active cron profile may differ from the target profile (e.g., `sakthai` writing to `hermesagent`). The filesystem soft-guard will block writes unless `cross_profile=True` is passed to `write_file`/`patch`. In review phases where `write_file` is denied even after creation, record the intended support file path in Supermemory for the next session to create.
   - **Sibling skill mapping**: If the new skill overlaps with an existing sibling skill (e.g., `hf-inference-client` vs `hf-inference-providers`), add a `references/related-skills.md` file noting the boundary and differentiation matrix.

5. **Delivery format** (required when a new skill is created)
   - Output format for the cron user:
     - "Learned `<TOPIC>`. New skill saved to `<PATH>`."
     - Bullet list of 3–5 key facts learned.
     - Optional: brief note on next-step usage or fallback commands.

6. **Record in Supermemory**
   - Save a durable entry summarizing the new skill topic, file path, and key facts.
   - If research is genuinely blocked and you would have to fabricate, record the no-op instead and stay silent.

   **GitHub API for repo structure**: When directory listings are unavailable, use `/repos/{owner}/{repo}/git/trees/main?recursive=1` to enumerate source files, then filter by extension or path to locate modules for direct extraction.

## Case study: HF Official MCP Server (2026-06-21)

- **Topic**: `Hugging Face Official MCP Server` (`hf-mcp-server`)
- **Skill path**: `~/.hermes/profiles/hermesagent/skills/mlops/hf-mcp-server/SKILL.md`
- **Research challenge**: `web_extract` failed repeatedly with HTTP 402 billing errors against `huggingface.co` and GitHub.
- **Workaround used**: `curl` against `raw.githubusercontent.com` to fetch README and TypeScript source; GitHub API `/git/trees` to enumerate the package tree; then targeted extraction of `tool-ids.ts`, `jobs-tool.ts`, `sandbox-tool.ts`, `dynamic-space-tool.ts`, `hub-inspect.ts`, and search tool definitions.
- **Outcome**: Successfully authored a class-level skill covering 17+ built-in tools, 3 transports, proxy-tool CSV loading, bouquet selection, SEP-2640 skills distribution, and client setup for Claude Desktop/Cursor/VSCode/Gemini.

## Pitfalls

- **Flat skills are discouraged.** A skill that only makes sense for a single session, PR, or date is a memory entry, not a skill.
- **Do not hardcode broken tools as permanent constraints.** If a tool fails, capture the retry/switching pattern, not the failure itself.
- **Loop-detection is real.** When the tool runtime warns about repeated identical failures, switch approach immediately.