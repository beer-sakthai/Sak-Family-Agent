# 🏛️ Sak-Family Monorepo Codebase Summary

**Architecture Overview, Persona Specializations, and Verification Matrix.**

---

## 🎯 Persona Architecture Matrix

| Persona | Lead Domain | Key Specializations & Toolkits |
| :--- | :--- | :--- |
| 👑 **SakKing** | Global Supervisor | Multi-agent quorum, high-level task decomposition, strategic governance |
| 🇹🇭 **SakThai** | Core Thai NLP & Reasoning | Bilingual Thai/English executive intelligence, persistent episodic memory |
| 🛡️ **SakSee** | Security Sentinel & AST | Zero-tolerance AST guardrail interceptor, path traversal & shell sanitization |
| ⚡ **SakJules** | CI/CD & Automation | Mutation testing, self-healing test generation, Vitest/Pytest CI gates |
| 📊 **SakTan** | Token Cost & Analytics | Semantic 64-D response cache, BigQuery telemetry streams, token velocity |
| 🎨 **SakNoi** | Prompt Design & Studio | High-dynamic-range prompts, persona tuning, stitch UI design integration |

---

## 📂 Core Subsystems Directory Tree

```
apps/sak_agent_dashboard/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── a2a/            # JSON-RPC 2.0 Agent-to-Agent Service Registry
│   │   │   ├── auto-cycle/     # 6-Part Cycle Intelligence State Controller
│   │   │   ├── cache/          # 64-D L2 Cosine Semantic Cache Endpoint
│   │   │   ├── eval/           # Quality Flywheel & G-Eval Benchmark Runner
│   │   │   ├── mutation/       # AST Mutation Testing & Self-Healing Generator
│   │   │   ├── redteam/        # Adversarial Prompt & Jailbreak Fuzzing Engine
│   │   │   └── telegram/       # Voice Bridge & Mobile Incident Alerts
│   │   └── page.tsx            # Unified Multi-Persona Dashboard & Studio Hub
│   ├── components/
│   │   ├── A2APanel.tsx
│   │   ├── AgentWarRoomPanel.tsx
│   │   ├── AutoCyclePanel.tsx
│   │   ├── CommandPaletteModal.tsx
│   │   ├── EvalQualityFlywheelPanel.tsx
│   │   ├── GoogleAdkBridgePanel.tsx
│   │   ├── TelegramVoiceBridgePanel.tsx
│   │   ├── cache/SemanticCachePanel.tsx
│   │   ├── mutation/MutationStudioPanel.tsx
│   │   ├── redteam/RedTeamStudioPanel.tsx
│   │   └── telegram/VoiceStudioWorkbench.tsx
│   ├── lib/
│   │   ├── a2a/                # A2A Service Registry & AST RPC validator
│   │   ├── adk/                # OpenTelemetry Trace Waterfall & BigQuery Analytics
│   │   ├── cache/              # 64-D Semantic Embedding & Cosine Cache Engine
│   │   ├── cycle/              # 6-Part Autonomous State Machine & Artifacts
│   │   ├── eval/               # Trajectory Scorer & Golden Benchmark Sets
│   │   ├── mutation/           # AST Fault Injector & Self-Healing Test Heuristics
│   │   ├── redteam/            # Base64 Cipher Decoder & Adversarial Threat Fuzzer
│   │   ├── voice/              # 24kHz PCM Audio Streamer & Persona Timbre Models
│   │   └── types.ts            # Global Domain Contracts & Typed Schemas
│   └── tests/                  # 100% Green Vitest Unit & Component Suites
```

---

## 🛡️ CI/CD Quality Gates & GitHub Actions

- `.github/workflows/quality-flywheel-gate.yml`: Automated multi-persona evaluation & trajectory benchmark gate.
- `.github/workflows/mutation-self-healing-gate.yml`: Automated mutation testing sweep with self-healing unit test generation for surviving mutants.

---

## 📊 Verification Summary

- **TypeScript Strict Compilation:** 0 errors (`pnpm tsc --noEmit` clean).
- **Next.js Turbopack Build:** 75 static routes / 42 dynamic REST endpoints compiled cleanly.
- **Vitest Test Matrix:** 100% green across unit, API, and React component test suites.
