# Sak Family Agents Summary

The Sak Family consists of 5 Telegram agents that share a single long-term memory (Supermemory "brain") but run separate live sessions.

## 1. SakKing (Lead)
- **Role**: Lead & Orchestrator / Master of Code & Self-Healing
- **Model**: `qwen3-coder:480b` (Ollama Cloud) with fallback `gpt-oss:120b`
- **Skills**: Orchestration, Heavy Coding, Self-Healing.

## 2. SakSee
- **Role**: Master of Web
- **Model**: `gpt-5.4-mini` (OpenAI Codex OAuth) with fallback `gpt-oss:120b`
- **Skills**: Web automation via Playwright, Chrome DevTools.

## 3. SakThai
- **Role**: Master of Hugging Face
- **Model**: `claude-opus-4-8` (Anthropic auth) with fallback `gpt-oss:120b`
- **Skills**: Hugging Face Hub/Inference, GitHub, Composio integrations.

## 4. SakSit
- **Role**: Master of Social Media
- **Model**: `kimi-k2.7-code` (Ollama Cloud) with fallback `gpt-oss:120b`
- **Skills**: Instagram image/video creation via Hugging Face Spaces, Terminal sandbox in Modal.

## 5. SakTan
- **Role**: Helper
- **Model**: `gemini-2.5-flash-lite` (Google Gemini API key) with fallback chain (`gemini-3-flash-preview` → `gemini-3.1-flash-lite` → `gemini-3.5-flash` → `gemini-2.5-flash-preview-native-audio-dialog`)
- **Skills**: Daily ops (calendar, reminders, email, tasks, life admin).
