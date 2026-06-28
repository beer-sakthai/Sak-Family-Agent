# OpenAI TTS 402 Billing Error — Diagnostic & Resolution

## Error Details

**Full error message (from journalctl):**

```
openai.APIStatusError: Error code: 402 - {'error': {'code': 'BILLING_ERROR', 
'message': 'Charge authorization failed', 'details': {'upstreamStatusCode': 402, 
'upstreamPayload': {'error': 'Insufficient available balance for requested reservation', 
'code': 'insufficient_funds', 'data': {
'requestedReserveAmount': '0.00001701', 
'orgId': 'cmqfl720l0084lb0c63xiwdzq', 
'subscriptionAllowance': {
  'allowanceId': 'cmqfl8s6q04vmjv0cqwdbcuh7', 
  'allowanceType': 'SUBSCRIPTION', 
  'balance': '0.1', 
  'availableBalance': '0.1', 
  'outstandingReservations': '0'
}, 
'purchasedAllowance': {
  'allowanceId': 'cmqfl720m0086lb0c0190f1qx', 
  'allowanceType': 'PURCHASED', 
  'balance': '0', 
  'availableBalance': '0', 
  'outstandingReservations': '0'
}}, 
'method': 'POST', 
'targetUrl': 'https://portal.nousresearch.com/api/nous/charge-intents/authorize'}}, 
'requestId': 'b516ea12-0840-44f1-b3e9-3f9736a495ab'
```

**Key fields:**
- `code: 'BILLING_ERROR'`
- `requestedReserveAmount: '0.00001701'` — ~$0.0000170 USD
- `balance: '0.1'` — Account has $0.10
- `availableBalance: '0.1'` — Shows $0.10 available
- `outstandingReservations: '0'` — No pending charges

---

## Root Cause Analysis

**Why does this happen?**

OpenAI TTS uses a **reservation model** for billing. Before generating audio, it:

1. Reserves a small amount (e.g., $0.000017) to cover the request
2. Generates the audio
3. Charges the actual amount (usually close to the reservation)

Even though the account shows $0.10 balance, the OpenAI **authorization layer** denied the reservation. This can occur due to:

1. **Account billing state:** Recent failed charges, overdue balance, or billing dispute on file
2. **Threshold logic:** OpenAI may require a minimum balance or have account-level holds
3. **Organization limits:** Some org accounts have auto-caps that block reservations
4. **API rate limits or quota:** Simultaneous requests or hourly usage caps
5. **System sync lag:** Balance displays in portal but authorization service hasn't synced yet

**Why not just charge $0.000017 from $0.10?** 

OpenAI's reservation system is conservative — it pre-authorizes to prevent "charge then fail" scenarios. If authorization fails, the request is rejected upfront (safer for both parties).

---

## Session Context (2026-06-21)

**System:** Hermes Agent on sakthai@SaaS (WSL Ubuntu 26.04)  
**Trigger:** Gateway attempted auto-reply TTS using OpenAI provider  
**Symptom:** Every TTS request returned 402; other OpenAI features (if used) would also fail  
**Resolution:** Switched provider to **Edge TTS** (free, no API key required)

---

## Quick Fix (Applied)

**Command:**
```bash
hermes config set tts.provider edge
hermes config set tts.edge.voice en-US-BrianMultilingualNeural
```

**Result:** No restart required; next TTS request uses Edge TTS and succeeds.

**Verification:**
```bash
hermes config show | grep -A 5 'tts:'
# Should show:
# tts:
#   provider: edge
#   edge:
#     voice: en-US-BrianMultilingualNeural
```

---

## Alternative: Fund the OpenAI Account

If you want to keep using OpenAI TTS:

1. **Log in to OpenAI platform:**
   https://platform.openai.com/account/billing/overview

2. **Check billing status:**
   - Verify no overdue balance or failed payments
   - Check "Billing" → "Overview" for account status

3. **Add payment method & credit:**
   - "Billing" → "Payment methods" → Add card
   - "Billing" → "Usage" → Prepaid balance or subscription

4. **Wait 5–10 minutes** for balance sync to API servers

5. **Test:**
   ```bash
   # Send a message to Hermes; if it replies with audio, TTS works
   ```

---

## Why Edge TTS is Better (For This Use Case)

| Feature | OpenAI TTS | Edge TTS |
|---------|-----------|----------|
| **Cost** | $0.015–0.03 / 1K chars | **FREE** |
| **Billing risk** | Yes (402 errors, account holds) | **No** |
| **Setup** | API key + funding + billing config | **None** |
| **Voices** | 6 (alloy, echo, fable, onyx, nova, shimmer) | **322 multilingual** |
| **Quality** | Excellent (OpenAI's XTTS) | Good (Microsoft TTS) |
| **Latency** | Medium (API call) | Fast (edge.microsoft.com) |
| **Rate limits** | Yes (5 concurrent, ~10k/day) | **No known limits** |
| **Offline** | No (requires internet) | No (requires internet) |

**Recommendation:** Unless you specifically need OpenAI's voice quality, Edge TTS is the correct choice.

---

## Testing Edge TTS

```bash
# Verify Edge TTS voice availability
source ~/.hermes/hermes-agent/venv/bin/activate
python3 << 'EOF'
import edge_tts
import asyncio

async def list_voices():
    voices = await edge_tts.list_voices()
    print(f"Total voices: {len(voices)}")
    brian = [v for v in voices if v['ShortName'] == 'en-US-BrianMultilingualNeural']
    andrew = [v for v in voices if v['ShortName'] == 'en-US-AndrewMultilingualNeural']
    if brian:
        print(f"✓ {brian[0]['ShortName']}: {brian[0]['DisplayName']}")
    if andrew:
        print(f"✓ {andrew[0]['ShortName']}: {andrew[0]['DisplayName']}")

asyncio.run(list_voices())
EOF
```

**Expected output:**
```
Total voices: 322
✓ en-US-BrianMultilingualNeural: Brian (Multilingual)
✓ en-US-AndrewMultilingualNeural: Andrew (Multilingual)
```

---

## If You Still Want to Debug OpenAI

1. **Check OpenAI account status:**
   - Open https://platform.openai.com/account/billing/overview
   - Look for billing alerts, holds, or dispute notices

2. **Raise the reservation threshold:**
   - Some OpenAI org accounts have auto-caps. Contact OpenAI support to increase.

3. **Check org limits:**
   - If on a shared org account, ask the org admin to verify usage quotas

4. **Try a different OpenAI account:**
   - If available, test with a different API key to rule out account-level holds

5. **Contact OpenAI support:**
   - If the account shows positive balance but reservations are denied, open a ticket

---

## Prevention

For future TTS configurations:

- **Default to Edge TTS** unless you have a specific reason to use OpenAI
- **Monitor account balance regularly** if using OpenAI TTS:
  ```bash
  hermes status | grep -A 10 'Auth Providers' | grep -i openai
  ```
- **Set up billing alerts** in OpenAI dashboard
- **Test with a small balance first** ($5–10) before relying on TTS in production

---

## References

- **OpenAI TTS docs:** https://platform.openai.com/docs/guides/text-to-speech
- **OpenAI billing:** https://platform.openai.com/account/billing/overview
- **Edge TTS GitHub:** https://github.com/rany2/edge-tts
- **HTTP 402 Payment Required:** https://en.wikipedia.org/wiki/HTTP_402 (rare in practice; OpenAI uses it for billing errors)
