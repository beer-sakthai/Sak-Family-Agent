# Genkit MCP & Tool Calling Constraints

## 1. Genkit MCP 4-Rule Content Coercion (`rawToolResponses: false`)
By default (`rawToolResponses: false`), `@genkit-ai/mcp` coerces MCP `content` arrays before returning them to the model:
1. Single text part containing valid JSON -> parsed into a JSON object/value.
2. Single text part containing invalid JSON -> returned as raw text string.
3. Single non-text part (e.g., image) -> returned directly.
4. Multiple or mixed parts (e.g., text + image) -> returned as the full MCP `content` array.

**Design rule:** Always test MCP tools under both `rawToolResponses: true` and `false`. Avoid returning ambiguous strings like `"123"` or `"true"` when callers expect raw strings, and avoid mixing text + image parts unless downstream callers handle array responses.

## 2. `createMcpServer` Prompt Limitations
When Genkit exposes `.prompt` files via `createMcpServer`:
- **String-only parameters:** Top-level `input.schema` properties must be strings. Numbers, booleans, arrays, and nested objects fail MCP prompt schema mapping.
- **No `system` role:** Only `{{role "user"}}` and `{{role "model"}}` are valid. Move system guidance into the opening `user` message or server instructions.
- **Single content type per message:** Never mix text and `{{media}}` inside the same role block; emit separate consecutive messages instead.

## 3. Transport & Session Resilience
- **Local `stdio`:** Scope workspace access explicitly via `roots` in `createMcpHost` / `createMcpClient`.
- **Streamable HTTP:** Handle `UnauthorizedError` during connection and message sends, refreshing tokens via `authProvider` or calling `StreamableHTTPClientTransport.finishAuth` before retrying.
- **Turn caps:** Set explicit `maxTurns` (Genkit default is `5`) and catch `GenkitError` gracefully with actionable recovery hints in tool error strings.

