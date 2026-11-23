# Tool Calling vs. RAG & Tool Consolidation Boundary

## Decision Matrix
- **Use direct MCP Tool Calling (`defineTool` / `createMcpHost`):** Live, fast-changing state (weather, stock prices, ticket status), deterministic math/lookups, or side-effecting mutations (guarded by `defineInterrupt()`).
- **Use RAG (`ai.retrieve` + `ai.rerank`):** Large, semi-static corpora (documentation, menus, policies) where relevant passages are ambiguous and citation grounding is required.
- **Use Two-Stage Tool-RAG:** When active tools across MCP servers exceed ~15–20 tools or exhibit high semantic overlap.

## Consolidation & Ablation Protocol
1. Index all `mcpHost.getActiveTools(ai)` names and `.describe()` strings into a vector index (`gemini-embedding-001`).
2. Run `ai.rerank` (e.g., `vertexai/semantic-ranker-512` or a custom cosine/cross-encoder `defineReranker`) across tool descriptions to identify near-duplicate tools.
3. Merge overlapping tools into unified parameter-driven tools (or disable redundant servers via `disabled: true` in `McpServerConfig`) and verify win-rate improvement on the `validation` dataset.

