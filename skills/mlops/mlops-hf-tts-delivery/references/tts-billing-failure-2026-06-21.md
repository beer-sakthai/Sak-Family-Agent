## TTS Billing Failure — 2026-06-21

**Error**: `Insufficient available balance for requested reservation`

**Provider**: openai (tts-1, voice: alloy)

**Error Code**: 402

**Details**:
- Requested: $0.0000126
- Subscription balance: $0.10 (available)
- Purchased balance: $0.00
- Org ID: cmqfl720l0084lb0c63xiwdzq
- Subscription ID: cmqfl8s6q04vmjv0cqwdbcuh7
- Purchased ID: cmqfl720m0086lb0c0190f1qx

**Root Cause**: Nous subscription funding expired or was exhausted.

**Resolution**: Contact Nous support to restore subscription, or switch to local TTS (espeak + ffmpeg) in WSL.

**Note**: This error is **not** a bug — it is a billing constraint. The agent must fail silently and fall back to text.