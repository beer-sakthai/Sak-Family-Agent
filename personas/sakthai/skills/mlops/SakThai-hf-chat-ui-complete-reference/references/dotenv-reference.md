# Chat UI — Complete `.env` Variable Reference

> Source: `huggingface/chat-ui/.env` template (v0.20.0). All variables are read from environment at runtime. Override in `.env.local`.

## Required

| Variable | Example | Description |
|----------|---------|-------------|
| `OPENAI_BASE_URL` | `https://router.huggingface.co/v1` | OpenAI-compatible API endpoint |
| `OPENAI_API_KEY` | `hf_xxx` | Auth token for the endpoint |

## Model & Inference

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_USER_TOKEN` | `false` | When true, user's own HF token used for inference instead of server key |
| `AUTOMATIC_LOGIN` | `false` | Require authentication on all routes |
| `MODELS` | (empty) | JSON5 array of model overrides: `id`, `name`, `multimodal`, `supportsTools`, `supportsArtifacts` |
| `TASK_MODEL` | (current model) | Model for internal tasks (title summarization) |
| `LLM_SUMMARIZATION` | `true` | Generate conversation titles with LLMs |

## LLM Router

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_ROUTER_ROUTES_PATH` | (unset) | Path to routes policy JSON file |
| `LLM_ROUTER_DEFAULT_ROUTE` | `default` | Default route name |
| `LLM_ROUTER_FALLBACK_MODEL` | (unset) | Fallback model when all routes fail |
| `LLM_ROUTER_ENABLE_MULTIMODAL` | (unset) | Enable multimodal route shortcut |
| `LLM_ROUTER_MULTIMODAL_MODEL` | (unset) | Model for image inputs (requires multimodal=true) |
| `LLM_ROUTER_ENABLE_TOOLS` | (unset) | Enable tools route shortcut |
| `LLM_ROUTER_TOOLS_MODEL` | (unset) | Model for MCP tool calls (requires tools=true) |
| `PUBLIC_LLM_ROUTER_DISPLAY_NAME` | `Omni` | Virtual router model display name |
| `PUBLIC_LLM_ROUTER_LOGO_URL` | (unset) | Logo URL for router entry in model list |
| `PUBLIC_LLM_ROUTER_ALIAS_ID` | `omni` | Virtual router model alias ID |

## MCP Tools

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVERS` | (empty) | JSON array of `{name, url, optional headers}` |
| `MCP_FORWARD_HF_USER_TOKEN` | (unset) | Forward logged-in user's HF token to MCP servers |
| `EXA_API_KEY` | (unset) | API key injected into `mcp.exa.ai` URLs |
| `MCP_TOOL_TIMEOUT_MS` | `120000` | Timeout for MCP tool calls (ms) |
| `MCP_ALLOW_INSECURE_URLS` | (unset) | Allow http on localhost/private LAN (dev only) |

## MongoDB

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | (embedded) | MongoDB connection string. Unset = embedded MongoDB to `./db` |
| `MONGODB_DB_NAME` | `chat-ui` | Database name |
| `MONGODB_DIRECT_CONNECTION` | `false` | Force direct connection |
| `MONGO_STORAGE_PATH` | (unset) | Custom path for embedded MongoDB data directory |

## OpenID Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENID_CONFIG` | `{}` | OpenID configuration object |
| `OPENID_CLIENT_ID` | `""` | Client ID. Use `__CIMD__` for auto-creation on HF Spaces |
| `OPENID_CLIENT_SECRET` | (unset) | Client secret |
| `OPENID_SCOPES` | `openid profile inference-api read-mcp read-billing` | OAuth scopes |
| `OPENID_PROVIDER_URL` | `https://huggingface.co` | Provider URL |
| `OPENID_NAME_CLAIM` | `name` | Claim for user display name |
| `ALLOWED_USER_EMAILS` | `[]` | Explicit email allow list |
| `ALLOWED_USER_DOMAINS` | `[]` | Email domain allow list |
| `AUTOMATIC_LOGIN` | `false` | Require login on all routes |
| `COOKIE_NAME` | `hf-chat` | Session cookie name |
| `COOKIE_SAMESITE` | (unset) | `lax`, `strict`, `none`, or empty |
| `COOKIE_SECURE` | (unset) | HTTPS-only cookies |
| `COUPLE_SESSION_WITH_COOKIE_NAME` | (unset) | Tie session to parent domain auth cookie |
| `ALTERNATIVE_REDIRECT_URLS` | `[]` | Valid alternative OAuth redirect URLs |

## Theming & UI

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLIC_APP_NAME` | `ChatUI` | App title |
| `PUBLIC_APP_ASSETS` | `chatui` | Logo set: `chatui` or `huggingchat` |
| `PUBLIC_APP_DESCRIPTION` | `"Making the community's best AI chat models available to everyone."` | App description |
| `PUBLIC_APP_DATA_SHARING` | (unset) | Enable data sharing opt-in toggle |
| `PUBLIC_ORIGIN` | (unset) | Public origin URL |
| `PUBLIC_CAVEAT` | (unset) | Text below chat input |
| `PUBLIC_SHARE_PREFIX` | (unset) | Share URL prefix |
| `PUBLIC_FEATURE_ANNOUNCEMENTS` | (unset) | JSON5 array of `{title, description, link?, cta?, maxDate?}` |
| `PUBLIC_GOOGLE_ANALYTICS_ID` | (unset) | Google Analytics ID |
| `PUBLIC_PLAUSIBLE_SCRIPT_URL` | (unset) | Plausible Analytics URL |
| `PUBLIC_APPLE_APP_ID` | (unset) | Apple App ID for PWA |
| `ALLOW_IFRAME` | `true` | Allow embedding in iframe |

## Voice Transcription

| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSCRIPTION_MODEL` | (unset) | Whisper model ID for voice-to-text (enables mic button) |
| `TRANSCRIPTION_BASE_URL` | `https://router.huggingface.co/hf-inference/models` | Custom transcription API base URL |

## Rate Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `USAGE_LIMITS` | `{}` | JSON object with `conversations`, `messages`, `assistants`, `messageLength`, `messagesPerMinute`, `tools` |

## Metrics & Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `METRICS_ENABLED` | `false` | Enable Prometheus metrics endpoint |
| `METRICS_PORT` | `5565` | Metrics server port |
| `LOG_LEVEL` | `info` | Logging level |
| `GENERATION_REAP_INTERVAL_MS` | `60000` | Sweep interval for dead generations (ms) |
| `GENERATION_REAP_AFTER_MS` | `90000` | No-heartbeat timeout before reaping (ms) |
| `GENERATION_HEARTBEAT_MS` | `10000` | Generation heartbeat interval (ms) |

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DATA_EXPORT` | `true` | Enable conversation data export |
| `ENABLE_CONFIG_MANAGER` | `true` | Enable config manager UI |

## Admin & Security

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_CLI_LOGIN` | `true` | Enable CLI login |
| `ADMIN_API_SECRET` | (unset) | Secret for admin API calls |
| `ADMIN_TOKEN` | (unset) | Admin token (auto-generated from terminal) |
| `HF_ORG_ADMIN` | (unset) | HF org for admin flags |
| `HF_ORG_EARLY_ACCESS` | (unset) | HF org for early access flags |
| `WEBHOOK_URL_REPORT_ASSISTANT` | (unset) | Slack webhook for reports |
| `TRUSTED_EMAIL_HEADER` | (unset) | Header for user email (expert use only) |

## Parquet Export

| Variable | Default | Description |
|----------|---------|-------------|
| `PARQUET_EXPORT_DATASET` | (unset) | HF dataset name for parquet export |
| `PARQUET_EXPORT_HF_TOKEN` | (unset) | Token for parquet export |

## Build/Deploy

| Variable | Default | Description |
|----------|---------|-------------|
| `BODY_SIZE_LIMIT` | `15728640` | SvelteKit body size limit (bytes) |
| `APP_BASE` | `""` | App base path |
| `PUBLIC_COMMIT_SHA` | (unset) | Git commit SHA for version display |

## Legacy/Deprecated

| Variable | Replaced By | Notes |
|----------|-------------|-------|
| `ALLOW_INSECURE_COOKIES` | `COOKIE_SECURE` + `COOKIE_SAMESITE` | Legacy |
| `PARQUET_EXPORT_SECRET` | `ADMIN_API_SECRET` | Deprecated |
| `RATE_LIMIT` | `USAGE_LIMITS.messagesPerMinute` | Deprecated |
| `EXPOSE_API` | — | API always exposed now |
| `HF_TOKEN` | `OPENAI_API_KEY` | Legacy alias for provider auth |
