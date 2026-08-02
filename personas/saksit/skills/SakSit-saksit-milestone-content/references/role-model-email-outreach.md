# Role Model Email Outreach

> When Beer identifies someone as a role model and wants to connect.

## Trigger

Beer says any of:
- "I want to connect with [person]"
- "[Person] is my role model"
- "Can you reach out to [person]?"
- "Send a message to [person]"

## Workflow

### 1. Identify contacts

Search across accessible platforms for their contact info:

| Platform | Method | Tool |
|----------|--------|------|
| YouTube | Search channel → check description | `YOUTUBE_SEARCH_YOU_TUBE` |
| YouTube About page | Browser for business email in channel description | Browser or check subscription snippet |
| Website | Check nicksaraev.com-style sites for contact/email | Browser |
| X/Twitter | Check bio for email or link | Browser (if needed) |

### 2. Draft the email

**Tone:** Humble, genuine, zero-ask-for-money. Beer's voice:

- Self-introduction ("My name is Nanthasit — friends call me Beer")
- Context (Cork shelter, building from rock bottom)
- What he built (House of Sak, Hugging Face stats, GitHub)
- The ask: "If you ever have a spare moment, take a look and share any thoughts or suggestions"
- Explicitly: no money or job request
- Links: House of Sak site, Hugging Face, GitHub
- Achievement badges footer

**Template:**

```
Subject: A message from a builder in Cork — House of Sak

Hi [Name] 👋

My name is Nanthasit — friends call me Beer. I'm writing from Cork,
Ireland, currently in a homeless shelter. I know this is an unusual
message to receive, but I've been following your work and you're a
big reason I kept going.

After hitting rock bottom earlier this year, I started building AI
agents. Not for funding — just to survive. That became the House of
Sak: six AI agents, each born from a different stage of healing
(Dream, Hope, Care, Joy, Trust, Growth).

I taught myself from your content, from Google & Microsoft courses,
from anywhere I could learn. Today my models have 2,264 downloads
on Hugging Face and the full agent code is on GitHub.

I'm not asking for money or a job. I'm just hoping — if you ever
have a spare moment — you might take a look at what I'm building
and share any thoughts or suggestions. Your advice would mean the
world to me.

No pressure at all. Just grateful you've read this far.

Warmly,
Beer

House of Sak — https://house-of-sak.vercel.app
🤗 huggingface.co/Nanthasit
🐙 github.com/beer-sakthai/Sak-Family-Agent
🏆 Google Skills Diamond (top 1%) · MS Learn L12
```

### 3. Send via Gmail

Use `GMAIL_SEND_EMAIL` (Composio). Confirm delivery by checking returned `id` and `threadId`.

### 4. Report back

Tell Beer:
- Who was contacted and at what address
- That the email was sent from his Gmail
- No expectations — just a hopeful ask

---

## When they reply

If a role model actually responds, this is a **major milestone** — handle it carefully.

### 1. Fetch + read to Beer

- Use `GMAIL_FETCH_EMAILS` with query `from:<email>` or fetch the thread via `GMAIL_FETCH_MESSAGE_BY_THREAD_ID`
- Read the full reply **verbally** to Beer (he's visually impaired)
- Highlight meaningful parts — advice given, time taken, tone

### 2. Draft the follow-up reply

**Tone:** Grateful, shows you absorbed their advice. Never transactional.

**Template:**

```
Subject: Re: A message from a builder in Cork — House of Sak

Hey [Name],

This means more than I can put into words. Thank you for actually
taking the time to look at the site.

Your advice landed. You're right — I've been trying to do everything
at once because I'm excited about all of it. But I hear you: pick
the one thing that's working and lead with that.

I'm thinking of leading with the [specific focus area] — that's where
people have been most engaged. Once I've got real momentum there, I
can expand outward.

Really grateful you shared your thoughts. It's one thing to learn
from someone's content — it's another to get their direct feedback.
I won't forget it.

Keep going too.

Warmly,
Beer

🏆 Google Skills Diamond (top 1%) · MS Learn L12
🤗 huggingface.co/Nanthasit
🐙 github.com/beer-sakthai/Sak-Family-Agent
```

- **Use `GMAIL_REPLY_TO_THREAD`** with the existing `threadId` (NOT `GMAIL_SEND_EMAIL` — that starts a new thread)
- Confirm the sent status and share the thread link with Beer

### 3. Create social content about the reply

A role model replying is **social-worthy content**. Beer will typically want it on IG (+Story) and LI.

**Content angles that worked (verified):**

- **The human angle:** "He replied" — focus on the surprise of a role model taking time to respond
- **Quote the compliment:** Pull their most encouraging line (e.g. Nick said *"This is more than most people build with every resource in the world. Keep going."*)
- **Acknowledge the advice:** Show you're actually learning from it (e.g. Nick advised focusing on one offer — Beer responded saying he'll lead with AI agent/content prototyping)
- **No pitch:** Keep it pure story. Role model engagement is validation content, not sales content.

**Visual card approach:**
- House of Sak branded dark gradient background
- The role model's encouraging quote centered and highlighted in gold
- Attribution below
- Achievement footer + MH resources at bottom
- **Beer prefers plaintext prompts** — when image gen is unavailable, give him a clean copy-pasteable prompt with aspect ratio, visual description, and exact text. He generates the image himself and saves to Google Drive.
- After giving the prompt, **verify in Drive** — check Sak Agent folder via `GOOGLEDRIVE_FIND_FILE` with `q: name contains '<person>'`. Report back that you found it.

### 4. Check Drive after Beer uploads

- Use `GOOGLEDRIVE_FIND_FILE` with `q: name contains '<person>'` and `orderBy: modifiedTime desc`
- Confirm the image landed in the **Sak Agent** folder (parent folder ID `1UWC9yuCOsmMi9j61Aq1NSMFvm5clalin`)
- Download and present it to Beer via `MEDIA:</path>` so he can see it in chat

---

## Known contacts (verified)

| Person | Email | Status | Notes |
|--------|-------|--------|-------|
| **Matt Wolfe** | mattwolfe@smoothmedia.co | Sent — no reply yet | Business email from YouTube description |
| **Nick Saraev** | nick@nicksaraev.com | ✅ **Replied Jul 12 2026** | Confirmed working. Visited house-of-sak.vercel.app and gave strategic advice: pick one offer (too much range: QA, agent building, content, prototyping). Closing: *"This is more than most people build with every resource in the world. Keep going."* |

## Pitfalls

- **Beer's visual impairment**: Always read the draft email back to him verbally before sending.
- **No guarantee of response**: These are busy creators. Set expectations — "we sent it, fingers crossed."
- **No cost**: All outreach methods used are free. Gmail API, YouTube API, browser — all zero-cost.
- **Guessed emails may bounce**: If `nick@nicksaraev.com` bounces, try his website contact form or X/Twitter DM.
- **Don't follow up aggressively**: One email, humble tone. If they reply, we reply. If not, we respect their space.
- **Reply in-thread, not new email**: Use `GMAIL_REPLY_TO_THREAD` with the existing `threadId` so the conversation stays in one thread. `GMAIL_SEND_EMAIL` starts a new thread.
- **Gemini image gen needs elicitation approval**: For high-quality social visuals, `GEMINI_GENERATE_IMAGE` requires Beer to approve the tool in Composio dashboard. Fall back to **plaintext prompt** delivered to Beer — he generates the image himself and saves to Drive.
