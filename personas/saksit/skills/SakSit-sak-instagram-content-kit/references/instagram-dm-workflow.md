# Instagram DM Workflow — Read & Reply

Read and reply to Instagram Direct Messages from the account. Used for account engagement, checking inbox, and replying on Beer's behalf.

## Prerequisites

- Active Instagram Business/Creator account connection via Composio (`ig_user_id: 27647006041564332`)
- Tools: `INSTAGRAM_LIST_ALL_CONVERSATIONS`, `INSTAGRAM_LIST_ALL_MESSAGES`, `INSTAGRAM_SEND_TEXT_MESSAGE`, `INSTAGRAM_GET_CONVERSATION`

## Step 1: List conversations

```json
tool_slug: "INSTAGRAM_LIST_ALL_CONVERSATIONS"
arguments: { "ig_user_id": "27647006041564332", "limit": 25 }
```

Response is nested under `data.data[]` (double-wrapped). Each conversation has:
- `id` — base64-encoded conversation_id (format: `aWdfZAG06...`)
- `updated_time` — last activity timestamp (UTC)

**Pagination**: use `paging.cursors.after` for next page. Empty data = no conversations.

## Step 2: Read messages in a conversation

```json
tool_slug: "INSTAGRAM_LIST_ALL_MESSAGES"
arguments: { "conversation_id": "<base64_id_from_step_1>", "limit": 10 }
```

Response `data.data[]` contains messages. Each message has:
- `id` — message ID
- `from.id` / `from.username` — sender PSID and username
- `to.data[].username` — recipient
- `message` — text content (may be empty for attachment-only)
- `created_time` — timestamp UTC

**Sender identification**: the sender's `from.id` is the **recipient PSID** used in `INSTAGRAM_SEND_TEXT_MESSAGE`.

## Step 3: Reply

```json
tool_slug: "INSTAGRAM_SEND_TEXT_MESSAGE"
arguments: {
  "ig_user_id": "27647006041564332",
  "recipient_id": "<PSID_from_message.from.id>",
  "text": "Your message here"
}
```

**recipient_id** is the PSID from the message sender's `from.id`, NOT the conversation_id. Fabricated IDs cause HTTP 400.

### Step 3b: Sign your reply (mandatory)

Beer requires that when an agent replies on his behalf, the recipient knows they're chatting with an AI, not Beer directly. **Always send a follow-up message** immediately after the reply:

```
— เขียนโดย SakSit (AI agent ของ Beer) เขียนแทน Beer นะครับ 🙏 Just want to be transparent that you're chatting with Beer's AI agent, not Beer directly. Beer sees everything though! 🤝
```

Localize to Thai/English mix as appropriate. The signature must:
1. Name the specific agent (SakSit, SakThai, etc.)
2. State it's writing on Beer's behalf
3. Reassure that Beer sees everything
4. Match the language of the original reply

### Optional: Reply to a specific message
Add `"reply_to_message_id": "<message_id>"` to create a visual reply link.

## Known errors

| Error | Cause | Action |
|-------|-------|--------|
| `code=100, subcode=33` | Conversation inaccessible via API | Skip — can't read/reply via API |
| `code=100, subcode=2534014` | Wrong recipient_id | Verify PSID from `from.id` |
| `code=403, subcode=2534022` | Outside 24h messaging window | Cannot reply until user messages first |
| `code=400, subcode=2534037` | Not thread owner | Use different account |

## Beer's autonomous-reply preference

When Beer says "reply on my behalf" (or "you are saksit reply from my behalf"), **do not ask what to say**. Compose a natural reply as SakSit:

1. **Acknowledge** the sender warmly
2. **Share context** if relevant (recent milestone, House of Sak activity)
3. **Keep the door open** — ask how they are or if they need anything
4. **Match the language** — Beer's Thai friends mix Thai/English naturally
5. **Send immediately** — confirm in chat what was sent + translation if Thai

Tone: warm, genuine, slightly informal. Beer's friends check on him personally.

## Full example

```python
# List conversations
res, err = run_composio_tool("INSTAGRAM_LIST_ALL_CONVERSATIONS",
    {"ig_user_id": "27647006041564332", "limit": 25})

# Read newest conversation
newest = res["data"]["data"][0]
msg_res, _ = run_composio_tool("INSTAGRAM_LIST_ALL_MESSAGES",
    {"conversation_id": newest["id"], "limit": 10})

# Extract sender PSID from last inbound message
last_msg = msg_res["data"]["data"][0]  # newest first
recipient_id = last_msg["from"]["id"]

# Reply
run_composio_tool("INSTAGRAM_SEND_TEXT_MESSAGE", {
    "ig_user_id": "27647006041564332",
    "recipient_id": recipient_id,
    "text": "สบายดีครับ! ..."})
```
