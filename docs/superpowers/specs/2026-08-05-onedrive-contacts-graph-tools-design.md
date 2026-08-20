# OneDrive + Contacts Graph Tools — Design

**Status:** Approved (2026-08-05, verbal approval in brainstorming session)
**Date:** 2026-08-05
**Owner:** Claude Code (with Beer's scoping decisions during brainstorming)

---

## Context

`agent/tools.py` already ships four Microsoft Graph tools (`send_outlook_mail`,
`read_outlook_mail`, `list_calendar_events`, `create_calendar_event`), added
in a prior session. They share three helpers — `_graph_access_token()`,
`_graph_request()`, `_graph_safe()` — that handle refresh-token exchange
(cached at `~/.sakthai/graph_token.json`, mode 0600), raw HTTP calls to
`https://graph.microsoft.com/v1.0`, and uniform error formatting.

This design extends that same plumbing with two more Graph surfaces:
OneDrive (read + write, sandboxed) and Contacts (lookup only). A third
surface discussed in brainstorming — Microsoft Teams (chats + channels) —
was explicitly deferred to its own follow-up design; it needs three
additional permission scopes and roughly as many new tools as this entire
spec, so bundling it here would make this batch disproportionately large
compared to the mail/calendar batch it's meant to mirror.

## Decisions (from brainstorming)

1. **Scope for this spec:** OneDrive + Contacts only. Teams is a separate,
   later design.
2. **OneDrive purpose:** both read (pull existing documents in as context)
   and write (save agent-generated output back).
3. **OneDrive sandboxing:** the agent may only read and write inside a
   single fixed app-managed folder — never anywhere else in the user's
   OneDrive.
4. **Contacts:** lookup/search only (no write).

## Goal

Give the SakThai agent loop four new tools, in the exact shape and quality
bar of the existing Graph tools: same helper reuse, same test coverage
pattern, same doc/README/`.env.example` upkeep, same `mypy --strict` /
`ruff` cleanliness.

## Architecture

No new plumbing. All four handlers call the existing
`_graph_access_token()` / `_graph_request()` / `_graph_safe()` trio
unchanged. `_GRAPH_SCOPES` in `agent/tools.py` gains two scopes:

```python
_GRAPH_SCOPES = (
    "Mail.Send Mail.Read Calendars.ReadWrite offline_access "
    "Files.ReadWrite.AppFolder Contacts.Read"
)
```

**Key architectural choice — sandboxing via Graph's `special/approot`,
not a manually-managed path.** Microsoft Graph provides a built-in
"app folder" concept for exactly this situation: `/me/drive/special/approot`
resolves to a folder Graph creates and manages on first use, hidden from
the user's normal OneDrive browsing view under a system "Apps" area. The
`Files.ReadWrite.AppFolder` delegated permission scopes the app's access to
*only* that folder — this is enforced by Graph itself, not by
application-level path-allowlist code (contrast with the local `read_file`
tool, which enforces its sandbox in Python). This is a strictly narrower
grant than full `Files.ReadWrite`, consistent with the "safety gate"
column every other tool in the README carries.

Because reads and writes both go through `special/approot`, there's no way
for the agent to address a path outside the app folder even if a bug crept
into the tool code — the API surface itself doesn't expose one.

## Components (precise)

### 1. `list_onedrive_files`

- **Endpoint:** `GET /me/drive/special/approot/children`
- **Input schema:** no required params. Optional `limit` (int, default 25,
  reuse existing `_coerce_limit` helper, capped at `_RECALL_LIMIT_MAX`=200).
- **Output:** one line per file — `name`, `size` (human-readable via a
  small `_human_size(n: int) -> str` helper, new — B/KB/MB thresholds),
  `lastModifiedDateTime`. Empty folder → `"No files found."`.
- **Handler:** `_list_onedrive_files(args, store) -> str`, wrapped in
  `_graph_safe("listing OneDrive files", _do)`.

### 2. `read_onedrive_file`

- **Endpoint:** `GET /me/drive/special/approot:/{name}:/content`
  (`name` URL-quoted via `urllib.parse.quote`).
- **Input schema:** `name` (string, required).
- **Behavior:**
  - Attempt UTF-8 decode of the response body.
  - On success: truncate at `MAX_ONEDRIVE_READ_CHARS = 50_000` chars (new
    constant, distinct from local `read_file`'s 20k — cloud documents
    pulled in as context benefit from more room), with a `"\n... [truncated]"`
    suffix — verified to match `read_file`'s exact existing truncation
    string (`agent/tools.py:271`).
  - On `UnicodeDecodeError`: return
    `"Error: file is not text-decodable (binary or unsupported encoding)."`
    — no crash, no partial/garbled output.
  - 404 from Graph (file not found) surfaces through the existing
    `_graph_safe` HTTPError branch as
    `"Microsoft Graph API Error (404): ..."` — no special-casing needed.
- **Handler:** `_read_onedrive_file(args, store) -> str`. `name` validated
  non-empty before the `_graph_safe` call (`ValueError`, same pattern as
  `_send_outlook_mail`'s field validation — raised, not caught, so it
  surfaces as a tool-input error rather than a formatted string).

### 3. `upload_onedrive_file`

- **Endpoint:** `PUT /me/drive/special/approot:/{name}:/content`
  (simple upload — Graph overwrites an existing file at that path by
  default; no conflict-behavior parameter needed for this size class).
- **Input schema:** `name` (string, required), `content` (string, required
  — text content only, no binary/base64 support in this pass).
- **Limits:** reject `content` over
  `MAX_ONEDRIVE_UPLOAD_CHARS = 1_000_000` (~1MB) chars before making the
  request, with a clear error
  (`"Error: content exceeds 1,000,000 character limit for upload."`).
  Graph's simple-upload endpoint has a hard ceiling around 4MB; capping at
  1MB keeps well clear of it without needing the chunked large-file upload
  session API, which is out of scope here.
- **Request body:** raw UTF-8-encoded content bytes, `Content-Type:
  text/plain` (not JSON — this is the one Graph call in the file that
  doesn't send a JSON body, so `_graph_request` needs a way to pass raw
  bytes + a content-type override rather than always JSON-encoding
  `json_body`). See "Data flow" below for the resulting signature change.
  Graph's response to a successful PUT is the uploaded DriveItem's JSON
  metadata, so the existing `json.loads(raw) if raw else None` response
  handling in `_graph_request` still works unchanged for this call.
- **Handler:** `_upload_onedrive_file(args, store) -> str`, returns
  `f"File uploaded: {name}"` on success (parity with
  `_create_calendar_event`'s `"Event created: {subject}"` return shape).

### 4. `find_contact`

- **Endpoint:** `GET /me/contacts?$search="displayName:{query}"` — falls
  back to `$filter=startswith(displayName,'{query}')` if `$search` proves
  unreliable in manual testing (Graph's contacts `$search` support is
  newer/less consistent than mail search; the task brief should note both
  and let the implementer confirm against a live tenant, or default to
  `$filter` if there's any doubt, since it's the safer/older-supported
  choice).
- **Input schema:** `query` (string, required — name or partial name),
  optional `limit` (int, default 10, reuse `_coerce_limit`).
- **Output:** one line per match — `displayName`, first
  `emailAddresses[].address`, first `businessPhones[]`/`mobilePhone` if
  present. No matches → `"No contacts found matching '{query}'."`.
- **Handler:** `_find_contact(args, store) -> str`, wrapped in
  `_graph_safe("searching contacts", _do)`.

### Registration

All four `Tool(...)` entries append to `BUILTIN_TOOLS` immediately after
the existing `create_calendar_event` entry and before `run_agent_loop`,
matching the existing ordering convention (Graph tools grouped together,
`run_agent_loop` last).

## Data flow: `_graph_request` gains a raw-body mode

The existing signature:

```python
def _graph_request(method: str, path: str, *, json_body: dict[str, Any] | None = None) -> Any:
```

`upload_onedrive_file` needs to PUT raw text, not JSON. Extend with an
optional `raw_body` parameter that takes precedence over `json_body` when
both would otherwise apply (only one is ever passed by any caller):

```python
def _graph_request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    raw_body: str | None = None,
) -> Any:
    token = _graph_access_token()
    url = f"{_GRAPH_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    if raw_body is not None:
        data = raw_body.encode("utf-8")
        headers["Content-Type"] = "text/plain"
    elif json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        data = None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
        raw = response.read()
    return json.loads(raw) if raw else None
```

Note the `json.loads(raw) if raw else None` fallback breaks for
`read_onedrive_file`, whose response body is arbitrary file content, not
JSON — that call cannot go through `_graph_request` unchanged (this is the
only one of the four new tools this applies to; `upload_onedrive_file`'s
*response* is normal DriveItem JSON, only its *request* body is raw — see
Components §3). Two options, implementer picks based on what's cleaner in
context:

- (a) give `read_onedrive_file` its own small direct
  `urllib.request.urlopen` call (same shape as `_graph_request` but
  skipping the `json.loads`), or
- (b) add a `raw_response: bool = False` flag to `_graph_request` that
  returns the decoded string body directly instead of attempting
  `json.loads`.

Either is acceptable; (b) keeps one call site pattern but adds a second
boolean flag to an already-growing signature. Flag this as an open
implementation-time judgment call, not a blocking question — pick (a) if
it reads more clearly once written; the task reviewer will check the
result stays consistent with `_graph_safe`'s error-handling contract
either way (both variants raise the same `HTTPError`/`URLError` types).

## Error handling

Unchanged: `_graph_safe` catches `RuntimeError` (config/auth), `HTTPError`
(API errors, with the existing `error.message` JSON-body extraction),
`URLError` (network), and a catch-all `Exception`. All four new handlers
route their Graph call through it exactly like the existing four tools.

`UnicodeDecodeError` in `read_onedrive_file` is the one new error shape —
it's not an `Exception` subtype `_graph_safe` needs special handling for;
catch it explicitly *inside* the handler's inner function (before it would
otherwise be caught by `_graph_safe`'s generic `Exception` branch) so the
message is the specific, user-legible one above rather than generic
"Unexpected Error reading OneDrive file: 'utf-8' codec can't decode...".

## Testing strategy

Mirror `tests/test_tools.py`'s existing Graph-tool test block exactly,
reusing `_graph_urlopen_stub` and `_FakeResponse` (both already generic to
any Graph call — no changes needed there). Per tool:

- `list_onedrive_files`: success (2+ files), empty (`"No files found."`)
- `read_onedrive_file`: success + truncation-at-cap, missing-name
  validation error, `UnicodeDecodeError` path (stub a `_FakeResponse` whose
  `.read()` returns non-UTF-8 bytes), HTTPError (404-style not-found)
- `upload_onedrive_file`: success, missing-name/content validation errors,
  over-cap content rejected pre-request (assert `urlopen` was never called
  — use a stub that raises `AssertionError` if invoked, to prove the size
  check short-circuits before any network call)
- `find_contact`: success (1+ match), empty (`"No contacts found..."`)
- Config-missing path: one shared test is enough (already covered by the
  existing `test_graph_missing_config_returns_error`, since all four new
  tools reuse `_graph_access_token()` unchanged) — no need to repeat it
  per new tool

Total: ~14-16 new tests, comparable in count to the ~15 added for the
mail/calendar batch.

## Out of scope (deferred)

- Microsoft Teams (chats + channels) — separate design, per brainstorming
  decision.
- OneDrive folders/subfolders inside the app folder (flat file list only
  for this pass).
- Binary file upload/download (text only).
- Chunked large-file upload session API (files over ~1MB).
- Contact create/update/delete (lookup only).
- `$search` vs `$filter` reliability is an implementer-time judgment call
  (see Components §4), not deferred, but flagged as needing a live check
  rather than being fully pinned down here.

## Risks

- **`special/approot` first-use creation:** if the app folder doesn't
  exist yet, does `GET .../approot/children` 404, or does Graph
  lazily create it? This needs a live-tenant check during implementation
  (task brief should call this out); if it 404s on first use,
  `list_onedrive_files` needs a friendly `"App folder is empty (not yet
  created)."` message on a 404 rather than surfacing a raw API error.
- **Upload Content-Type mismatch:** some Graph SDKs use
  `application/octet-stream` for simple uploads regardless of actual file
  type; using `text/plain` here is deliberate (this pass is text-only) but
  worth a one-line comment in the code so a future OneDrive-binary-support
  pass doesn't have to rediscover why.

## Open questions

None blocking — the `$search`/`$filter` and `raw_body` design choices
above are resolved at implementation time with reviewer verification, not
before.

## Definition of done

- Four tools registered in `BUILTIN_TOOLS`, `_GRAPH_SCOPES` updated.
- `_graph_request` extended with raw-body support (or `read_onedrive_file`
  uses its own request call — either satisfies this item).
- `MAX_ONEDRIVE_READ_CHARS` and `MAX_ONEDRIVE_UPLOAD_CHARS` constants
  added near the existing `MAX_FILE_READ_CHARS`/`MAX_CMD_OUTPUT_CHARS`.
- ~14-16 new tests in `tests/test_tools.py`, full suite passing.
- `ruff check` and `mypy --strict` clean on `agent/tools.py`.
- `README.md` tool table and count (14 → 18), `CLAUDE.md` tool list, and
  `.env.example` updated to note the two new scopes.
- Az CLI permission-add instructions (given to the user previously for
  Mail/Calendar) get a follow-up snippet for `Files.ReadWrite.AppFolder`
  and `Contacts.Read`.

## Approval

Approved verbally by Beer during the 2026-08-05 brainstorming session
(scope: OneDrive read+write via app folder, Contacts lookup; Teams
deferred). No further sign-off gate before moving to
`superpowers:writing-plans`.
