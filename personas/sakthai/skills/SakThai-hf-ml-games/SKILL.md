---
name: SakThai-hf-ml-games
author: SakThai
license: MIT
description: "Integrate AI into games — NPCs, tools, Unity, Cubzh."
version: 1.0.0
tags: [GameDev, AI, NPC, Unity, HuggingFace]
---
# Machine Learning for Games

Based on the [HF ML for Games Course](https://huggingface.co/learn/ml-games-course). Covers building smart NPCs with LLMs, using AI tools in game dev pipelines, integrating models with Unity Sentis, and creating AI-powered game demos.

## When to Use

- User wants to "add AI to a game"
- User asks about NPC behavior with LLMs
- User wants to generate game assets (textures, voice) with AI
- User needs to integrate HF models with Unity or Cubzh

## Prerequisites

- For Unity: Unity Editor (2022.3+) + Unity Sentis package (1.0+)
- For Cubzh: Cubzh account (free) at [cubzh.com](https://cubzh.com)
- HF account for model access
- Local or cloud API key for LLM inference

## Quick Reference

| Concept | Tool | Description |
|---------|------|-------------|
| Smart NPCs | LLMs + APIs | Conversational NPCs powered by chat models |
| Unity Sentis | Unity | Run ONNX models directly in Unity runtime |
| Cubzh AI | Lua + API | Call HF Inference API from Cubzh Lua scripts |
| AI Art | HF Diffusers | Generate textures, sprites, concept art |
| Voice | HF TTS | Text-to-speech for game dialogue |
| Local Inference | llama.cpp, Ollama | Run models without cloud APIs |
| Behavior Trees | Custom | Combine LLM decisions with traditional BT |
| Memory | Vector DB | NPC long-term memory (conversation history) |

## NPC AI Patterns

### Pattern 1: Simple Q&A NPC (HF Inference API)
```python
import requests

def npc_response(player_input, npc_name="Merchant Marcus"):
    """Simple NPC that answers using HF Inference API."""
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {"Authorization": "Bearer hf_***"}
    
    prompt = f"""You are {npc_name}, a merchant in a fantasy game.
Keep responses under 2 sentences. Be helpful but greedy.

Player: {player_input}
{npc_name}:"""
    
    response = requests.post(
        API_URL,
        headers=headers,
        json={
            "inputs": prompt,
            "parameters": {"max_new_tokens": 100, "temperature": 0.7}
        }
    )
    return response.json()[0]["generated_text"].split(f"{npc_name}:")[-1].strip()
```

### Pattern 2: NPC with Actions and Function Calling
```python
from openai import OpenAI

class GameNPC:
    def __init__(self, name, personality, inventory=None):
        self.name = name
        self.personality = personality
        self.inventory = inventory or {}
        self.memory = []
        
    def process_input(self, player_input):
        """Process player input and return response + actions."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "give_item",
                    "description": "Give an item to the player",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string"},
                            "quantity": {"type": "integer"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "start_quest",
                    "description": "Give the player a new quest",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "quest_name": {"type": "string"},
                            "objective": {"type": "string"}
                        }
                    }
                }
            }
        ]
        
        messages = [
            {"role": "system", "content": f"You are {self.name}. {self.personality}"},
            *self.memory[-5:],  # Last 5 interactions
            {"role": "user", "content": player_input}
        ]
        
        client = OpenAI(base_url="https://router.huggingface.co/v1", api_key="hf_***")
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        self.memory.append({"role": "user", "content": player_input})
        self.memory.append({"role": "assistant", "content": response.choices[0].message.content})
        
        return response.choices[0].message
```

### Pattern 3: Behavior Tree with LLM Decisions
```
                    ┌─────────────────────┐
                    │   Selector (LLM)     │
                    │ "What should NPC do?" │
                    └──────────┬──────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │ Idle     │   │ Patrol   │   │ Talk to  │
         │ Wander   │   │ Route    │   │ Player   │
         └──────────┘   └──────────┘   └──────────┘
```

```python
# Behavior node with LLM decision
def npc_behavior_selector(npc_state, game_context):
    prompt = f"""NPC State: {npc_state}
Game Context: {game_context}

Choose ONE action:
- idle_wander: Walk around aimlessly
- patrol: Follow patrol route
- talk_to_player: Engage with nearby player
- trade: Offer items for sale
- fight: Attack nearby enemies

Respond with just the action name."""
    
    decision = llm_call(prompt).strip()
    return decision
```

### Pattern 4: NPC with Memory (Vector Store)
```python
from sentence_transformers import SentenceTransformer
import numpy as np

class NPCMemory:
    def __init__(self, max_memories=100):
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.memories = []
        self.embeddings = []
        self.max_memories = max_memories
        
    def add_memory(self, text, importance=1.0):
        emb = self.encoder.encode(text)
        self.memories.append({"text": text, "importance": importance})
        self.embeddings.append(emb)
        
        # Forget least important if over limit
        if len(self.memories) > self.max_memories:
            idx = min(range(len(self.memories)), key=lambda i: self.memories[i]["importance"])
            del self.memories[idx]
            del self.embeddings[idx]
    
    def recall(self, query, top_k=3):
        query_emb = self.encoder.encode(query)
        scores = [np.dot(query_emb, m) for m in self.embeddings]
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [self.memories[i]["text"] for i in top_indices]
```

## Unity Sentis Integration

### Export Model to ONNX
```bash
# Install optimum
pip install optimum

# Export to ONNX
optimum-cli export onnx --model microsoft/Phi-3-mini-4k-instruct ./phi3_onnx
```

### Unity C# Script (Sentis)
```csharp
using UnityEngine;
using Unity.Sentis;
using System.Collections.Generic;

public class SentisNPC : MonoBehaviour
{
    public string npcName = "Guard";
    public TextAsset onnxModel;
    
    private IWorker worker;
    private Dictionary<string, Tensor> inputs;
    
    void Start()
    {
        // Load ONNX model
        Model model = ModelLoader.Load(onnxModel);
        worker = WorkerFactory.CreateWorker(BackendType.GPUCompute, model);
    }
    
    public string GetResponse(string playerInput)
    {
        // Tokenize input (simplified)
        int[] tokens = TokenizeInput(playerInput);
        Tensor<int> inputTensor = new Tensor<int>(new TensorShape(1, tokens.Length), tokens);
        
        // Run inference
        worker.Execute(inputTensor);
        Tensor<float> output = worker.PeekOutput() as Tensor<float>;
        
        // Post-process
        return DecodeOutput(output);
    }
    
    void OnDestroy()
    {
        worker?.Dispose();
    }
    
    private int[] TokenizeInput(string text)
    {
        // Simplified — use actual tokenizer in production
        return new int[] { 1, 2, 3, 4 };
    }
    
    private string DecodeOutput(Tensor<float> output)
    {
        return "Hello adventurer! I have quests for you.";
    }
}
```

### Importing and Using Sentis in Unity
1. Package Manager → Install **Sentis** (Unity Registry)
2. Export model to ONNX (optimum-cli)
3. Drag `.onnx` file into Unity Assets
4. Create a C# script as above
5. Attach to NPC GameObject
6. Call `GetResponse()` on player interaction

## Cubzh Integration

### Cubzh Lua NPC Script
```lua
-- Cubzh NPC using HF Inference API
local npc = {
    name = "Wise Sage",
    position = {-10, 2, 5},
    dialog_history = {}
}

function npc:on_interact(player)
    local response = self:call_hf_api("You are a wise sage in a fantasy world. Keep replies short.")
    self:say(response)
end

function npc:call_hf_api(system_prompt)
    local url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    local headers = {
        Authorization = "Bearer hf_YOUR_TOKEN_HERE",
        ["Content-Type"] = "application/json"
    }
    
    local body = {
        inputs = system_prompt .. "\nPlayer: " .. self:get_last_input() .. "\nSage:",
        parameters = { max_new_tokens = 80 }
    }
    
    -- Cubzh http request
    local req = http.post(url, headers, body)
    local result = json.decode(req.body)
    return result[1].generated_text
end

function npc:say(text)
    -- Display speech bubble above NPC
    ui.speech_bubble(self.position, text, 5.0)  -- 5 second duration
end

function npc:get_last_input()
    return "Hello, who are you?"
end

-- Register NPC
game.on("player_interact", function(player, target)
    if target == npc then
        npc:on_interact(player)
    end
end)
```

### Cubzh Asset Generation Pipeline
```lua
-- Generate a texture using HF in Cubzh
local function generate_texture(prompt)
    local url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    local headers = {
        Authorization = "Bearer hf_YOUR_TOKEN",
        ["Content-Type"] = "application/json"
    }
    
    local response = http.post(url, headers, {
        inputs = "game texture, " .. prompt .. ", pixel art style"
    })
    
    -- Convert response to Cubzh texture
    local texture = texture.from_bytes(response.body)
    return texture
end

-- Usage
local stone_texture = generate_texture("stone wall, medieval fantasy, 16x16")
```

## AI Asset Generation

### Textures & Sprites
```python
from diffusers import StableDiffusionPipeline
import torch

# Generate game textures
pipe = StableDiffusionPipeline.from_pretrained(
    "dreamshaper-8",
    torch_dtype=torch.float16
).to("cuda")

prompts = [
    "stone wall texture, top-down RPG, seamless",
    "chest with gold, pixel art style, isometric",
    "forest background, side-scrolling game",
    "character portrait, fantasy knight, digital art"
]

for i, prompt in enumerate(prompts):
    image = pipe(prompt, width=512, height=512).images[0]
    image.save(f"asset_{i}.png")
```

### Voice Dialogue (TTS)
```python
from transformers import pipeline

# Generate NPC voice lines
tts = pipeline("text-to-speech", model="microsoft/speecht5_tts")

npc_lines = [
    "Welcome to our village, traveler!",
    "I've been expecting you.",
    "Beware of the dark forest to the north."
]

for i, line in enumerate(npc_lines):
    result = tts(line)
    with open(f"npc_line_{i}.wav", "wb") as f:
        f.write(result["audio"])
```

## Pitfalls

- LLM inference latency is high for real-time NPC dialogue — cache responses and use streaming.
- Unity Sentis supports limited ops — test ONNX export compatibility (use ONNX Runtime validation first).
- Generated assets may need manual cleanup before use in production.
- Always check model licenses for commercial game use.
- Cubzh HTTP requests are synchronous — avoid blocking the main loop with long inference calls.
- NPC memory grows unbounded — implement forgetting or summarization for long sessions.
- LLM-based NPCs can hallucinate game state — validate actions before applying them.

## Verification

```python
from transformers import pipeline
pipe = pipeline("text-generation", model="gpt2")
print(pipe("NPC dialogue: Hello adventurer,")[0]["generated_text"])
```
