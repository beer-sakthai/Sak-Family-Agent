# HF Learnings — Model Routing for Agentic Systems Deep Dive

## 2026-07-25: model-routing-agent-systems-deep-dive — Model Routing Strategies for Agentic Systems (Topic #355)

### Summary

Deep dive into model routing for agentic systems, based on IBM Research's production routing work (published July 15, 2026) and Ai2/Shippy's maritime agent architecture. Covers why naive classification-based routing fails, the three hidden dimensions of routing (caching economics, invisible complexity, infrastructure latency), and how optimization-based routing explores cost-accuracy frontiers. Includes agent architecture patterns (soul/skills/config), deterministic CLI abstractions, and agent-specific evaluation frameworks.

Key insight: Routing isn't about choosing models — it's about optimizing systems. Models are one variable among caching behavior, infrastructure state, compliance constraints, and workload patterns.

---

### 1. The Three Hidden Dimensions of Model Routing

#### 1.1 Cost Is More Than Model Pricing

**Naive assumption:** Send simple requests to cheaper models, reserve expensive ones for harder tasks. A classifier or heuristic makes the call, costs go down, performance stays up.

**Reality (IBM Research, AppWorld Test Challenge, 417 tasks, CodeAct agent):**

| Metric | Claude Sonnet 4.6 | GPT-4.1 |
|--------|-------------------|---------|
| Total cost (417 tasks) | **$79** ($0.19/task) | **$155** ($0.37/task) |
| Sticker input price | Higher | Lower |
| Sticker output price | Higher | Lower |
| Reasoning steps | ~3x more | Baseline |
| Cache hit rate | High (lower cache-read pricing) | Lower benefit |

**Why:** Sonnet costs less despite higher sticker pricing. The explanation is **caching** — agent workloads reuse large chunks of context across steps. When cache hit rates are high, effective input costs drop dramatically. Sonnet's lower cache-read pricing means it benefits disproportionately from this pattern, enough to overcome both its higher base pricing and its longer trajectories.

**Lesson:** Actual cost depends on the interaction between the model, the workload, and the serving infrastructure. A router that only looks at pricing sheets is optimizing against the wrong numbers.

**Practical pattern for HF Inference Providers:**
- HF Provider caching behavior varies by provider (some offer prompt caching, some don't)
- Effective cost = (cache-miss tokens × miss price) + (cache-hit tokens × hit price) + output tokens
- Agent workloads with repeated system prompts benefit most from providers with aggressive caching
- Always benchmark real workloads rather than relying on sticker prices

#### 1.2 Complexity Is More Than Task Difficulty

**Naive assumption:** Estimate how hard a task is and route to stronger models for harder tasks.

**Why it breaks:**

1. **Difficulty is invisible at routing time.** A request like "summarize this contract" looks simple, but might trigger retrieval, compliance checks, tool use, and multiple rounds of refinement. A highly technical prompt might be handled efficiently by a smaller specialized model. You often don't know how hard a task actually is until execution is underway.

2. **Difficulty is one signal among many.** Production routers need to balance:
   - **Cost** — per-task and aggregate budget
   - **Quality** — accuracy, completeness, correctness
   - **Latency** — end-to-end response time
   - **Model specialization** — some models excel at specific domains
   - **Reliability** — uptime, error rates, fallback chains
   - **Compliance** — data residency, privacy, approved model lists
   - **Governance** — regulatory constraints, audit trails

**Lesson:** Routers aren't solving one problem. They're constantly juggling cost, quality, latency, compliance, and reliability all at once.

#### 1.3 Latency Is More Than Model Speed

**Naive assumption:** Bigger models are slower, smaller ones are faster.

**Reality:** What the user experiences depends on:
- **Routing overhead** — the router itself adds latency
- **Infrastructure factors** — which hardware, cache warmth, endpoint load
- **Routing granularity** — routing once per task (low overhead) vs. routing at every step (flexible but expensive)
- **Serving conditions** — a theoretically faster model can produce a slower experience if the serving conditions aren't right

**IBM's results:** Their optimization-based router adds only ~6ms and ~2kB of memory per task — lightweight enough to avoid becoming the bottleneck.

**Lesson:** A router that ignores the serving system is optimizing against the wrong reality.

---

### 2. Optimization-Based Routing (IBM Research Approach)

The key shift: stop treating routing as a **classification problem** ("which model is best for this task?") and start treating it as an **optimization problem** ("what's the best operating point for the entire system?").

#### How It Works

- **Algorithm:** Simultaneously optimizes across cost, quality, and latency
- **Output:** A **cost-accuracy frontier** — a range of operating points to choose from
- **User control:** Tuning parameters let you prioritize cost, latency, or accuracy
- **Performance:** ~6ms and ~2kB of memory per task

#### Results on AppWorld Test Challenge (CodeAct Agent)

| Configuration | Accuracy | Cost | Latency | vs. Opus (baseline) |
|--------------|----------|------|---------|---------------------|
| Opus alone (baseline) | 88% | $118 | 91s | — |
| Config 1 (latency-optimized) | **84%** | **$93** | **83s** | -21% cost, -9% latency, -4% accuracy |
| Config 2 (cost-optimized) | Lower | Even lower | — | Explores further tradeoffs |
| Difficulty-based router (teal) | Similar accuracy | Higher cost | — | Doesn't explore full tradeoff space |

**Key takeaway:** A standard difficulty-based router lands in a similar accuracy range but at higher cost — it doesn't explore the full tradeoff space the way an optimization-based approach can.

#### Implementation Considerations

```
[Agent Request] → [Optimization Router] → [Model Selection]
                        ↑
              Objective: minimize cost + latency
              Constraints: minimum accuracy, compliance, latency SLA
              Variables: model options, provider, cache state, endpoint load
```

- Define an objective function: `minimize(cost × w_cost + latency × w_latency)`
- Subject to: `accuracy ≥ min_acceptable`, `latency ≤ max_acceptable`
- Each model option has a vector: `(cost_per_task, expected_latency, expected_accuracy, specialized_domains, compliance_ok)`
- Router evaluates the Pareto frontier and picks the operating point matching current priorities

---

### 3. Agent Architecture Patterns (from Shippy/Ai2)

Shippy is a maritime AI agent built for high-stakes decisions. Its architecture reveals patterns applicable to any agent system that wants to implement routing.

#### Agent Anatomy: Soul, Skills, Config

| Component | What It Is | Why It Matters for Routing |
|-----------|-----------|---------------------------|
| **Soul** | System prompt defining persona and behavioral boundaries | Frame what the agent will/won't do — determines routing guardrails |
| **Skills** | Plain markdown files with structured frontmatter (same spec as Claude Code/Codex) | Each skill encodes the full workflow for a task type — enables routing by skill domain |
| **Config** | Agent harness (OpenClaw), LLM selection, runtime settings, secrets injection | Swapping the model is a config change, not a rebuild — enables dynamic routing |

**Key insight:** Skills follow the **agent-skills spec** used by coding tools like Claude Code and Codex — plain markdown files with structured frontmatter. This keeps each skill comprehensible, versioned, and easy to revise.

#### Deterministic Tools for Nondeterministic Agents

Shippy communicates with its backend through a **purpose-built CLI** rather than issuing raw API calls. The layering is:

```
Typed API → Deterministic CLI → Agent Skills (reference CLI commands)
```

- The CLI collapses API complexity into predictable commands with typed flags
- Output is written to local JSON files (not piped through stdout — avoids pipe buffer limits)
- Self-documenting with `--help` text and detailed error messages
- Each layer narrows what the next layer can get wrong

**Routing relevance:** When implementing routing, the tool layer abstraction ensures that routing decisions are made at the skill level, not confused with API implementation details.

#### Sandboxed Hosting (Mothership)

- Each user gets an ephemeral, isolated Kubernetes deployment
- Agent runtime, skills, and CLI are packaged together
- User JWT injected at provision time for data scoping
- Network sandbox restricted to only needed services

#### Agent-Specific Evaluation (Harbor Framework)

- **Subject-matter experts** write scenarios and rubrics with weighted criteria
- **LLM judge** scores each criterion (0-1) with written reasoning
- Weighted aggregate checked against a pass threshold
- Tests run against **live data** in real sandbox sessions
- Suite reruns whenever skills, model, or data change

**Routing relevance:** An agent eval framework like this is essential for measuring whether routing improves or degrades system performance.

---

### 4. Practical Routing Patterns

#### Pattern A: Skill-Based Routing

Route requests to models based on the skill domain:

```
"Show me fishing activity in Panama's EEZ"
  → Skill: SkylightQuery
  → Route to: model_optimized_for_geospatial_queries (smaller/cheaper)
  
"Analyze this vessel behavior pattern"
  → Skill: VesselTrackAnalysis
  → Route to: frontier_model (stronger reasoning)
```

#### Pattern B: Step-Level Dynamic Routing

Route at every agent step rather than once per task. More flexible but:
- Higher overhead (each decision point adds latency)
- Needs lightweight router (~6ms per decision as IBM achieved)
- Can adapt mid-execution if task difficulty changes

#### Pattern C: Cost-Accuracy Frontier Selection

Maintain a pre-computed cost-accuracy frontier:

```
Operating Point A: Max accuracy (frontier model, highest cost)
Operating Point B: Balanced (medium model, medium cost)
Operating Point C: Min cost (small model, lower accuracy)
```

Select operating point dynamically based on:
- Current budget remaining
- Task criticality (inferred from request context)
- Latency SLA requirements
- Compliance constraints

#### Pattern D: Caching-Aware Routing

Since caching dominates real cost:
- Track cache hit rates per model/provider
- Route repetitive tasks to providers with aggressive caching
- Route novel tasks to models with best raw quality (cache matters less)
- Monitor effective cost (post-cache), not sticker price

---

### 5. Key Takeaways for Hugging Face Inference Providers

1. **Provider pricing is just the starting point.** HF Inference Providers offer different models at different price points, but effective cost depends on workload patterns, caching behavior, and routing overhead.

2. **Multi-provider routing benefits from optimization.** HF supports multiple providers (Together, Replicate, SambaNova, etc.) — each has different latency profiles, cache behavior, and pricing. An optimization-based router can select the best provider+model combination for each request.

3. **Agent workloads amplify caching advantages.** Repeated system prompts, tool schemas, and conversation history are ideal for prompt caching. HF Inference Providers that support prompt caching will have significantly lower effective costs for agent workloads.

4. **Build eval before you build routing.** As Shippy demonstrates, agent-specific evaluation (scenarios + rubrics + LLM judge) is essential for measuring whether routing changes improve or degrade system performance.

---

### References

- IBM Research. "Model Routing Is Simple. Until It Isn't." Hugging Face Blog, July 15, 2026. https://huggingface.co/blog/ibm-research/model-routing-is-simple-until-it-isnt
- Ai2/Shippy. "What building Shippy taught us about building agents." Hugging Face Blog, July 15, 2026. https://huggingface.co/blog/allenai/shippy-tech-blog
- Hugging Face Inference Providers Documentation. https://huggingface.co/docs/api-inference/index
