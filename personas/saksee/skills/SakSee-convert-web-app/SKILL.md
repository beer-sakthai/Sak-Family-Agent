---
name: SakSee-convert-web-app
version: 1.0.0
description: This skill should be used when the user asks to add MCP App support to
  my web app, turn my web app into a hybrid MCP App, make my web page work as an MCP
  App too, wrap my existing UI as an MCP App, convert iframe embed to MCP App, turn
  my SPA into an
category: web-browser
tags:
- app
- browser
- convert
- web
---

# Add MCP App Support to a Web App

Add MCP App support to an existing web application so it works both as a standalone web app **and** as an MCP App that renders inline in MCP-enabled hosts like Claude Desktop — from a single codebase.

## How It Works

The existing web app stays intact. A thin initialization layer detects whether the app is running inside an MCP host or as a regular web page, and fetches parameters from the appropriate source. A new MCP server wraps the app's bundled HTML as a resource and registers a tool to display it.

```
Standalone:  Browser loads page → App reads URL params / APIs → renders
MCP App:     Host calls tool → Server returns result → Host renders app in iframe → App reads MCP lifecycle → renders
```

The app's rendering logic is shared — only the data source changes.

## Getting Reference Code

Clone the SDK repository for working examples and API documentation:

```bash
git clone --branch "v$(npm view @modelcontextprotocol/ext-apps version)" --depth 1 https://github.com/modelcontextprotocol/ext-apps.git /tmp/mcp-ext-apps
```

### API Reference (Source Files)

Read JSDoc documentation directly from `/tmp/mcp-ext-apps/src/`:

| File | Contents |
|------|----------|
| `src/app.ts` | `App` class, handlers (`ontoolinput`, `ontoolresult`, `onhostcontextchanged`, `onteardown`), lifecycle |
| `src/server/index.ts` | `registerAppTool`, `registerAppResource`, tool visibility options |
| `src/spec.types.ts` | All type definitions: `McpUiHostContext`, CSS variable keys, display modes |
| `src/styles.ts` | `applyDocumentTheme`, `applyHostStyleVariables`, `applyHostFonts` |
| `src/react/useApp.tsx` | `useApp` hook for React apps |
| `src/react/useHostStyles.ts` | `useHostStyles`, `useHostStyleVariables`, `useHostFonts` hooks |

### Framework Templates

Learn and adapt from `/tmp/mcp-ext-apps/examples/basic-server-{framework}/`:

| Template | Key Files |
|----------|-----------|
| `basic-server-vanillajs/` | `server.ts`, `src/mcp-app.ts`, `mcp-app.html` |
| `basic-server-react/` | `server.ts`, `src/mcp-app.tsx` (uses `useApp` hook) |
| `basic-server-vue/` | `server.ts`, `src/App.vue` |
| `basic-server-svelte/` | `server.ts`, `src/App.svelte` |
| `basic-server-preact/` | `server.ts`, `src/mcp-app.tsx` |
| `basic-server-solid/` | `server.ts`, `src/mcp-app.tsx` |

### Reference Examples

| Example | Relevant Pattern |
|---------|-----------------|
| `examples/map-server/` | External API integration + CSP (`connectDomains`, `resourceDomains`) |
| `examples/sheet-music-server/` | Library that loads external assets (soundfonts) |
| `examples/pdf-server/` | Binary content handling + app-only helper tools |

## Step 1: Analyze the Existing Web App

Before writing any code, examine the existing web app to plan what needs to change.

### What to Investigate

1. **Data sources** — How does the app get its data? (URL params, API calls, props, hardcoded, localStorage)
2. **External dependencies** — CDN scripts, fonts, API endpoints, iframe embeds, WebSocket connections
3. **Build system** — Current bundler (Webpack, Vite, Rollup, none), framework (React, Vue, vanilla), entry points
4. **User interactions** — Does the app have inputs/forms that should map to tool parameters?
5. **Runtime detection** — How to tell if the app is running inside an MCP host (e.g., check the current origin, a query param, or whether `window.parent !== window`)

Present findings to the user and confirm the approach.

### Data Source Mapping

In hybrid mode, the app keeps its existing data sources for standalone use and adds MCP equivalents:

| Standalone data source | MCP App equivalent |
|---|---|
| URL query parameters | `ontoolinput` / `ontoolresult` `arguments` or `structuredContent` |
| REST API calls | `app.callServerTool()` to server-side tools, or keep direct API calls with CSP `connectDomains` |
| Props / component inputs | `ontoolinput` `arguments` |
| localStorage / sessionStorage | Not available in sandboxed iframe — pass via `structuredContent` or server-side state |
| WebSocket connections | Keep with CSP `connectDomains`, or convert to polling via app-only tools |
| Hardcoded data | Move to tool `structuredContent` to make it dynamic |

## Step 2: Investigate CSP Requirements

MCP Apps HTML runs in a sandboxed iframe with no same-origin server. **Every** external origin must be declared in CSP — missing origins fail silently.

**Before writing any code**, build the app and investigate all origins it references:

1. Build the app using the existing build command
2. Search the resulting HTML, CSS, and JS for **every** origin (not just "external" origins — every network request will need CSP approval)
3. For each origin found, trace back to source:
   - If it comes from a constant → universal (same in dev and prod)
   - If it comes from an env var or conditional → note the mechanism and identify both dev and prod values
4. Check for third-party libraries that may make their own requests (analytics, error tracking, etc.)

**Document your findings** as three lists, and note for each origin whether it's universal, dev-only, or prod-only:

- **resourceDomains**: origins serving images, fonts, styles, scripts
- **connectDomains**: origins for API/fetch requests
- **frameDomains**: origins for nested iframes

If no origins are found, the app may not need custom CSP domains.

## Step 3: Set Up the MCP Server

Create a new MCP server with tool and resource registration. This wraps the existing web app for MCP hosts.

### Dependencies

```bash
npm install @modelcontextprotocol/ext-apps @modelcontextprotocol/sdk zod
npm install -D tsx vite vite-plugin-singlefile
```

Use `npm install` to add dependencies rather than manually writing version numbers. This lets npm resolve the latest compatible versions. Never specify version numbers from memory.

### Server Code

Create `server.ts`:

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { registerAppTool, registerAppResource, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import fs from "node:fs/promises";
import path from "node:path";
import { z } from "zod";

const server = new McpServer({ name: "my-app", version: "1.0.0" });

const resourceUri = "ui://my-app/mcp-app.html";

// Register the tool — inputSchema maps to the app's data sources
registerAppTool(server, "show-app", {
  description: "Displays the app with the given parameters",
  inputSchema: { query: z.string().describe("The search query") },
  _meta: { ui: { resourceUri } },
}, async (args) => {
  // Process args server-side if needed
  return {
    content: [{ type: "text", text: `Showing app for: ${args.query}` }],
    structuredContent: { query: args.query },
  };
});

// Register the HTML resource
registerAppResource(server, {
  uri: resourceUri,
  name: "My App UI",
  mimeType: RESOURCE_MIME_TYPE,
  // Add CSP domains from Step 2 if needed:
  // _meta: { ui: { connectDomains: ["api.example.com"], resourceDomains: ["cdn.example.com"] } },
}, async () => {
  const html = await fs.readFile(
    path.resolve(import.meta.dirname, "dist", "mcp-app.html"),
    "utf-8",
  );
  return { contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }] };
});

// Start the server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Package Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "build:ui": "vite build",
    "build:server": "tsc",
    "build": "npm run build:ui && npm run build:server",
    "serve": "tsx server.ts"
  }
}
```

## Step 4: Adapt the Build Pipeline

The MCP App build must produce a single HTML file using `vite-plugin-singlefile`. The standalone web app build stays unchanged.

### Vite Configuration

Create or update `vite.config.ts`. If the app already uses Vite, add `vite-plugin-singlefile` and a separate entry point for the MCP App build. If it uses another bundler, add a Vite config alongside for the MCP App build only.

```typescript
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    outDir: "dist",
    rollupOptions: {
      input: "mcp-app.html",
    },
  },
});
```

Add framework-specific Vite plugins as needed (e.g., `@vitejs/plugin-react` for React, `@vitejs/plugin-vue` for Vue).

### HTML Entry Point

Create `mcp-app.html` as a separate entry point for the MCP App build. This can point to the same app code — the runtime detection handles the rest:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MCP App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./src/main.ts"></script>
  </body>
</html>
```

### Two-Phase Build

1. Vite bundles the UI → `dist/mcp-app.html` (single file with all assets inlined)
2. Server is compiled separately (TypeScript → JavaScript)

The standalone web app continues to build and deploy as before.

## Framework Migration Patterns & Code Examples

For detailed migration tables across Vite, Next.js, and static SPAs, see [`references/framework_migration_patterns.md`](./references/framework_migration_patterns.md).
