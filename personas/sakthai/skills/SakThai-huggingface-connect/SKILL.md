---
name: SakThai-huggingface-connect
description: "Use when setting up or connecting to Hugging Face Inference Providers in opencode. Covers token creation, /connect setup, model selection, and config wiring."
---

# Hugging Face Connect

## Steps

1. **Create a Hugging Face token** at:
   https://huggingface.co/settings/tokens/new?ownUserPermissions=inference.serverless.write&tokenType=fineGrained
   - Required permission: `inference.serverless.write`
   - Token type: Fine-grained

2. **Add the token** via one of:
   - TUI: Run `/connect`, search "Hugging Face", paste the token
   - Env var: `HUGGINGFACE_API_KEY=hf_xxx`

3. **Select a model**: Run `/models` in opencode TUI

4. **Config file** (`opencode.json`):
   ```json
   {
     "$schema": "https://opencode.ai/config.json",
     "model": "huggingface/Kimi-K2-Instruct",
     "provider": {
       "huggingface": {}
     }
   }
   ```

5. **Restart** opencode after making config changes.
