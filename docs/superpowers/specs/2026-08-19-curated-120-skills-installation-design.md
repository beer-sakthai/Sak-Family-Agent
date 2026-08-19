# Curated 120-Skill Architecture & Multi-Agent Installation Specification

**Author:** SakJules (Master of Automation & CI/CD)  
**Date:** 2026-08-19  
**Status:** Approved  
**Target Repositories & Environments:** `Sak-Family-Agent`, `sakthai-agent-v2`, `~/.agents/skills`, `~/.gemini/config/skills`

---

## 1. Executive Summary

From an audited catalog of 1,115 operational skills, this specification codifies the Top 120 High-Impact Skills across 6 strategic pillars to optimize repository operations, automated CI/CD quality gates, AST security containment, Google Cloud ADK telemetry, Hugging Face MLOps, and inter-agent coordination.

---

## 2. The 6 Strategic Pillars (20 Skills per Pillar)

### Pillar 1: AST Security & Vulnerability Containment (20 Skills)
1. `saksee-security-scan`
2. `saksee-path-traversal-guard`
3. `saksee-command-injection-blocker`
4. `sakjules-redteam-fuzzer`
5. `sakjules-cipher-decoder`
6. `saksee-doctor`
7. `saksee-secret-scanner`
8. `saksee-codeql-remediation`
9. `saksee-bandit-security`
10. `saksee-ast-guardrail-parity`
11. `sakjules-devsecops`
12. `security-patcher`
13. `analyze-full`
14. `analyze-github-pr`
15. `dependency-manager`
16. `poc`
17. `sakking-github-security-compliance`
18. `saksee-cloudflare-turnstile`
19. `saksee-webauthn-storage`
20. `sakjules-asset-monitor`

### Pillar 2: CI/CD, Mutation Testing & Self-Healing (20 Skills)
21. `sakjules-ci-fixer`
22. `sakjules-mutation-testing`
23. `sakjules-self-healing-test-generator`
24. `sakjules-pylint-ruff-matrix`
25. `sakjules-mypy-strict`
26. `sakjules-playwright-headless`
27. `sakjules-playwright-html-report`
28. `sakjules-github-actions-concurrency`
29. `sakjules-pnpm-turbopack-build`
30. `sakjules-git-commit`
31. `sakjules-claude-settings-hooks`
32. `sakjules-test-driven-development`
33. `sakjules-coverage-governor`
34. `sakjules-dependabot-audit`
35. `sakjules-release-drafter`
36. `sakjules-scorecard-supply-chain`
37. `sakjules-subproject-test-runner`
38. `sakjules-cron-fleet-watchdog`
39. `sakjules-benchmark-latency`
40. `sakjules-quick-fix`

### Pillar 3: Google ADK & Cloud Native Operations (20 Skills)
41. `google-agents-cli-adk-code`
42. `google-agents-cli-observability`
43. `google-agents-cli-deploy`
44. `google-agents-cli-eval`
45. `google-agents-cli-scaffold`
46. `google-agents-cli-workflow`
47. `google-agents-cli-publish`
48. `sakthai-gemini-live-api`
49. `sakthai-gemini-2-flash-routing`
50. `sakthai-cloud-run-terraform`
51. `sakthai-bigquery-telemetry-stream`
52. `sakthai-gcp-secret-manager`
53. `sakthai-gke-helm-orchestrator`
54. `sakthai-cloud-monitoring-alerts`
55. `sakthai-gemini-sdk-python`
56. `sakthai-genkit-bridge`
57. `sakthai-vertex-ai-endpoint`
58. `sakthai-cloud-sql-pgvector`
59. `sakthai-google-workspace-gws`
60. `sakthai-adk-a2a-bridge`

### Pillar 4: Hugging Face MLOps, Models & Spaces (20 Skills)
61. `hf-cli`
62. `sakthai-hf-peft-lora`
63. `sakthai-hf-datasets`
64. `sakthai-hf-hub-contents-api`
65. `sakthai-hf-inference-endpoints`
66. `sakthai-hf-safetensors`
67. `sakthai-hf-smolagents`
68. `sakthai-hf-repocard-system`
69. `sakthai-hf-spaces-docker`
70. `sakthai-hf-spaces-zerogpu`
71. `sakthai-hf-sentence-transformers`
72. `sakthai-hf-mergekit`
73. `sakthai-hf-trl`
74. `sakthai-hf-transformers-cache`
75. `sakthai-hf-jobs-api`
76. `sakthai-hf-data-studio-sql`
77. `sakthai-hf-distilabel`
78. `sakthai-hf-open-llm-leaderboard`
79. `sakthai-hf-tts`
80. `sakthai-hf-security-scanning`

### Pillar 5: Multi-Agent Orchestration & A2A Protocols (20 Skills)
81. `a2a-service-registry`
82. `superpowers-subagent-driven-development`
83. `superpowers-dispatching-parallel-agents`
84. `superpowers-executing-plans`
85. `superpowers-writing-plans`
86. `sakking-supervisor`
87. `sakking-war-room-mesh`
88. `sakking-model-routing`
89. `sakking-agent-platform-skill-registry`
90. `sakking-agent-platform-rag-engine`
91. `sakking-agent-health-diagnostics`
92. `sakking-using-git-worktrees`
93. `saknoi-prompt-studio`
94. `saktan-token-analytics`
95. `saksit-continuous-learning-loop`
96. `saksit-diary-writer`
97. `sakthai-a2a-json-rpc-guard`
98. `sakking-consensus-voting`
99. `pm`
100. `team`

### Pillar 6: Code Quality, Semantic Caching & OODA Cycle (20 Skills)
101. `sakjules-semantic-cache-optimizer`
102. `sakthai-cycle-dream`
103. `sakthai-cycle-hope`
104. `sakthai-cycle-care`
105. `sakthai-cycle-joy`
106. `sakthai-cycle-trust`
107. `sakthai-cycle-growth`
108. `sakjules-simplify-code`
109. `saksee-systematic-debugging`
110. `sakjules-command-palette`
111. `stitch`
112. `design`
113. `api-design`
114. `code-review`
115. `compound-docs`
116. `persistence`
117. `db`
118. `brainstorm`
119. `refactor`
120. `watzup`

---

## 3. Registration Targets & Locations

The installer targets three primary discovery directories:
1. **Gemini CLI Configuration:** `/home/beern/.gemini/config/skills/`
2. **Antigravity Global Registry:** `/home/beern/.agents/skills/`
3. **Workspace Project Registry:** `/home/beern/Sak-Family-Agent/.agents/skills/`

---

## 4. Verification & Quality Invariants
- 100% of the 120 skills must contain valid YAML frontmatter delimiters (`---`).
- Valid `name:` and `description:` fields (>15 characters) for LLM progressive disclosure.
- Zero broken symlinks across all target directories.
