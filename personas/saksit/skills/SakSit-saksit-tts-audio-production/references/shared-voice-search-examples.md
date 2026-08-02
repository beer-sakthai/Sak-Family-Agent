# Shared Voice Search Examples — ElevenLabs

> Quick reference for voice discovery, vibe-based searches, celebrity voice blocking, and pagination. Updated Jul 23, 2026.

## Search Parameter Cheat Sheet

| Parameter | Valid Values |
|-----------|-------------|
| `gender` | male, female, neutral |
| `age` | young, middle_aged, old |
| `accent` | american, british, australian, irish, standard, spanish, french, etc. |
| `search` | Any keyword — name, vibe, use case |
| `use_cases` | audiobook, narration, gaming, advertisement, conversational, social_media, narrative_story |
| `category` | professional, generated, high_quality, **famous** (returns 0 — no celebrity voices) |

## Pagination Rules

| Field | Notes |
|-------|-------|
| `page` | Starts at **0** (zero-indexed) |
| `page_size` | Max **100** per page |
| `has_more` | Boolean — if true, call again with `page + 1` |
| `last_sort_id` | Only relevant for cursor-based sort orders |
| `total_count` | Total matching voices across all pages |

When `has_more == true`, iterate by incrementing `page` until `has_more == false`. Deduplicate results by `voice_id` across pages and across parallel queries.

## Celebrity Voice Search — Expected Results

**Confirmed Jul 2026:** ElevenLabs returns **0 results** for any named celebrity search. The `famous` category is valid but always empty. This is by design (ElevenLabs TOS prohibits unauthorized celebrity impersonation).

When a user asks for a celebrity voice:
1. Search the exact name first (e.g. "Joan Rivers") — 0 results is the expected outcome
2. Do NOT search for alternative spellings or nicknames thinking you'll find it — it's blocked, not missed
3. Skip directly to **vibe-matching** by age/gender/accent/descriptive tags
4. Be upfront: "No [celebrity] voice available on any free TTS platform — closest free option is [X]"

### Cross-platform checks for celebrity voices

When ElevenLabs returns nothing (which it always will for celebrities):

| Platform | How to check | Result pattern |
|----------|-------------|----------------|
| **FakeYou** | `browser_navigate("https://fakeyou.com/search/weights?query=<name>")` | 0 results for known celebrities — DMCA takedowns have cleared the library |
| **Hugging Face models** | `curl "https://huggingface.co/api/models?search=<name>"` or browser to `/models?search=<name>` | Empty `[]` for celebrity names |
| **Hugging Face datasets** | `curl "https://huggingface.co/api/datasets?search=<name>"` | Empty `[]` for celebrity names |
| **GitHub repos** | `curl "https://api.github.com/search/repositories?q=<name>+voice+tts"` | `total_count: 0` for celebrity names |
| **Jammable** | URL pattern `jammable.com/ai-voices?query=<name>` | Usually returns 404 or no results |

## Vibe-Based Search Patterns

### Sarcastic / Comedic / Brassy (like Joan Rivers)

**Direct name search:** `search="joan rivers"` → **0 results** (copyright blocked)

**Vibe matches discovered Jul 23 (free tier):**
```
search="sarcastic"                     → 22 results (Jarin, Dusty Garner, Caty, etc.)
search="comedian"                       → 4 results (French Physical Comedian 🆓)
gender=female, age=old, search="american" → 10+ old female voices
search="raspy"                          → limited results
```

### Free old female American voices (discovered)
| Voice | Description |
|-------|-------------|
| **Nana Margaret - Little Old Lady** 🆓 | Authentic, warm, elderly female |
| **Mora - Gritty and Enigmatic** 🆓 | Weathered, textured, distinctive raspy edge |
| **Maria Moody - Grandmotherly Storykeeper** 🆓 | Octogenarian, wise |
| **Carol - Relatable, Real, Likeable Grandma** 🆓 | Smart, versatile grandma |
| **Empress - Smoky, Breathy, and Neutral** 🆓 | Strong, confident, 60-yo Black woman |

### Free sarcastic female voices (discovered)
| Voice | Vibe |
|-------|------|
| **Jarin - Sarcastic and Raspy** 🆓 | Raspy with sarcastic undertone — best Joan Rivers analog |
| **Dusty Garner - Sarcastic Southern Mom** 🆓 | Southern firecracker, sarcastic |
| **Caty - Droll, Wry and Dry** 🆓 | "Whatever" deadpan, sarcastic |
| **Ivanna - Sassy, Condescending and Clear** 🆓 | Entitled, high-maintenance, sarcastic |
| **Xena Alexander** 🆓 | Southern Woman, Sarcastic |

### "Jones" variants (discovered)
| Voice | Cost |
|-------|------|
| Jones - Children's audiobook narrator | 🆓 FREE |
| Axel Jones - Relaxed & Caring | 🆓 FREE |
| Axel Jones - The Storyteller | 🆓 FREE |
| Mitch Jones | 🆓 FREE |

### Deep / Authoritative male
Geared toward the premade voices already on Beer's account:
- George - Warm, Captivating Storyteller ✅ (current SakSit voice)
- Brian - Deep, Resonant and Comforting
- Daniel - Steady Broadcaster
- Eric - Smooth, Trustworthy
- Bill - Wise, Mature, Balanced

## Premade Voices on Account (23 total)
Always check `ELEVENLABS_GET_VOICES` first before searching shared — premade are always free and immediately usable. Key ones: George, Brian, Harry, Daniel, Eric, Bill, River, Callum, Jessica, Laura, Charlie, Sir Michael Caine.

## Critical: Free Tier vs Shared Voices

**Discovered Jul 23, 2026:** The `free_users_allowed` field on shared library voices is misleading. It means "free to add to your voice library" — NOT "free to use via API." Any shared library voice used via the ElevenLabs API on the free plan returns:

```json
402 paid_plan_required: "Free users cannot use library voices via the API."
```

**Only premade voices** (returned by `ELEVENLABS_GET_VOICES`) are usable on the free plan. This includes 23 voices as of Jul 2026 — all the standard ElevenLabs premade voices.

**What works on free tier via API:**
- All voices from `ELEVENLABS_GET_VOICES` ✅
- `text_to_speech` built-in tool ✅ (routes through ElevenLabs with configured voice)

**What does NOT work on free tier via API:**
- ANY voice from `ELEVENLABS_GET_SHARED_VOICES` ❌ (all return 402)
- Voice cloning / `ELEVENLABS_ADD_VOICE` ❌ (locked on free tier)

## Session Log — Jul 23 Voice Shopping

### Request 1: "Joan Rivers" voice
**ElevenLabs premade:** ❌ Not found
**ElevenLabs shared:** ❌ 0 results ("joan rivers" exact search)
**Vibe search (sarcastic + old + female):** ✅ Found Jarin, Mora, Nana Margaret, etc. (all shared — blocked by free tier)
**FakeYou:** ❌ 0 results
**Hugging Face:** ❌ 0 models
**Verdict:** Blocked by estate copyright on every platform. Closest free premade alternative on account: Jessica - Playful, Bright, Warm (female) or Callum - Husky Trickster (husky male energy).

### Request 2: "Troye Sivan" voice
**ElevenLabs shared:** ❌ 0 results (exact), "troye" partial search found "Troy" variants — unrelated
**Closest premade on account:** Callum - Husky Trickster, Liam - Energetic Social Media Creator

### Request 3: "Tate McRae" voice
**ElevenLabs shared:** ❌ 0 results (exact), "tate" search found unrelated voices (Tate Dalton, Tyrese Tate)
**Closest premade on account:** Jessica - Playful, Bright, Warm

### Request 4: "Jarin - Sarcastic and Raspy" (was going to switch)
**Discovered via:** `search="sarcastic"` → Jarin - Sarcastic and Raspy 🆓 (voice_id: lRGgBdmdfHYNiqPVpbiS)
**Test result:** ❌ 402 `paid_plan_required: Free users cannot use library voices via the API`
**Action:** Config briefly set to Jarin, reverted to George after failure
**Lesson:** Always test a shared voice via `TEXT_TO_SPEECH` BEFORE updating config. The config change itself is easy (`hermes config set tts.elevenlabs.voice_id <id>`) but reverting after a failed test requires another `hermes config set` call.

### Current voice: George - Warm, Captivating Storyteller (voice_id: JBFqnCBsd6RMkjVDRZzb)
