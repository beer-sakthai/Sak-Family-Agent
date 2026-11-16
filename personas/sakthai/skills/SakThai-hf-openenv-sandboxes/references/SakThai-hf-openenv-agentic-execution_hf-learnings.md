# HF Learnings Log — Hugging Face OpenEnv: Agentic Execution Environments

## 2026-07-25: hf-openenv-agentic-execution — Hugging Face OpenEnv v0.4.1: Unified Framework for Agentic RL Environments (Topic #385)

### Summary
Comprehensive deep-dive into **OpenEnv** (`pip install openenv`, v0.4.1, experimental) — Hugging Face's unified framework for building, deploying, and interacting with isolated execution environments for agentic reinforcement learning. OpenEnv provides a Gymnasium-style API (`step()`, `reset()`, `state()`) over HTTP/WebSocket with container isolation, MCP tool integration, a composable Rubric reward system, and seamless RL training integration (TRL/Unsloth/Inspect AI). Governed by a technical committee including Meta-PyTorch, Nvidia, Hugging Face, and others.

### Key Findings

| Area | Finding |
|------|---------|
| **What it is** | Unified framework for isolated agentic RL environments. Gymnasium-style API + container isolation + MCP tools. Experimental (v0.4.1). |
| **Architecture** | Client-server model over HTTP/WebSocket. Agents send structured Actions, receive Observations with reward/done/metadata. |
| **Connection methods** | HTTP URL (remote/HF Spaces), Docker (local), cloud sandbox (Daytona/ACA), auto-discovery (installed packages). |
| **MCP integration** | Two action types: `ListToolsAction` (discovery) and `CallToolAction` (invocation). Dual API: Gym control plane (`/ws`) + MCP tools (`/mcp`). |
| **Rubrics** | Composable reward computation: `WeightedSum`, `Gate`, `Sequential`, `TrajectoryRubric`, LLM judge. Rewards computed inside env, not externally. |
| **Cloud providers** | LocalDocker, DockerSwarm, UV, Daytona, ACA (Azure Container Apps), Kubernetes (planned). Neutral ContainerProvider contract. |
| **RL training** | Works with TRL (GRPOTrainer), Unsloth, torchforge, and custom loops via `environment_factory` pattern. |
| **MCP maturity** | Still in flight — RFC 003 proposes MCP as standard for all agent actions. Currently only echo_env and finqa_env use MCPEnvironment base. |
| **Governance** | Technical committee: Meta-PyTorch, Reflection, Unsloth, Modal, Prime Intellect, Nvidia, Mercor, Fleet AI, Microsoft, HF, RadixArk. |
| **Zero-cost** | Local dev with `UVProvider` (no Docker), sync client for scripts, HF Space hosting (free tier). Docker required for containerized deployment. |

### Architecture Deep-Dive

```
+-----------------+  HTTP/WebSocket  +-----------------+
|                 | —————/step—————> |                 |
|   Your Agent    | <——observation—  |   Environment   |
|   (Client)      | —————/reset————> |   (Server)      |
|                 | <———state——————  |                 |
+-----------------+                  +-----------------+
```

- **Environment**: Isolated execution context (server). Subclasses `Environment[ActT, ObsT, StateT]`.
- **Action**: Structured command. Custom Pydantic model per env. Subclasses `Action` base.
- **Observation**: Response with state. Subclasses `Observation` base (carries `reward` + `done` fields).
- **StepResult**: Bundles observation + reward + done + metadata.
- **Client**: Async (default) or sync (`.sync()`) connector.

### The Dual API Boundary

| Surface | Protocol | Endpoint | Used By |
|---------|----------|----------|---------|
| **Control plane** | Gym-style WebSocket | `/ws` | Trainer (reset/step/state timing) |
| **Agent tools** | MCP JSON-RPC | `/mcp` | Model (tool calls, discovery) |

In simulation mode, MCP tool calls flow **through** `step()` — the trainer stays in control of timing/rewards/termination while the model sees standard MCP tool schemas.

### Environment Anatomy

```
my_env/
├── openenv.yaml          # Manifest (name, version, client/action/observation classes, default_image, spec_version)
├── my_env/
│   ├── __init__.py
│   ├── client.py         # Client classes
│   ├── server.py         # Environment class + FastAPI app
│   └── models.py         # Pydantic Action, Observation, State models
├── Dockerfile            # Container definition
├── pyproject.toml        # Package metadata
└── README.md
```

### Manifest (openenv.yaml) Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Environment package name |
| `version` | Yes | Semver |
| `description` | No | Human-readable description |
| `client.class_name` | Yes | Client class for connecting |
| `client.module` | Yes | Python module path |
| `action.class_name` | Yes | Action class |
| `action.module` | Yes | Python module path |
| `observation.class_name` | Yes | Observation class |
| `observation.module` | Yes | Python module path |
| `default_image` | No | Default Docker image tag |
| `spec_version` | Yes | Manifest spec version (currently 1) |

### MCP Tools — Two Action Types

**ListToolsAction** (discovery):
```python
obs = env.step(ListToolsAction())
# obs.tools: [Tool(name, description, input_schema), ...]
```

**CallToolAction** (invocation):
```python
obs = env.step(CallToolAction(tool_name="echo", arguments={"msg": "Hi"}))
# obs.result — CallToolResult (may have .data, .structured_content, .content)
# obs.error — None if success
# obs.reward — env's reward for this turn
# obs.done — episode terminated
```

### Comparison: Traditional Gym vs OpenEnv

| Aspect | OpenAI Gym | OpenEnv |
|--------|-----------|---------|
| **Process** | Same-process | Docker container (isolated) |
| **API** | Python function call | HTTP/WebSocket |
| **Language** | Python only | Any language |
| **Types** | Numpy arrays / magic indices | Pydantic models (IDE support) |
| **Deployment** | "Works on my machine" | Same container everywhere |
| **Scaling** | Hard to distribute | Kubernetes, Docker Swarm, cloud sandboxes |
| **Tools** | N/A | MCP protocol (standard agent interface) |
| **Rewards** | Tuple return | Composable Rubrics inside env |
| **Debugging** | Cryptic numpy errors | Clear type errors |

### RL Training Integration

**Custom rollout loop** (framework-agnostic):
```python
obs = env.reset()
for turn in range(max_turns):
    tool_call = model.decide(obs)
    obs = env.step(CallToolAction(tool_name=tool_call.name, arguments=tool_call.arguments))
    total_reward += obs.reward or 0.0
    if obs.done: break
```

**TRL GRPOTrainer environment_factory**:
```python
class MyEnvFactory:
    def __init__(self, env):
        self.env = env
        self.reward = 0.0

    def my_tool(self, arg: str) -> str:
        step_result = self.env.step(CallToolAction(tool_name="my_tool", arguments={"arg": arg}))
        self.reward = step_result.reward or 0.0
        return step_result.observation.result.data
```

### OpenEnv Ecosystem (as of v0.4.1)

**Pre-built environments** available or in development:
- `echo_env` — Minimal echo (has MCPEnvironment base)
- `finqa_env` — Financial QA (has MCPEnvironment base)
- `calendar_env` — Calendar with local MCP wrapper
- `textarena_env` — Wordle / text games
- `openspiel_env` — OpenSpiel game environments
- `chess_env` — Chess
- `browsergym_env` — Web browser automation
- `coding_env` — Code execution

**Note**: Only echo_env and finqa_env currently inherit from `MCPEnvironment`. Most envs use custom action types passed through `env.step(CustomAction(...))`.

### Frontend/Web UI

OpenEnv includes a built-in web interface for live environment monitoring. The web UI is served alongside the FastAPI server and shows:
- Current environment state
- Step history
- Reward progression
- Tool call logs

### Known Limitations (v0.4.1)

1. **MCP not universal** — RFC 003 still In Review; most envs use custom actions
2. **Experimental** — APIs may change; main branch requires source install
3. **Docker dependency** — Container isolation requires Docker unless using `UVProvider`
4. **HF Spaces integration** — MCP-based envs can be deployed to Spaces but documentation is still evolving
5. **No HF Hub integration yet** — No built-in `push_to_hub` for environments (unlike models/datasets); manual Docker registry upload required

### Skill Created
`hf-openenv-agentic-execution/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with full architecture, API reference, MCP integration details, Rubric system, deployment patterns, zero-cost analysis.

### Sources
- https://huggingface.co/docs/openenv/en/index — Official docs (v0.4.1)
- https://huggingface.co/docs/openenv/en/getting-started — Getting Started guide
- https://huggingface.co/docs/openenv/en/guides/concepts — Core concepts
- https://huggingface.co/docs/openenv/en/guides/first-environment — Your First Environment
- https://huggingface.co/docs/openenv/en/tutorials/openenv-tutorial — Hello World tutorial
- https://huggingface.co/docs/openenv/en/tutorials/mcp-environment — MCP Environments tutorial
- https://huggingface.co/docs/openenv/en/tutorials/rl-training-2048 — RL Training with TRL tutorial
- https://github.com/huggingface/OpenEnv — GitHub repository (RFCs, issues, releases)

### Tags
`openenv` `agentic` `rl` `environments` `mcp` `training` `gymnasium` `containers` `fastapi` `trl` `unsloth` `sandbox`
