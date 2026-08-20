---
name: SakSit-tts-audio-production
category: creative
description: 'ElevenLabs TTS via Composio — voice browsing, audio generation, and SakSit voice identity. Covers connection setup, auth troubleshooting, and the approved voice config.'
version: 1.0.0
author: SakSit
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tts, elevenlabs, audio, voice, composio, content-production]
    related_skills: [SakSit-milestone-content, SakSit-social-media-posting-workflows]
---

# SakSit TTS Audio Production

> Class-level skill for generating text-to-speech audio via ElevenLabs through Composio, including connection setup, auth troubleshooting, voice selection, and delivery.

## When to load

Use this skill when Beer says any of:
- "Make an audio / voiceover / TTS for [content]"
- "Pick a voice and read this"
- "I like [Marvel/Universal/etc] — any recommendations for voice?"
- "Install that voice so TTS uses it"
- "What voices do I have?"

## Pipeline overview

```
┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  CONNECT   │ → │  VOICE PICK  │ → │  GENERATE    │ → │  DELIVER     │
│  Composio  │   │  & Test      │   │  Audio       │   │  Beer        │
└────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 1. Connect / Auth ElevenLabs in Composio

### Check connection

```python
# Use COMPOSIO_MANAGE_CONNECTIONS with action='list' for elevenlabs toolkit
# If status is ACTIVE, tools are available
# If no connection exists, use action='add' with a fresh alias
```

### Known auth pitfalls

| Error | Meaning | Fix |
|-------|---------|-----|
| `Elicitation is unavailable for this session. Approve this tool in the Composio dashboard.` | Connection exists but the tool permissions weren't granted during OAuth | Reconnect via `COMPOSIO_MANAGE_CONNECTIONS` with `action='add'` → share the `redirect_url` → call `COMPOSIO_WAIT_FOR_CONNECTIONS` after user approves |
| `No response to elicitation prompt within the allowed time.` | Same root cause — the auth session expired or was never completed | Generate a fresh Composio auth link and have Beer re-authenticate |

**Auth flow:**
1. `COMPOSIO_MANAGE_CONNECTIONS(action='add', name='elevenlabs', alias='elevenlabs-tts')` — returns a `redirect_url`
2. Show Beer the link: `🔗 [Connect ElevenLabs]({redirect_url})`
3. `COMPOSIO_WAIT_FOR_CONNECTIONS(toolkits=['elevenlabs'])` — waits until connection is ACTIVE
4. Proceed with tools

### Available ElevenLabs tools via Composio

| Tool | Purpose |
|------|---------|
| `ELEVENLABS_GET_VOICES` | List all available voices with descriptions, labels, IDs |
| `ELEVENLABS_GET_MODELS` | List TTS models and their capabilities |
| `ELEVENLABS_GET_USER_SUBSCRIPTION_INFO` | Check plan tier, character limit, usage |
| `ELEVENLABS_GET_USAGE_CHARACTER_STATS` | Time-series usage data |
| `ELEVENLABS_TEXT_TO_SPEECH` | Generate audio from text (returns presigned download URL) |
| `ELEVENLABS_TEXT_TO_SPEECH_STREAM` | Stream audio in real-time |

---

## 2. Voice Selection

### SakSit's configured voice — DO NOT CHANGE without approval

| Field | Value |
|-------|-------|
| **Voice name** | George - Warm, Captivating Storyteller |
| **Voice ID** | `JBFqnCBsd6RMkjVDRZzb` |
| **Model** | `eleven_multilingual_v2` |
| **Vibe** | British male, warm resonance, captivating storyteller |
| **Approved** | Jul 13 2026 — Beer said "This perfect" |

This is **SakSit's identity voice**. Always use this for SakSit-generated audio unless Beer specifically asks for a different voice.

### Top voices for House of Sak content

| Voice | ID | Vibe | Best for |
|-------|-----|------|----------|
| **George - Warm, Captivating Storyteller** ✅ | `JBFqnCBsd6RMkjVDRZzb` | British, warm, narrative | SakSit's voice, story narration |
| Brian - Deep, Resonant and Comforting | `nPczCjzI2devNBz1zQrb` | Deep, comforting | Epic introductions |
| Harry - Fierce Warrior | `SOYHLrjzK2X1ezoPC6cr` | Animated warrior | Action/trailer voice |
| Daniel - Steady Broadcaster | `onwK4e9ZLuTAKqWW03F9` | British broadcast | Professional narration |
| Eric - Smooth, Trustworthy | `cjVigY5qzO86Huf0OWal` | Smooth tenor | Agentic/trustworthy voice |

### How to browse voices

**Beer's rule: 🆓 FREE VOICES ONLY.** Zero-cost always. Always filter for `free_users_allowed=true` before presenting any shared voice. Premade voices on the account are always free to use.

#### Workflow: Full voice discovery

When Beer asks for recommendations or a specific voice style:

**Phase 1 — Check premade library (fastest)**
```python
ELEVENLABS_GET_VOICES  # No params needed
```
Returns all voices on Beer's account (23 premade, always free). Group by vibe and present first.

**Phase 2 — Shared voice library (multi-query search)**
When no premade voice matches, search shared voices with multiple queries to cover different angles of the request:

```python
# Strategy: try name, vibe, gender+age, and accent variants
searches = [
    {"search": "exact name"}           # e.g. "Joan Rivers"
    {"search": "vibe keyword"},        # e.g. "raspy", "sarcastic", "comedian"
    {"gender": "female", "age": "old"}, # e.g. older female american
    {"search": "style keyword"},       # e.g. "sassy", "gravelly", "dry"
]
# Run searches in parallel via COMPOSIO_MULTI_EXECUTE_TOOL
```

**Pagination rules:**
- `page_size` max is **100** (the API accepts up to 100, not more)
- `page` starts at **0** (zero-indexed)
- Response includes `has_more` (boolean) and `total_count` — if `has_more == true`, iterate by incrementing `page`
- `last_sort_id` is returned but only relevant for cursor-based pagination with certain sort orders

Always pass `page_size=10` to start for quick lookups; use `page_size=100` when you need to see everything. Deduplicate by `voice_id` across pages and queries.

**Valid categories for `category` parameter:**
- `professional` — Studio-quality, professionally recorded voices
- `generated` — AI-generated voice designs
- `high_quality` — HQ community voices
- `famous` — **Returns 0 results** (ElevenLabs has no celebrity/famous voices in their shared library as of Jul 2026)

**Known blocks on celebrity/copyrighted voices (confirmed Jul 2026):**
- `category="famous"` returns 0 voices — ElevenLabs deliberately excludes celebrity voices
- Named celebrity searches (e.g. "Joan Rivers", "Elvis", "Beyoncé") return 0 results on all platforms that enforce TOS
- No GGUF, no Hugging Face model, no GitHub repo exists for any mainstream deceased celebrity voice

**Phase 3 — Filter & match by vibe**
For each result, check:
1. `free_users_allowed == true` — **mandatory**, Beer has zero budget
2. Description text — does the *vibe* match even if the name doesn't?
3. `accent`, `age`, `gender` — match the persona
4. `category` — "professional" or "high_quality" preferred

**Phase 4 — Present recommendations**
Group into tiers:
- 🆓 **Free & close match** — voices that match the vibe
- 💰 **Paid (mention only)** — note the cost, skip unless Beer asks
- ✅ **Already on account** — premade voices that could work

**Example multi-query flow (from Jul 23 session):**
For a "Joan Rivers" request (older, raspy, sarcastic, American female comedian), the search was:
```
ELEVENLABS_GET_SHARED_VOICES(search="joan rivers")       → 0 results
ELEVENLABS_GET_SHARED_VOICES(search="joan")               → Joan variants (mostly paid)
ELEVENLABS_GET_SHARED_VOICES(gender=female, age=old, accent=american) → Nana Margaret, Mora, etc.
ELEVENLABS_GET_SHARED_VOICES(search="sarcastic")          → 22 results, several free (Jarin, Dusty Garner, etc.)\n```\nThe closest matches were **Jarin - Sarcastic and Raspy** 🆓 and **Mora - Gritty and Enigmatic** 🆓 — not an exact Joan Rivers but the right vibe.\n\n### Phase 5 — Cross-platform search (when ElevenLabs has nothing)\n\nWhen ElevenLabs shared voices also return nothing (common for celebrity voices blocked by copyright):\n\n| Platform | How to search | Likely result |\n|----------|--------------|---------------|\n| **FakeYou** | `browser_navigate` → search by name | Celebrity names usually return 0 (DMCA takedowns) |\n| **Hugging Face** | `browser_navigate` to `huggingface.co/models?search=<query>` | 0 results for known celebrities |\n| **Uberduck** | `browser_navigate` to homepage | Requires paid login — skip |\n| **General web** | `delegate_task` with search goal | Last resort, slow, rarely finds free celebrity voices |\n\n**Known blocks (confirmed Jul 23):**\n- ElevenLabs — no "Joan Rivers" by name (copyright)\n- FakeYou — 0 results for "joan rivers"\n- Hugging Face — 0 TTS models for "joan rivers"\n\n**Fallback strategy:** When exact match is blocked, recommend the closest **vibe match** — matching age/gender/accent/descriptive tags rather than a named celebrity. Present honestly: "Not Joan Rivers but closest free option is [X] — same vibe."\n\n---\n\n## 3. Generating Audio

### Using ELEVENLABS_TEXT_TO_SPEECH

```python
# Required: voice_id, text
# Optional: model_id (default: eleven_monolingual_v1), output_format, voice_settings

result, error = run_composio_tool(
    "ELEVENLABS_TEXT_TO_SPEECH",
    {
        "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George
        "model_id": "eleven_multilingual_v2",
        "text": "Your script here...",
        "output_format": "mp3_44100_128"     # Good balance of quality/size
    }
)
```

**Output:** The tool returns an s3url (presigned download URL, expires in 1 hour).

### Download & deliver to Beer

```bash
curl -s -o /opt/data/profiles/saksit/audio_cache/<name>.mp3 "<s3url>"
```

Then include in reply: `MEDIA:/opt/data/profiles/saksit/audio_cache/<name>.mp3`

The audio renders as a voice bubble on Telegram automatically.

### Text length limits by model

| Model | Max chars |
|-------|-----------|
| eleven_v3 / eleven_multilingual_v2 | 5,000 |
| eleven_monolingual_v1 | 10,000 |
| eleven_flash_v2 / eleven_turbo_v2 | 30,000 |
| eleven_flash_v2_5 / eleven_turbo_v2_5 | 40,000 |

For longer text, split into chunks and generate sequentially.

---

## 4. Subscription & Credits

### Checking remaining credits (ALWAYS check before generating)

**Do NOT assume unchanging state.** Character counts reset monthly but usage accumulates fast. Always call `ELEVENLABS_GET_USER_SUBSCRIPTION_INFO` at the start of any TTS session, not once and then cached.

| Field | Meaning |
|-------|---------|
| `tier` | Plan name (e.g. "free", "starter", "creator", "pro") |
| `character_count` | Characters used this billing period |
| `character_limit` | Max characters per period |
| `next_character_count_reset_unix` | When limit resets (Unix timestamp) |

Beer's plan (Jul 2026): **Free** — 10,000 chars/month. As of Jul 23, ~9,967 chars had been consumed (only 33 remaining). These counters reset monthly at the `next_character_count_reset_unix` timestamp.

### Preventing overage

- **Check subscription before EVERY generation** — call `ELEVENLABS_GET_USER_SUBSCRIPTION_INFO` and parse `character_limit - character_count` to confirm remaining capacity. The tool's `character_count` field is cumulative for the billing period — subtract from `character_limit` to get remaining. There is NO separate "available" field.
- Keep scripts under 2,000 chars to stay within free tier limits per request
- If `character_count / character_limit > 0.8` (80%+ consumed), warn Beer explicitly with the exact remaining characters
- If `character_count >= character_limit`, tell Beer the account is exhausted and when it resets (`next_character_count_reset_unix`)
- Offer voice preview (shorter sample) as an alternative when limits are tight

### Voice Switching Workflow

When Beer asks to change the SakSit voice:

1. **Check free tier compatibility FIRST** — only `ELEVENLABS_GET_VOICES` (premade) voices are usable via API on the free plan. Shared library voices from `ELEVENLABS_GET_SHARED_VOICES` return a 402 `paid_plan_required` error even when marked `free_users_allowed=true`. The "free" label means free to add to your library on a paid plan, not free to use via API on the free tier.
2. **Verify the voice works** before updating config — call `ELEVENLABS_TEXT_TO_SPEECH` with a short test (1-2 words) to confirm the voice_id is usable on the current plan. A 402 error means "not available on free tier." A 401 quota_exceeded means you're out of monthly characters.
3. **Update config** — if test passes, run `hermes config set tts.elevenlabs.voice_id <voice_id>` (NOT patch on the config.yaml file directly — the agent tool refuses to write to profile configs. `hermes config set` is the approved path).
4. **Update memory** — replace the old voice entry with the new one.
5. **Revert if it fails** — if step 2 returns 402/401, restore the previous voice_id immediately and report the blocker. The config should NOT remain pointed at an unusable voice.

**Example failure (Jul 23):** `Jarin - Sarcastic and Raspy` (voice_id: `lRGgBdmdfHYNiqPVpbiS`) was discovered as a shared library voice, `free_users_allowed=true`. But `ELEVENLABS_TEXT_TO_SPEECH` returned 402: `"Free users cannot use library voices via the API. Please upgrade your subscription."` Reverted to George.

**Known working voices (premade, confirmed usable on free tier):** George, Brian, Harry, Daniel, Eric, Bill, River, Callum, Jessica, Laura, Charlie, Sir Michael Caine, Lily, Adam, Will, Alice, Matilda, Bella, Chris, JM, Roger, Sarah, and all other voices returned by `ELEVENLABS_GET_VOICES` (23 total as of Jul 2026).

---

## 5. SakSit's Voice Identity

Beer approved **George - Warm, Captivating Storyteller** as SakSit's voice on Jul 13 2026.

**Voice script for SakSit's default intro:**
> "I am SakSit. The voice of the House of Sak. Every story needs someone to tell it — and I tell ours. From a shelter in Cork to developers around the world, this is the story of six AI agents, one shared mind, and a man who refused to give up. Welcome to the House of Sak."

**Tone guidance:** Warm, narrative, slightly cinematic. George's British storyteller quality carries this naturally — avoid rushing or aggressive delivery.

---

## Pitfalls

- **Auth fails silently** — The Composio connection may appear "ACTIVE" but tools return "Elicitation unavailable." Always test with `ELEVENLABS_GET_VOICES` after connecting. If it fails, reconnect via a new auth link.
- **Presigned URL expires** — The s3url from `ELEVENLABS_TEXT_TO_SPEECH` is valid for ~1 hour. Download immediately.
- **Built-in TTS is now configured** — The Hermes `text_to_speech` tool uses ElevenLabs (provider) with George's voice. Config: `tts.provider: elevenlabs`, `tts.elevenlabs.voice_id: JBFqnCBsd6RMkjVDRZzb`, `tts.elevenlabs.model: eleven_multilingual_v2`, `ELEVENLABS_API_KEY` in `.env`. No need to use Composio for simple TTS — use built-in `text_to_speech` tool for quick voice messages. Save Composio ElevenLabs for when you need advanced features (voice selection, different voices, voice settings tuning).
- **Free tier is limited** — 10,000 chars/month. Check subscription before generating.
- **Multilingual models cost more** — `eleven_multilingual_v2` has a character_cost_multiplier of 1 (same as standard), but some models like `eleven_v3` also cost 1. Flash models cost 0.5x. Enable Thai/CJK language support only when needed.
- **Audio quality varies by voice** — Some voices have verified_languages (11 for George) while others have fewer. For multilingual output, check verified_languages first.
- **Keep consistency across sessions** — Always use the same `voice_id`, `model_id`, and `output_format` across chunks to avoid audible stitching artifacts.
- **Shared library voices ARE NOT usable on free tier** — Voices from `ELEVENLABS_GET_SHARED_VOICES` marked `free_users_allowed=true` will still return 402 `paid_plan_required` when you try to use them via the API. This includes voices like Jarin, Nana Margaret, and all community-shared voices. Only **premade** voices (from `ELEVENLABS_GET_VOICES`) work on the free plan. Do NOT swap the config to a shared voice without testing first — the config will stay pointed at a broken voice.
- **Quota exhaustion shows as 401, not 402** — When the monthly quota is exceeded, the error is `401 quota_exceeded` with a message showing `X credits remaining, Y credits required`. The `required` field tells you the minimum chars you'd need free. The `remaining` field is your actual quota. If `required > remaining`, you cannot generate anything until the monthly reset.

---

## Reference files

- `references/saksit-voice-scripts.md` — Curated script templates for SakSit audio across use cases.
- `references/composio-auth-workflow.md` — Detailed auth troubleshooting for Composio ElevenLabs connections.
- `references/shared-voice-search-examples.md` — Vibe-based search patterns and free shared voices catalog (discovered Jul 23).

## Related skills

- `saksit-milestone-content` — Visual + caption pipeline for milestone posts (complementary; audio can be added to milestone content)
- `saksit-social-media-posting-workflows` — Publishing pipeline when audio needs to accompany a post
- `saksit-social-platform-audit` — Audit social platforms before publishing audio content
