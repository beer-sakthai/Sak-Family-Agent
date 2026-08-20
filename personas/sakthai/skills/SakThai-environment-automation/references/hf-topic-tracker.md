# HF Topic Tracker Pattern

When setting up a recurring learning cron job that must never repeat topics:

## Core pattern

1. **JSON tracker file** at `~/profiles/sakthai/cron/hf-topics-covered.json`
2. Cron job reads tracker → picks unlisted topic → learns → updates tracker
3. Each tick appends the new topic so no repeat ever occurs

## Tracker file format

```json
["topic-one", "topic-two", "topic-three"]
```

## Cron prompt flow

1. Read tracker file via `read_file`
2. Pick brand-new topic not in list
3. Research via `web_search`
4. Improve/create skill with findings
5. Sync to GitHub (git commit + push)
6. Write FULL updated JSON array back to tracker
7. Deliver briefing

## Topics scope

The Hugging Face ecosystem is vast — pull from these categories to ensure diversity:
- Models (architectures, formats, quantization, libraries)
- Datasets (creation, streaming, SQL, evaluation)
- Spaces (Gradio, Streamlit, ZeroGPU, secrets, hardware)
- Hub API (webhooks, collections, discussions, PRs, search)
- Inference (serverless, endpoints, TGI, vLLM, Providers)
- Training (AutoTrain, TRL, PEFT, DeepSpeed, FSDP)
- CLI (hf commands, buckets, extensions, skills)
- Libraries (Transformers, Diffusers, Tokenizers, Datasets, Accelerate)
- Community (Orgs, Papers, Leaderboards, Licensing)
- Infrastructure (Inference Endpoints, Docker, Spaces hardware)
- Policies (Gated repos, dataset privacy, DUA agreements)

## Pitfalls

- Do NOT hardcode the topic list — let the agent pick from first principles each tick
- The tracker grows unbounded — at ~1,440 ticks/day, it'll be ~500 topics/month. This is fine; JSON handles it.
- Cron job must have `enabled_toolsets: ["web", "terminal", "file"]` to access web_search, git, and file operations
