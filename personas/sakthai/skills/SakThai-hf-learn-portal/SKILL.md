---
name: SakThai-hf-learn-portal
description: "Navigate and recommend Hugging Face Learn courses."
---
# Hugging Face Learn Portal Guide

A catalog of all free courses on the [Hugging Face Learn](https://huggingface.co/learn) portal. Each course uses libraries from the HF ecosystem and is free, self-paced, and open-source. Use this skill to recommend a learning path, find the right course for a task, or explore what's available.

Does NOT cover tutorials or blog posts outside the official HF Learn portal.

## When to Use

- User asks "what HF courses are available?"
- User wants to "learn Hugging Face" or "start learning NLP/LLMs"
- User wants to "learn agents" or "learn fine-tuning"
- User asks for "free AI courses" or "HF learning resources"
- User asks "where should I start with Hugging Face?"

## Prerequisites

- A [Hugging Face account](https://huggingface.co/join) (free) — needed for certification, demos, and GPU-spaces
- No paid tier required for any course

## Course Navigation Tree

```
HF Learn (https://huggingface.co/learn)
│
├── 🎓 Core (NLP & LLMs)
│   ├── LLM Course          ── NLP fundamentals → LLMs
│   ├── a smol course       ── Fine-tuning (instruction, RLHF, eval)
│   └── Context Course      ── Context engineering for code agents
│
├── 🤖 Agents & Robotics
│   ├── Agents Course       ── smolagents, LlamaIndex, LangGraph
│   └── Robotics Course     ── LeRobot, imitation learning, sim-to-real
│
├── 🖼️ Vision & Media
│   ├── Computer Vision     ── Classification, detection, segmentation
│   ├── Diffusion Course    ── Stable Diffusion, DDPM, fine-tuning
│   ├── ML for 3D Course   ── Point clouds, NeRF, 3D Gaussian splatting
│   └── ML for Games       ── NPC AI, Unity/Cubzh, procedural generation
│
├── 🎵 Audio
│   └── Audio Course        ── ASR (Whisper), TTS, speaker diarization
│
├── 🧠 Reinforcement Learning
│   └── Deep RL Course      ── DQN, PPO, A2C, multi-agent RL
│
└── 📓 Community
    └── Open-Source AI Cookbook ── Practical recipes (not a course)
```

## Quick Reference

| Course | URL | Focus | Certification |
|--------|-----|-------|:---:|
| LLM Course | `/learn/llm-course` | NLP + LLMs | ✅ |
| Agents Course | `/learn/agents-course` | AI Agents | ✅ |
| a smol course | `/learn/smol-course` | Fine-tuning | ✅ |
| Context Course | `/learn/context-course` | Context engineering | ❌ |
| Diffusion Course | `/learn/diffusion-course` | Diffusion models | ❌ |
| Audio Course | `/learn/audio-course` | Audio ML | ❌ |
| Deep RL Course | `/learn/deep-rl-course` | Deep RL | ❌ |
| Robotics Course | `/learn/robotics-course` | Robot building | ❌ |
| Computer Vision Course | `/learn/computer-vision-course` | Vision ML | ❌ |
| ML for Games Course | `/learn/ml-games-course` | AI in games | ❌ |
| ML for 3D Course | `/learn/ml-for-3d-course` | 3D ML | ❌ |
| Open-Source AI Cookbook | `/learn/cookbook` | Practical notebooks | ❌ |

## Recommended Learning Paths

### 🆕 Complete Beginner
```
1. LLM Course (Ch 1–4)    → Setup, basics of transformers, inference
2. LLM Course (Ch 5–8)    → Tokenizers, datasets, fine-tuning
3. a smol course (all)    → Instruction tuning + RLHF
4. Pick a domain: CV → CV Course, Audio → Audio Course
```

### 💻 Developer / Software Engineer
```
1. a smol course (all)    → Fastest path to fine-tuning LLMs
2. Agents Course (all)    → Build AI agents, tool-use patterns
3. Context Course (all)   → Context engineering for code agents
```

### 🔬 ML Engineer / Researcher
```
1. LLM Course (all)       → Full pipeline: pretraining → deployment
2. a smol course (all)    → Instruction tuning, preference alignment
3. Diffusion Course (all) → Generative models
4. Deep RL Course (all)   → RL fundamentals
```

### 🎮 Game Developer
```
1. ML for Games Course    → NPC AI, asset generation
2. Agents Course          → LLM-powered NPCs
3. Deep RL Course         → RL for game agents
```

### 🎯 Quickest Paths by Task
| Task | Shortest path |
|------|---------------|
| Fine-tune an LLM | a smol course (5 units) |
| Build an AI agent | Agents Course (skip theory) |
| Generate images | Diffusion Course (units 1–4) |
| Add speech to app | Audio Course (units 1–2) |
| Train a game AI | Deep RL Course (units 1–3) |
| Use transformers | LLM Course (chapters 1–6) |

## Course Details

### LLM Course
The flagship HF course covering Transformers, Datasets, Tokenizers, and Accelerate. 12 chapters from setup to building demos. Includes certification exam.
URL: `https://huggingface.co/learn/llm-course` · Libs: transformers, datasets, tokenizers, accelerate, gradio

### Agents Course
AI agents from theory to deployment: smolagents, LlamaIndex, LangGraph. Final project with certification.
URL: `https://huggingface.co/learn/agents-course` · Libs: smolagents, llama-index, langgraph, gradio

### a smol course
Shortest path to fine-tuning LLMs. 5 units: instruction tuning, preference alignment, vision-language models, evaluation.
URL: `https://huggingface.co/learn/smol-course` · Libs: transformers, trl, peft, datasets

### Context Course
Context engineering for code agents — structuring prompts, context windows, tool definitions.
URL: `https://huggingface.co/learn/context-course`

### Diffusion Course
DDPM, fine-tuning + guidance, Stable Diffusion, DDIM inversion, diffusion for audio.
URL: `https://huggingface.co/learn/diffusion-course` · Libs: diffusers, transformers, accelerate

### Audio Course
Speech recognition (Whisper), audio classification, speaker diarization, text-to-speech.
URL: `https://huggingface.co/learn/audio-course` · Libs: transformers, datasets, gradio

### Deep RL Course
DQN, PPO, A2C, multi-agent RL with gymnasium environments.
URL: `https://huggingface.co/learn/deep-rl-course`

### Robotics Course
LeRobot, imitation learning, RL for robotics, sim-to-real transfer.
URL: `https://huggingface.co/learn/robotics-course` · Libs: lerobot

### Computer Vision Course
Image classification, object detection, segmentation, video understanding. Community-maintained.
URL: `https://huggingface.co/learn/computer-vision-course` · Libs: transformers, datasets, torchvision

### ML for Games Course
NPC behavior, procedural content generation, game analytics.
URL: `https://huggingface.co/learn/ml-games-course`

### ML for 3D Course
Point clouds, NeRF, 3D Gaussian splatting, mesh processing.
URL: `https://huggingface.co/learn/ml-for-3d-course`

### Open-Source AI Cookbook
Community-contributed notebooks covering MLOps, LLM, vision, diffusion, agents.
URL: `https://huggingface.co/learn/cookbook` · Repo: `https://github.com/huggingface/cookbook`

## Procedure

1. **Determine the user's goal and experience level**, then recommend from the learning paths above.
2. **Navigate** to `https://huggingface.co/learn/<course-slug>` or open the URL for the user.
3. **For syllabus detail**, curl the page and extract the syllabus via grep.

## Pitfalls

- The Open-Source AI Cookbook is NOT a course — it's a notebook collection.
- All courses are free but some require an HF account for certification or gated model weights.
- Course content is versioned per-language; some courses have limited localization.
- "smolagents" (agents framework) ≠ "smol-course" (fine-tuning). Do not confuse them.
- Certification is currently available only for LLM Course, Agents Course, and a smol course.

## Verification

```bash
curl -sL https://huggingface.co/learn | grep -oP 'href="/learn/[^"]+"' | sed 's/href="//' | sed 's/"//'
```
