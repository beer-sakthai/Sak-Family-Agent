# HF Learnings — Inference Providers Responses API & Remote MCP Deep Dive

## 2026-07-25: hf-inference-providers-responses-api-deep-dive — Hugging Face Inference Providers Responses API (beta) Complete Architecture (Topic #381)

### Summary
Deep dive into the Hugging Face **Inference Providers Responses API (beta)** — a unified OpenAI-compatible interface exposed at `https://router.huggingface.co/v1` that wraps all Inference Providers behind a single endpoint. Unlike the legacy `InferenceClient` or direct provider APIs, the Responses API provides a `client.responses.create()` pattern with native support for tool orchestration, event-driven streaming, structured outputs (Pydantic `.parse()`), reasoning effort controls, **Remote MCP tool execution**, and multi-provider routing strategies (`:fastest`, `:cheapest`, `:preferred`, explicit provider pinning). Free tier includes $0.10/mo credits ($2/mo for PRO) covering moderate usage.

### Key Findings

#### 1. Architecture
- **Endpoint**: `https://router.huggingface.co/v1` — OpenAI SDK compatible, uses existing `openai` Python/TS packages
- **Auth**: `HF_TOKEN` with "Make calls to Inference Providers" permission
- **Model selection**: `<model_id>:<provider>` for explicit provider, or `<model_id>:<policy>` for automatic routing
- **Policies**: `:fastest` (lowest latency, default), `:cheapest` (lowest cost), `:preferred` (user's provider ordering in HF settings)

#### 2. Provider Routing Strategies
- **`:fastest`** — selects the provider with lowest `first_token_latency_ms` for the requested model; re-evaluated per request based on live provider metrics
- **`:cheapest`** — selects the provider with lowest combined `pricing.input + pricing.output` per token; ideal for batch/background workloads
- **`:preferred`** — follows the user's ranked provider list in HF account settings; falls back if first-choice provider is unavailable
- **Explicit pinning** — e.g. `openai/gpt-oss-120b:groq` locks to Groq; fails if that provider doesn't serve the model
- **Fallback behavior**: If a provider returns an error during streaming, the router does NOT automatically switch mid-stream; retry at the application level with a different provider

#### 3. Remote MCP Execution (Game-Changer)
The Responses API introduces **server-side MCP tool execution** — the first HF inference feature to natively support the Model Context Protocol:
- **Tool schema**: `{"type": "mcp", "server_label": "...", "server_url": "https://...", "allowed_tools": [...], "require_approval": "never"|"always"|"on_first_use"}`
- **How it works**: The model generates tool calls → HF router forwards them to the MCP server → results stream back as events
- **No MCP client needed**: The HF router acts as the MCP client, you just provide the server URL
- **Security**: `require_approval` controls whether tool execution needs user confirmation
- **Limitations**: MCP servers must be publicly accessible HTTPS endpoints; no local/Unix socket support

#### 4. Event-Driven Streaming Events
When `stream=True`, the API emits semantic SSE events:
| Event | Description |
|-------|-------------|
| `response.created` | Response session initialized |
| `response.in_progress` | Model is generating |
| `output_text.delta` | Streaming text chunk |
| `output_text.done` | Text segment complete |
| `tool_call.delta` | Partial tool call args |
| `tool_call.done` | Full tool call ready |
| `response.completed` | Entire response finished |
| `response.failed` | Error occurred |
| `response.incomplete` | Tokens exhausted / max_output reached |

#### 5. Structured Outputs with Pydantic
```python
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

response = client.responses.parse(
    model="openai/gpt-oss-120b:groq",
    input=[{"role": "user", "content": "Alice and Bob are going to a science fair on Friday."}],
    text_format=CalendarEvent,
)
print(response.output_parsed)  # CalendarEvent(name="Science Fair", ...)
```
- Uses `.parse()` method on the client (not `.create()`)
- Returns typed Pydantic model directly via `response.output_parsed`
- Falls back gracefully if model can't comply — returns raw text in `response.output_text`

#### 6. Multi-Provider Model Discovery
New Hub API filters enable provider-aware model discovery:
- `GET /api/models?inference_provider=groq` — models served by Groq
- `GET /api/models?inference_provider=all` — any model served by at least one provider
- `GET /api/models?inference_provider=nscale,novita&pipeline_tag=image-text-to-text` — multi-provider, multi-tag
- `GET /router.huggingface.co/v1/models` — OpenAI-compatible model list with provider metadata (pricing, latency, throughput, tool/structured-output support)
- `model_info("model-id", expand="inference")` — returns "warm" if served by a provider

#### 7. Tool Calling via Chat Completions (Classic)
The existing `/v1/chat/completions` endpoint also supports tool calling:
- `tool_choice="auto"` — model decides when to call functions
- `tool_choice="required"` — forces at least one function call
- `tool_choice="none"` — disables tool calling
- `tool_choice={"type": "function", "function": {"name": "my_function"}}` — forces a specific function
- Functions defined as JSON Schema in `tools` array with `type: "function"`

#### 8. Billing & Free Tier
| Account | Monthly Credits | Pay-as-you-go |
|---------|----------------|---------------|
| Free | $0.10 | Yes (purchase credits) |
| PRO | $2.00 | Yes |
| Team/Enterprise | $2.00/seat | Yes |
- Credits auto-apply when routed through HF (not when using custom provider keys)
- No markup on provider pricing — you pay what the provider charges
- 200+ models available across 17+ providers

### Zero-Cost Patterns
1. **Free credits cover**: Inference Widgets, Playground, Data Studio AI, moderate API calls via the router
2. **`:cheapest` routing** automatically picks the lowest-cost provider for each model
3. **Model selection**: Many strong open models are available free (via HF Inference provider or cheap providers)
4. **Remote MCP**: No infrastructure cost for tool hosting — use free MCP servers or HF Spaces as MCP hosts
5. **Structured outputs**: Use `.parse()` to reduce retry costs from malformed JSON

### Skill Created
`hf-inference-providers-responses-api-deep-dive/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete architecture, routing strategies, MCP integration, event reference, billing details, and zero-cost patterns.

### Sources
- https://huggingface.co/docs/inference-providers/en/guides/responses-api — Responses API (beta) guide
- https://huggingface.co/docs/inference-providers/en/guides/function-calling — Function Calling guide
- https://huggingface.co/docs/inference-providers/en/pricing — Pricing and Billing
- https://huggingface.co/docs/inference-providers/en/hub-integration — Hub Integration
- https://huggingface.co/docs/inference-providers/en/hub-api — Hub API reference
- https://router.huggingface.co/v1/models — OpenAI-compatible model list with provider metadata
- https://huggingface.co/docs/inference-providers/en/index — Inference Providers docs (main)
