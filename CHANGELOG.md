# Changelog

All notable changes to the `sakthai-agent-v2` project will be documented in this file.

---

## [2.2.0] — 2026-06-17
### Added
- **Unified Extension Paths**: Integrated automatic discovery of skills and MCP servers installed under the user's `~/.gemini/extensions/` path.
- **Namespaced Slash Commands**: Support for parsing and routing namespaced extension commands (e.g. `/plugin:command`) natively within the agent loop.
- **Caveman Mode Toggle**: Added `--caveman [lite|full|ultra]` flag to `sakthai run` to dynamically compress assistant output and save tokens.
- **User Preference Rules**: Copied user tone/style preference rules to `sakthai-personal` skill.

---

## [2.1.0] — 2026-06-16
### Added
- **Fast-Track Mode**: `--fast` flag to bypass the 6-stage verification cycle.
- **Memory Sync**: Remote memory backup and sync (`sakthai memory sync`) via Git and zero-dependency HTTP fallbacks.
- **Incremental Exports**: Transitioned snapshot generation to `facts.jsonl` and `observations.jsonl`.
- **Auto-Merge Conflict Resolver**: Local SQLite DB-based merge resolution during Git synchronizations.

---

## [2.0.0] — 2026-06-15
### Added
- **Stdio MCP Client**: Dynamic integration with external stdio-based MCP servers.
- **Provider Refactoring**: Split loops and moved Anthropic, OpenAI, Gemini, and Ollama providers to isolated package modules.
- **Streaming Output**: Native `--stream` token display.
- **Streamlit Activity Dashboard**: Session activity timelines and model token utilization statistics.
