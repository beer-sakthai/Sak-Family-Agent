# MEMORY.md — SakSee 👁️
> *QA, Playwright, DevTools & Vision Computer Use Memory Store*

---

## 🧠 Permanent System Bindings

- **Hermes Profile Path**: `~/.hermes/profiles/saksee/`
- **Active Model Engine**: `gemini-3.5-flash` / `gemini-2.5-flash`
- **Vision Computer Use Daemon**: `/home/beern/start_cua_daemon.sh` (socket: `~/.cache/cua-driver/cua-driver.sock`)
- **SakSeeBrowser Runner**: [`/home/beern/run_saksee.sh`](file:///home/beern/run_saksee.sh) (`/home/beern/saksee_browser_agent.py`)

---

## 🛠️ Active Connected MCP Servers & Skill Tools

- **`cua-driver`**: `browser_click`, `browser_type`, `browser_scroll`, `get_desktop_state`
- **`chrome-devtools-mcp`**: DOM tree parsing, console error enrichment, network call tracking
- **`stitch`**: Google Stitch code-to-design, UI generation, and visual layout diffing
- **`supermemory`**: Local semantic memory endpoint (`http://localhost:6767`)

---

## 📋 Verified Execution Log & Benchmarks

1. **Browser Navigation & Vision Computer Use**: Verified 1-step navigation loop to `https://example.com` returning clean text response and saving visual screenshot to `saksee_last_screenshot.png`.
2. **Playwright Unit Test Suite**: `tests/test_saksee_agent.py` passing 100% cleanly.
3. **Dual Agent Verification**: Successfully executed live dual query via Hermes (`hermes --profile saksee --provider google -m gemini-2.5-flash`).

---

*Last Synchronized: August 2026 · Sak-Family-Agent Memory Node*
