---
name: mlops-hf-tts-delivery
title: Reliable TTS Delivery on Hugging Face Systems
author: SakThai
version: 1.0
description: How to deliver voice replies to Beer when TTS providers fail due to billing or environment restrictions — with fallbacks, verification, and silent resilience.
---

# HF TTS Delivery — Reliable Voice Output for Silent Automation

## Trigger Condition
This skill activates when:
- The user requires voice replies (via `voice: true` in config)
- TTS generation fails with `BILLING_ERROR` or `Insufficient funds`
- The system is WSL, non-root, PEP 668-managed, and cannot install packages

## Goal
Deliver voice replies **silently and reliably** — even when OpenAI/Edge TTS are blocked — without user intervention.

## Steps

1. **Check TTS provider** — Use `hermes config show | grep -A 3 tts` to confirm `provider: openai` or `edge`
2. **Attempt primary TTS** — Call `text_to_speech` with configured provider and voice
3. **If it fails with `BILLING_ERROR`**:
   - Log the error to `references/tts-billing-failure-2026-06-21.md`
   - Do NOT retry the same provider — it will fail again
   - Fallback to `espeak` via `ffmpeg` if available
4. **If `espeak` is unavailable**:
   - Generate a **text summary** with `⚠️ VOICE FAILED: Billing limit reached. See references/tts-billing-failure-2026-06-21.md`
   - Send text reply only — **do not error or notify**
5. **Verify delivery** — Check Telegram for message receipt (via session_search)
6. **Auto-alert** — If this fails 3x in 24h, trigger `hermes curator alert "TTS delivery degraded for Beer"`

## Pitfalls

- ❌ **Assuming `sudo` works** — WSL Hermes runs as user, no sudo. Never use `sudo apt install`.
- ❌ **Using `pip install --user`** — PEP 668 blocks it. Use `uv` or `venv` if allowed.
- ❌ **Switching providers on failure** — Edge → OpenAI → Edge again wastes quota. Pick one and fail silently.
- ❌ **Expecting `espeak` to be installed** — It rarely is on fresh WSL. Always test first.
- ❌ **Using `text_to_speech` without fallback** — This causes silent user frustration.

## Verification

Run this test after config changes:

```bash
hermes config show | grep -A 3 tts
python3 -c "import sys; print('espeak' if any('espeak' in p for p in sys.path) else 'not found')"
```

If `espeak` is not found, and TTS fails — **this skill has done its job**.

## Support Files

- `references/tts-billing-failure-2026-06-21.md` — Contains the exact error transcript from this session
- `scripts/test-tts-fallback.sh` — Safe script to test fallback path

## See Also

- `hermes-agent` — for config management
- `mlops/hf-jobs` — for compute isolation

---