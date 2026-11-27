# Framework Migration Patterns

## Step 5: Add MCP App Initialization Alongside Existing Logic

This is the core step. Instead of replacing the app's data sources, add an alternative initialization path for MCP mode. The app detects its environment at startup and reads parameters from the right source.

### The Hybrid Pattern

```typescript
import { App, PostMessageTransport } from "@modelcontextprotocol/ext-apps";

// Detect whether we're running inside an MCP host.
// Choose a detection method that fits the app:
//   - Origin check: window.location.origin !== 'https://myhost.com'
//   - Null origin (sandboxed iframe): window.location.origin === 'null'
//   - Query param: new URL(location.href).searchParams.has('mcp')
const isMcpApp = window.location.origin === "null";

async function getParameters(): Promise<Record<string, string>> {
  if (isMcpApp) {
    // Running as MCP App — get params from tool lifecycle
    const app = new App({ name: "My App", version: "1.0.0" });

    // Register handlers BEFORE connect()
    const params = await new Promise<Record<string, string>>((resolve) => {
      app.ontoolresult = (result) => resolve(result.structuredContent ?? {});
    });

    await app.connect(new PostMessageTransport());
    return params;
  } else {
    // Running as standalone web app — get params from URL
    return Object.fromEntries(new URL(location.href).searchParams);
  }
}

async function main() {
  const params = await getParameters();
  renderApp(params); // Same rendering logic for both modes
}

main().catch(console.error);
```

### URL Parameters (Hybrid)

```typescript
// Before (standalone only):
const query = new URL(location.href).searchParams.get("q");
renderApp(query);

// After (hybrid):
async function getQuery(): Promise<string> {
  if (isMcpApp) {
    const app = new App({ name: "My App", version: "1.0.0" });
    return new Promise((resolve) => {
      app.ontoolinput = (params) => resolve(params.arguments?.q ?? "");
      app.connect(new PostMessageTransport());
    });
  }
  return new URL(location.href).searchParams.get("q") ?? "";
}

const query = await getQuery();
renderApp(query); // Unchanged rendering logic
```

### API Calls (Hybrid)

```typescript
// Before (standalone only):
const data = await fetch("/api/data").then(r => r.json());

// After (hybrid):
async function fetchData(): Promise<any> {
  if (isMcpApp) {
    const result = await app.callServerTool("fetch-data", {});
    return result.structuredContent;
  }
  return fetch("/api/data").then(r => r.json());
}
```

Or keep direct API calls in both modes with CSP `connectDomains`:

```typescript
// API calls can stay unchanged if the API is external and the CSP declares the domain
// Declare connectDomains: ["api.example.com"] in the resource registration
```

### localStorage / sessionStorage (Hybrid)

```typescript
// Before (standalone only):
const saved = localStorage.getItem("settings");

// After (hybrid) — localStorage isn't available in sandboxed iframes:
function getSettings(): any {
  if (isMcpApp) {
    // Will be provided via tool result
    return null; // or a default
  }
  return JSON.parse(localStorage.getItem("settings") ?? "null");
}
```

### Complete Hybrid Example

```typescript
import { App, PostMessageTransport, applyDocumentTheme, applyHostStyleVariables, applyHostFonts } from "@modelcontextprotocol/ext-apps";

const isMcpApp = window.location.origin === "null";

async function initMcpApp(): Promise<Record<string, any>> {
  const app = new App({ name: "My App", version: "1.0.0" });

  // Register ALL handlers BEFORE connect()
  const params = await new Promise<Record<string, any>>((resolve) => {
    app.ontoolinput = (input) => resolve(input.arguments ?? {});
  });

  app.onhostcontextchanged = (ctx) => {
    if (ctx.theme) applyDocumentTheme(ctx.theme);
    if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
    if (ctx.styles?.css?.fonts) applyHostFonts(ctx.styles.css.fonts);
    if (ctx.safeAreaInsets) {
      const { top, right, bottom, left } = ctx.safeAreaInsets;
      document.body.style.padding = `${top}px ${right}px ${bottom}px ${left}px`;
    }
  };

  app.onteardown = async () => {
    return {};
  };

  await app.connect(new PostMessageTransport());
  return params;
}

async function initStandaloneApp(): Promise<Record<string, any>> {
  return Object.fromEntries(new URL(location.href).searchParams);
}

async function main() {
  const params = isMcpApp ? await initMcpApp() : await initStandaloneApp();
  renderApp(params); // Same rendering logic — no fork needed
}

main().catch(console.error);
```

## Step 6: Add Host Styling Integration (MCP Mode Only)

When running as an MCP App, integrate with host styling for theme consistency. Use CSS variable fallbacks so the app looks correct in both modes.

**Vanilla JS** — use helper functions:
```typescript
import { applyDocumentTheme, applyHostStyleVariables, applyHostFonts } from "@modelcontextprotocol/ext-apps";

app.onhostcontextchanged = (ctx) => {
  if (ctx.theme) applyDocumentTheme(ctx.theme);
  if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
  if (ctx.styles?.css?.fonts) applyHostFonts(ctx.styles.css.fonts);
};
```

**React** — use hooks:
```typescript
import { useApp, useHostStyles } from "@modelcontextprotocol/ext-apps/react";

const { app } = useApp({ appInfo, capabilities, onAppCreated });
useHostStyles(app);
```

**Using variables in CSS** — use `var()` with fallbacks so standalone mode still looks right:

```css
.container {
  background: var(--color-background-secondary, #f5f5f5);
  color: var(--color-text-primary, #333);
  font-family: var(--font-sans, system-ui);
  border-radius: var(--border-radius-md, 8px);
}
```

Key variable groups: `--color-background-*`, `--color-text-*`, `--color-border-*`, `--font-sans`, `--font-mono`, `--font-text-*-size`, `--font-heading-*-size`, `--border-radius-*`. See `src/spec.types.ts` for the full list.

## Optional Enhancements

### App-Only Helper Tools

For data the UI needs to poll or fetch that the model doesn't need to call directly:

```typescript
registerAppTool(server, "refresh-data", {
  description: "Fetches latest data for the UI",
  _meta: { ui: { resourceUri, visibility: ["app"] } },
}, async () => {
  const data = await getLatestData();
  return { content: [{ type: "text", text: JSON.stringify(data) }] };
});
```

The UI calls these via `app.callServerTool("refresh-data", {})`.

### Streaming Partial Input

For large tool inputs, use `ontoolinputpartial` to show progress during LLM generation:

```typescript
app.ontoolinputpartial = (params) => {
  const args = params.arguments; // Healed partial JSON - always valid
  renderPreview(args);
};

app.ontoolinput = (params) => {
  renderFull(params.arguments);
};
```

### Fullscreen Mode

```typescript
app.onhostcontextchanged = (ctx) => {
  if (ctx.availableDisplayModes?.includes("fullscreen")) {
    fullscreenBtn.style.display = "block";
  }
  if (ctx.displayMode) {
    container.classList.toggle("fullscreen", ctx.displayMode === "fullscreen");
  }
};

async function toggleFullscreen() {
  const newMode = currentMode === "fullscreen" ? "inline" : "fullscreen";
  const result = await app.requestDisplayMode({ mode: newMode });
  currentMode = result.mode;
}
```

### Text Fallback

Always provide a `content` array for non-UI hosts:

```typescript
return {
  content: [{ type: "text", text: "Fallback description of the result" }],
  structuredContent: { /* data for the UI */ },
};
```

## Common Mistakes to Avoid

1. **Forgetting CSP declarations for external origins** — fails silently in the sandboxed iframe
2. **Using `localStorage` / `sessionStorage` in MCP mode** — not available in sandboxed iframe; use fallbacks or pass via `structuredContent`
3. **Missing `vite-plugin-singlefile`** — external assets won't load in the iframe
4. **Registering handlers after `connect()`** — register ALL handlers BEFORE calling `app.connect()`
5. **Hardcoding styles without fallbacks** — use host CSS variables with `var(..., fallback)` so both modes look correct
6. **Not handling safe area insets** — always apply `ctx.safeAreaInsets` in `onhostcontextchanged`
7. **Forgetting text `content` fallback** — always provide `content` array for non-UI hosts
8. **Forgetting resource registration** — the tool references a `resourceUri` that must have a matching resource
9. **Replacing standalone logic instead of branching** — keep the original data sources intact; add the MCP path alongside them

## Testing

### Using basic-host

Test the MCP App mode with the basic-host example:

```bash
# Terminal 1: Build and run your server
npm run build && npm run serve

# Terminal 2: Run basic-host (from cloned repo)
cd /tmp/mcp-ext-apps/examples/basic-host
npm install
SERVERS='["http://localhost:3001/mcp"]' npm run start
# Open http://localhost:8080
```

Configure `SERVERS` with a JSON array of your server URLs (default: `http://localhost:3001/mcp`).

### Verify

1. **MCP mode**: App loads in basic-host without console errors
2. `ontoolinput` handler fires with tool arguments
3. `ontoolresult` handler fires with tool result
4. Host styling (theme, fonts, colors) applies correctly
5. External resources load (if CSP domains are configured)
6. **Standalone mode**: App still works when opened directly in a browser