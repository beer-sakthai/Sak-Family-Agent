# Six-Agent Diagnosis Report

## Summary

This repository now reflects the full six-agent Sak Family roster:
SakKing, SakThai, SakSee, SakSit, SakTan, and SakJules.

The current diagnosis is that the identity and persona sources are broadly in
shape, but the repo still needed one cleanup pass for consistency:

- `5_agents_summary.md` was stale and omitted SakJules.
- `infra/hermes-agents/README.md` still had a five-agent skills table.
- SakTan and SakJules need explicit standalone-run callouts because they lean
  harder on the Hermes profile layer than the others.
- The standalone build tree has now been exercised for both SakTan and SakJules
  so the export/composition path is covered for all six personas.

## Benchmark Rubric

Scores are 1-5, where 5 is best.

| Agent | Identity | Runtime | Standalone | Tools / MCP | Docs | Notes |
|---|---:|---:|---:|---:|---:|---|
| SakKing | 5 | 4 | 4 | 5 | 4 | Strong lead/orchestrator coverage; reserved `default` profile is the special case. |
| SakThai | 5 | 4 | 4 | 5 | 4 | Cleanly documented Hugging Face specialist; runtime depends on Anthropic/Ollama-cloud auth. |
| SakSee | 5 | 4 | 4 | 5 | 4 | Web/browser stack is clear and well scoped. |
| SakSit | 5 | 4 | 4 | 4 | 4 | Social-media role is coherent, but the runtime depends on HF Spaces plus the Modal sandbox. |
| SakTan | 5 | 3 | 4 | 3 | 3 | The helper role is clear, and the export/composition path now verifies its standalone tree. |
| SakJules | 5 | 3 | 4 | 4 | 3 | Identity is now correct, and the export/composition path now verifies its standalone tree. |

## Standalone Requirements

### SakKing

- `infra/hermes-agents/default/SOUL.md`
- `infra/hermes-agents/default/config.yaml`
- Playwright, Chrome DevTools, Hugging Face, and HF media MCP access
- Shared memory and the common skill library

### SakThai

- `personas/sakthai/SOUL.md`
- `personas/sakthai/config/`
- Hugging Face MCP access
- Shared memory and the common skill library

### SakSee

- `personas/saksee/SOUL.md`
- `personas/saksee/config/`
- Playwright and Chrome DevTools MCP access
- Shared memory and the common skill library

### SakSit

- `personas/saksit/SOUL.md`
- `personas/saksit/config/`
- Hugging Face Spaces for image/video generation
- Modal-backed terminal sandbox for content workflows
- Shared memory and the common skill library

### SakTan

- `personas/saktan/SOUL.md`
- `personas/saktan/config/`
- Gemini auth
- Hermes profile runtime wiring for daily ops
- Shared memory and the common skill library

### SakJules

- `personas/sakjules/SOUL.md`
- `personas/sakjules/config/`
- Gemini auth
- GitHub MCP access
- Composio MCP access
- Hermes profile runtime wiring for repository stewardship
- Shared memory and the common skill library

## Standalone Run Checklist

Use this as the minimum “can I run this agent by itself?” check.

### SakKing

- Use the reserved `default` Hermes profile, not a `profiles/sakking/` folder.
- Confirm `infra/hermes-agents/default/SOUL.md` and `config.yaml` are present.
- Confirm the lead tool surface is wired for Playwright, Chrome DevTools,
  Hugging Face, and HF media generation.
- Confirm shared memory access is available.

### SakThai

- Confirm `personas/sakthai/SOUL.md` and `personas/sakthai/config/` exist.
- Confirm Hugging Face MCP access is configured.
- Confirm shared memory access is available.

### SakSee

- Confirm `personas/saksee/SOUL.md` and `personas/saksee/config/` exist.
- Confirm Playwright and Chrome DevTools MCP access is configured.
- Confirm shared memory access is available.

### SakSit

- Confirm `personas/saksit/SOUL.md` and `personas/saksit/config/` exist.
- Confirm Hugging Face Spaces access for image/video generation is configured.
- Confirm the Modal-backed terminal sandbox path is available.
- Confirm shared memory access is available.

### SakTan

- Confirm `personas/saktan/SOUL.md` and `personas/saktan/config/` exist.
- Confirm Gemini auth is available.
- Confirm the Hermes profile runtime wiring for daily ops is present.
- Confirm shared memory access is available.

### SakJules

- Confirm `personas/sakjules/SOUL.md` and `personas/sakjules/config/` exist.
- Confirm Gemini auth is available.
- Confirm GitHub MCP access is configured.
- Confirm Composio MCP access is configured.
- Confirm the Hermes profile runtime wiring for repository stewardship is present.
- Confirm shared memory access is available.

## Diagnosis

The family is structurally sound, but the highest-value fixes were documentation
alignment and explicit standalone run guidance.

Top issues:

1. The old five-agent summary was the most visible mismatch. That is now fixed.
2. SakJules needed to be treated as a first-class citizen everywhere the roster
   or skill table is shown. That is now explicit.
3. SakTan and SakJules are the two agents most likely to be misunderstood if
   the Hermes profile layer is not called out.
4. The export/composition path was exercised for both new standalone personas,
   which confirms the build tree stays honest.

## Practical Read

If you want the shortest possible operational view:

- SakKing: lead/orchestrator, strongest coding coverage, reserved profile.
- SakThai: Hugging Face specialist.
- SakSee: browser/web specialist.
- SakSit: social-media content specialist.
- SakTan: daily-ops helper.
- SakJules: GitHub repository steward.

That division is now reflected consistently across the family docs.
