---
name: SakSit-learned-oc-architecture
description: OpenClaw Plugin SDK architecture reference.
version: 1.0.0
author: SakSit (cron research)
openclaw_upstream: https://github.com/openclaw/openclaw
category: social-media
tags:
- OpenClaw
- Reference
---

# Learned: OpenClaw Plugin SDK Architecture

## Topic
**OpenClaw Plugin SDK & Load Pipeline** — how OpenClaw's plugin system works: the capability registration model, plugin shapes, the 4-layer load pipeline, manifest-first design, metadata snapshot system, and the 60+ subpath SDK export architecture.

## Why This Matters for SakSit
OpenClaw is the upstream framework that Hermes Agent (which SakSit runs on) is built from. Understanding the plugin architecture explains how tools, providers, channels, and skills get loaded — crucial context for debugging, extending, or explaining the stack to Beer.

## Key Findings

### 1. Capability Model

Every native OpenClaw plugin registers against one or more **capability types** via methods on `OpenClawPluginApi`:

| Capability | Registration Method | Examples |
|------------|-------------------|----------|
| Text inference | `api.registerProvider(...)` | anthropic, openai |
| CLI inference backend | `api.registerCliBackend(...)` | anthropic, openai |
| Embeddings | `api.registerEmbeddingProvider(...)` | Provider-owned vector plugins |
| Speech | `api.registerSpeechProvider(...)` | elevenlabs, microsoft |
| Realtime transcription | `api.registerRealtimeTranscriptionProvider(...)` | openai |
| Realtime voice | `api.registerRealtimeVoiceProvider(...)` | google, openai |
| Media understanding | `api.registerMediaUnderstandingProvider(...)` | google, openai |
| Image generation | `api.registerImageGenerationProvider(...)` | fal, google, openai |
| Music generation | `api.registerMusicGenerationProvider(...)` | fal, google, minimax |
| Video generation | `api.registerVideoGenerationProvider(...)` | fal, google, qwen |
| Web fetch | `api.registerWebFetchProvider(...)` | firecrawl |
| Web search | `api.registerWebSearchProvider(...)` | brave, firecrawl, google |
| Channel / messaging | `api.registerChannel(...)` | matrix, msteams |
| Gateway discovery | `api.registerGatewayDiscoveryService(...)` | bonjour |
| Transcripts source | `api.registerTranscriptSourceProvider(...)` | discord, google-meet, teams-meetings |

### 2. Plugin Shapes

OpenClaw classifies every loaded plugin into a **shape** based on actual registration behavior:

- **plain-capability** — exactly one capability type (e.g. `arcee`, `chutes`)
- **hybrid-capability** — multiple capability types (e.g. `openai` owns text + speech + media + image gen)
- **hook-only** — only hooks, no capabilities/tools/commands/services (legacy pattern, still supported)
- **non-capability** — tools, commands, or services but no capabilities

### 3. The 4-Layer Load Pipeline

| Layer | What Happens |
|-------|-------------|
| **1. Manifest + Discovery** | OpenClaw finds candidates from config paths, workspace roots, global roots, and bundled plugins. Reads `openclaw.plugin.json` manifests first. |
| **2. Enablement + Validation** | Core decides enabled/disabled/blocked/slot-selected. Safety gates check path ownership, world-writability, and entry-point escape before runtime execution. |
| **3. Runtime Loading** | Native plugins load in-process; bundled via native require, third-party TS via Jiti fallback. Call `register(api)` into central registry. |
| **4. Surface Consumption** | Rest of OpenClaw reads the registry to expose tools, channels, provider setup, hooks, HTTP routes, CLI commands, and services. |

**Safety gates** block candidates whose entry escapes the plugin root, are world-writable, or (for non-bundled) don't match the current uid. World-writable bundled dirs get a `chmod` repair attempt first.

### 4. Manifest-First Design

The manifest is the **control-plane** source of truth. It identifies the plugin, declares channels/skills/config schema, drives validation, and enables `activation` / `setup` metadata descriptors — all **without loading plugin runtime code**. The runtime module is the **data-plane** part that registers actual behavior.

Manifest `activation` hints narrow loading:
- `activation.onStartup` → explicit startup imports
- `activation-channel-hint` → narrows to channel-owning plugins
- `activation-command-hint` → narrows to command-owning plugins
- `activation-provider-hint` → narrows to provider-owning plugins

### 5. Metadata Snapshot System

Gateway startup builds a `PluginMetadataSnapshot` (metadata-only: plugin index, manifest registry, diagnostics, owner maps). A derived `PluginLookUpTable` adds the startup plugin plan. These snapshots keep repeated startup decisions on the **fast path** — channel ownership, deferred startup, startup plugin ids — without re-running cold discovery.

The snapshot is **not cached behind wall-clock windows** — it's explicitly passed through the call chain and rebuilt/replaced when config changes.

### 6. Plugin SDK Subpath Export Architecture

The `@openclaw/plugin-sdk` package exports **60+ subpaths** (not a single barrel) — each a self-contained module for fast startup and no circular deps:

- `openclaw/plugin-sdk/plugin-entry` — definePluginEntry
- `openclaw/plugin-sdk/core` — umbrella surface + shared helpers
- `openclaw/plugin-sdk/channel-core` — channel entry/build helpers
- `openclaw/plugin-sdk/provider-auth` — provider auth helpers
- `openclaw/plugin-sdk/plugin-runtime` — plugin runtime helpers
- `openclaw/plugin-sdk/config-runtime` — config runtime
- `openclaw/plugin-sdk/exec-approvals-runtime` — execution approval API
- And many more covering auth flows, error handling, media, TTS, file access, cron stores, secrets, etc.

**Golden rule for plugin authors:** Import from a specific subpath, never from `openclaw/plugin-sdk` directly or from provider-branded seams (e.g. `openclaw/plugin-sdk/slack`).

### 7. Compatibility Stance

- Existing external plugins → keep hook-based integrations working (baseline)
- New bundled/native plugins → prefer explicit capability registration
- External plugins adopting capability registration → allowed, treat evolving surfaces as unstable unless docs mark them stable

## Source References
- OpenClaw Plugin architecture docs: `docs/plugins/architecture.md`, `docs/plugins/architecture-internals.md`
- Plugin SDK overview: `docs/plugins/sdk-overview.md`
- Building plugins guide: `docs/plugins/building-plugins.md`
- SDK subpath reference: `docs/plugins/sdk-subpaths.md`
- Agent runtime architecture: `docs/agent-runtime-architecture.md`
- Plugin SDK package exports: `packages/plugin-sdk/package.json` (60+ subpath entries)
- Plugin package contract: `packages/plugin-package-contract/`
