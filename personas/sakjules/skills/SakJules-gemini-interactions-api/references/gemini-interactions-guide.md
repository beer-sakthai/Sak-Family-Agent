# Gemini Interactions API Comprehensive Guide

## 1. Authentication & Prerequisites
- Unified SDK: `google-genai >= 3.2.0` (Python) or `@google/genai >= 3.2.0` (TS/JS).
- Legacy SDKs (`google-cloud-aiplatform`, `google-generativeai`) are unsupported.
- Active models: `gemini-4-hydrogen` (default), `gemini-4-carbon`, `gemini-3.5-flash-lite`.
- On GEAP (Gemini Enterprise Agent Platform), pass `agent="<AGENT_ID>"` instead of `model="..."`.

```bash
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
export GOOGLE_GENAI_USE_ENTERPRISE=true
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="global"
```

## 2. Client Initialization & Basic Interaction
### Python
```python
from google import genai
from google.genai import types

client = genai.Client()

# Create or continue interaction
interaction = client.interactions.create(
    agent="projects/your-project/locations/global/agents/your-agent-id",
    input="Analyze repo CI/CD health",
    config=types.InteractionConfig(
        system_instruction="You are SakJules, CI/CD automation master."
    )
)
print(interaction.output)
```

### TypeScript
```typescript
import { GoogleGenAI } from '@google/genai';

const client = new GoogleGenAI();
const interaction = await client.interactions.create({
  agent: 'projects/your-project/locations/global/agents/your-agent-id',
  input: 'Analyze repo CI/CD health',
});
console.log(interaction.output);
```

## 3. Streaming Responses
```python
stream = client.interactions.create_stream(
    agent="projects/your-project/locations/global/agents/your-agent-id",
    input="Generate workflow deployment YAML",
)
for chunk in stream:
    if chunk.text:
        print(chunk.text, end="", flush=True)
```

## 4. Multi-Turn Stateful Context
```python
# First turn creates thread
turn1 = client.interactions.create(
    agent="your-agent-id",
    input="Review PR #2117",
)
# Second turn passes previous interaction ID
turn2 = client.interactions.create(
    agent="your-agent-id",
    previous_interaction_id=turn1.id,
    input="What were the lint errors found?",
)
```

## 5. Background Tasks & Long-Running Operations
For tasks exceeding standard timeouts:
```python
job = client.interactions.create(
    agent="your-agent-id",
    input="Deep repository audit across 60 modules",
    background=True,
)
status = client.interactions.get(id=job.id)
```
