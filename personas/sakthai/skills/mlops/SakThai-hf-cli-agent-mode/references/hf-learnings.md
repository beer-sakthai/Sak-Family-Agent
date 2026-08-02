# HF Learnings — hf CLI Agent Mode

## 2026-07-25: hf-cli-agent-mode-deep-dive — Hugging Face hf CLI Agent-Optimized Mode (Topic #314)

### Summary
Deep dive into the `hf` CLI v1.9.0+ agent-optimized mode. Covers auto-detection of coding agents (Claude Code, Codex, Cursor, etc.), dual rendering (human vs agent output formats), the auto-generated skill system, safe retry semantics (`--exist-ok`, `--yes`, `--dry-run`), next-command hints, composable output (`-q`, `--json`, `--quiet`), and the benchmark results comparing CLI vs curl/Python SDK across ~1,000 graded runs on 18 Hub tasks. The CLI achieves 94% task success on Sonnet (vs 84% without it) and burns 1.3–6× fewer tokens on complex multi-step workflows.

### Key Findings

| Aspect | Detail |
|--------|--------|
| **Detection** | Reads CLAUDECODE, CODEX_SANDBOX, AI_AGENT, CURSOR env vars |
| **Agent output** | TSV format, no truncation, no ANSI, ISO 8601, all tags, stderr guidance |
| **Human output** | Aligned tables, ANSI color, truncated to fit, green ✅ on success |
| **Skill effect** | ~30% fewer tool calls (10.4→6.9 Sonnet, 10.1→7.3 GPT-5.5) |
| **Safe retry** | --exist-ok, -y/--yes, --dry-run on destructive/data-move commands |
| **Token savings** | 1.3–1.8× overall, 2.4–6× on multi-step tasks (bucket sync, org ranking) |
| **Simple reads** | Near parity or cheaper via curl/SDK (0.3–0.5×) |
| **Error handling** | Errors go to stderr with fix command; never prompts in agent mode |

### Benchmark Detail (18 tasks, ~1,000 graded runs)

| Agent | Tool | Success | Self-report errors | Token vs baseline |
|-------|------|---------|-------------------|-------------------|
| Claude Code (Sonnet 4.6) | `hf` CLI | **0.94** | 2/163 | baseline |
|  | curl/Python SDK | 0.84 | 11/163 | 1.3–1.6× |
| Codex (GPT-5.5) | `hf` CLI | **0.93** | 3/163 | baseline |
|  | curl/Python SDK | 0.92 | 10/163 | 1.6–1.8× |

Per-task token ratios for curl/SDK vs CLI (GPT-5.5): bucket create+sync+prune 6.0×, rank org trending models 4.1×, repo create+branch+tag / delete files / copy files across repos 2.4× each. Simple reads: batch model metadata 0.5×, count dataset rows 0.3×.

### Agent Harness Registration
Any agent harness can register by PR to `agent-harnesses.ts` in huggingface.js. Guide at `/docs/hub/agents-overview#register-your-agent-harness`.

### Skill Created
`mlops/hf-cli-agent-mode/` — SKILL.md + references/hf-learnings.md covering agent-optimized CLI design, detection, rendering modes, skill system, benchmark results, and best practices.

### Sources
- https://huggingface.co/blog/hf-cli-for-agents (primary source)
- https://huggingface.co/docs/huggingface_hub/guides/cli
- https://huggingface.co/docs/hub/agents-overview
