---
name: hermes-tts-setup
title: Hermes TTS Setup & Provider Configuration
description: Configure text-to-speech providers, diagnose billing issues, manage voice selection, and set Edge TTS as the free default.
tags:
  - hermes
  - tts
  - configuration
  - audio
  - billing
related:
  - hermes-agent
  - hermes-gateway-health-audit
trigger: |
  User asks to configure TTS, switch providers, fix voice generation, diagnose 402/billing errors, select voices, or ensure free TTS is active.
---

# Hermes TTS Setup & Provider Configuration

Hermes supports 10+ TTS providers. This skill covers configuration, troubleshooting billing issues, voice selection, and establishing Edge TTS as the free default.

## Quick Reference

| Provider | Cost | Speed | Quality | Setup | Notes |
|----------|------|-------|---------|-------|-------|
| **Edge TTS** | **FREE** | Fast | Good | Zero API keys | **Recommended default** |
| OpenAI TTS | $0.015–0.03 / 1K chars | Medium | Excellent | Needs OpenAI key + funding | Billing errors common |
| ElevenLabs | $8–22/mo | Medium–slow | Excellent | Needs account | Pay-as-you-go option |
| Google Gemini | Free tier / paid | Medium | Good | Needs Gemini API key | Rate limits apply |
| Piper (local) | FREE | Slow | Fair | Download voice model | Runs on CPU; offline |

**Default recommendation:** Edge TTS (free, no billing, 322 voices, no rate limits).

---

## Configuration

### 1. Set Edge TTS as Default (Recommended)

```bash
hermes config set tts.provider edge
hermes config set tts.edge.voice en-US-BrianMultilingualNeural
```

**Verify:**
```bash
hermes config show | grep -A 5 'tts:'
```

Expected output:
```yaml
tts:
  provider: edge
  edge:
    voice: en-US-BrianMultilingualNeural
```

### 2. Available Edge TTS Voices

Edge ships with 322 multilingual voices. Common variants:

- **English (US):** en-US-AndrewMultilingualNeural, en-US-BrianMultilingualNeural, en-US-AvaMultilingualNeural
- **English (UK):** en-GB-RyanMultilingualNeural, en-GB-SoniaMultilingualNeural
- **Other languages:** Hundreds of voices across 100+ locales

**List all voices:**
```bash
# From the Hermes venv (required):
source ~/.hermes/hermes-agent/venv/bin/activate
python3 << 'EOF'
import edge_tts
import asyncio

async def list_voices():
    voices = await edge_tts.list_voices()
    for v in voices[:20]:  # Show first 20
        print(f"  {v['ShortName']}: {v['DisplayName']}")

asyncio.run(list_voices())
EOF
```

### 3. Switch to Another Provider (Optional)

**To OpenAI TTS:**
```bash
hermes config set tts.provider openai
hermes config set tts.openai.voice alloy  # or: echo, fable, onyx, nova, shimmer
```
Requires: `OPENAI_API_KEY` env var set, account with funding.

**To ElevenLabs:**
```bash
hermes config set tts.provider elevenlabs
hermes config set tts.elevenlabs.voice_id pNInz6obpgDQGcFmaJgB  # replace with your voice ID
```
Requires: `ELEVENLABS_API_KEY` env var, subscription.

**To Piper (local, offline):**
```bash
hermes config set tts.provider piper
hermes config set tts.piper.voice en_US-lessac-medium
```
Requires: `espeak-ng` and voice model download (slow first run; subsequent runs use cached model).

---

## Troubleshooting

### Issue: OpenAI TTS Returns 402 Billing Error

**Symptom:**
```
openai.APIStatusError: Error code: 402 - {'error': {'code': 'BILLING_ERROR', 
'message': 'Charge authorization failed', 'details': {'upstreamStatusCode': 402, 
'upstreamPayload': {'error': 'Insufficient available balance for requested reservation'...
```

**Root cause:** OpenAI account has insufficient balance to reserve the charge, even if total balance appears positive. Reservation authorization failed.

**Fix (choose one):**

1. **Switch to Edge TTS (recommended):**
   ```bash
   hermes config set tts.provider edge
   hermes config set tts.edge.voice en-US-BrianMultilingualNeural
   ```
   No restart needed; takes effect on next message.

2. **Fund the OpenAI account:**
   - Log in to https://platform.openai.com/account/billing/overview
   - Add payment method and prepaid credit
   - Wait 5–10 minutes for balance to sync
   - Retry TTS request

3. **Raise the reservation amount in OpenAI settings:**
   - Some accounts have low auto-reserve thresholds; increase in billing dashboard

---

### Issue: TTS Not Working After Config Change

**Diagnosis:**
```bash
# Check Hermes gateway is running:
systemctl --user status hermes-gateway

# Check the config was saved:
hermes config show | grep -A 10 'tts:'

# Check the gateway logs for TTS errors:
journalctl --user -u hermes-gateway -n 50 --grep='TTS\|tts\|speech'
```

**Common causes:**
- **Gateway not reloaded:** Config is loaded at startup. Gateway was restarted? If not, restart it (if possible from outside the gateway process):
  ```bash
  # From a shell outside the gateway:
  systemctl --user restart hermes-gateway
  ```
- **API key missing or invalid:** If using OpenAI/ElevenLabs, verify `$OPENAI_API_KEY` or `$ELEVENLABS_API_KEY` is set in the shell that started the gateway.
- **Voice name typo:** Double-check voice name spelling. Edge voice names are case-sensitive (e.g., `en-US-BrianMultilingualNeural`, not `brian`).

---

### Issue: Edge TTS Slow or Returning No Audio

**Cause:** Usually transient network glitch or momentary API unavailability.

**Mitigation:**
- Hermes retries TTS automatically (default 3 attempts).
- If retry succeeds, no action needed.
- If repeated failures occur, switch to OpenAI (if funded) or Piper (local, but slower).

---

## Pitfalls

1. **Do NOT set TTS provider to an API (OpenAI, ElevenLabs, Gemini) without funding/setup first.** If the account lacks credits, every reply fails with 402 or auth error. Edge TTS is always safe.

2. **Edge TTS voice names are exact.** `en-US-BrianMultilingualNeural` ✓, `Brian` ✗, `en-US-brian` ✗.

3. **Config changes made via `hermes config set` take effect on the NEXT message.** If you're inside the Hermes gateway (e.g., in a Telegram reply), the change won't apply until the gateway reloads or the next request comes in.

4. **Local voices (Piper) require downloading the model on first use.** The first TTS call may timeout or take 30+ seconds. Subsequent calls use the cached model.

5. **OpenAI billing is hard to debug.** If you see "Insufficient available balance" even with a positive balance, it means the reservation was denied. The user portal and API sometimes disagree about available credit. Add more credit, wait 5+ minutes, or switch to Edge.

6. **STT (speech-to-text) is separate from TTS.** If you configure the TTS provider but leave STT on OpenAI and the account is unfunded, STT will fail independently. Check `stt.provider` separately.

---

## Verification

After configuration, verify TTS is active and the correct provider is loaded:

```bash
# Check config:
hermes config show | grep -A 15 'tts:'

# Generate a test voice message (manual test):
# Send any message to your Hermes bot; if it replies with audio, TTS is working.
```

**Expected:** Replies include audio attachments (or voice bubbles in Telegram).

---

## References

- **Edge TTS** — Microsoft's free cloud TTS. https://github.com/rany2/edge-tts
- **OpenAI TTS** — https://platform.openai.com/docs/guides/text-to-speech
- **ElevenLabs** — https://elevenlabs.io/docs
- **Piper** — Offline TTS; voice models at https://huggingface.co/rhasspy/piper-voices

---

## Related Skills

- `hermes-agent` — General Hermes configuration and CLI reference.
- `hermes-gateway-health-audit` — Verify TTS and other gateway services are online.
