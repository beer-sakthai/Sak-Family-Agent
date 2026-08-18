# OneDrive + Contacts Graph Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four new Microsoft Graph tools to the SakThai agent — `list_onedrive_files`, `read_onedrive_file`, `upload_onedrive_file`, `find_contact` — extending the existing mail/calendar Graph tool set with app-folder-sandboxed OneDrive access and read-only Contacts lookup.

**Architecture:** All four handlers reuse the existing `_graph_access_token()` / `_graph_request()` / `_graph_safe()` helpers in `personas/sakthai/sakthai/agent/tools.py`. OneDrive access is sandboxed via Microsoft Graph's built-in `special/approot` ("app folder") concept — enforced by the `Files.ReadWrite.AppFolder` permission scope itself, not by application-level path checks. `read_onedrive_file` needs a small new raw-bytes GET helper (its response is file content, not JSON); `upload_onedrive_file` needs `_graph_request` extended with a `raw_body` parameter (its request body is raw text, not JSON).

**Tech Stack:** Python 3.14, stdlib `urllib.request`/`urllib.parse` only (no new dependencies, matching the existing Graph tools), `pytest` + `monkeypatch` for tests.

## Global Constraints

- No new third-party dependencies — use `urllib.request`/`urllib.parse` exactly as the existing four Graph tools do.
- Every new tool's error path (config missing, HTTP error, network error) must go through the existing `_graph_safe()` wrapper, exactly like `send_outlook_mail` et al.
- Every new handler validates required string arguments the same way as `_send_outlook_mail`: `if not isinstance(x, str) or not x.strip(): raise ValueError(...)`.
- OneDrive reads/writes MUST use the `/me/drive/special/approot` endpoint family — never a caller-supplied path outside the app folder.
- `mypy --strict` and `ruff check` must both stay clean on `agent/tools.py` after every task (matches this codebase's existing quality bar).
- Full test suite (`tests/test_tools.py`) must pass after every task — never leave it red between tasks.
- Truncation marker text for `read_onedrive_file` is the literal string `"\n... [truncated]"` — must match `read_file`'s existing truncation string exactly (verified at `agent/tools.py:265` in the current file).

---

### Task 1: `list_onedrive_files` + shared constants + `_human_size` helper

**Files:**
- Modify: `personas/sakthai/sakthai/agent/tools.py:33-35` (add two new constants after existing ones)
- Modify: `personas/sakthai/sakthai/agent/tools.py:41` (extend `_GRAPH_SCOPES`)
- Modify: `personas/sakthai/sakthai/agent/tools.py:596-597` (insert `_human_size` + `_list_onedrive_files` before `_run_agent_loop`)
- Modify: `personas/sakthai/sakthai/agent/tools.py:902-903` (register the `list_onedrive_files` Tool, before `run_agent_loop`)
- Test: `tests/test_tools.py` (append after the existing Graph tool test block, before the `_path_under_any_root` section divider at line 855)

**Interfaces:**
- Produces: `_human_size(num_bytes: int) -> str` — used by this task and referenced in the plan's Definition of Done for documentation, not by later tasks' code.
- Produces: `_list_onedrive_files(args: dict[str, Any], store: MemoryStore) -> str` — registered as the `list_onedrive_files` tool.
- Consumes: `_graph_request`, `_graph_safe`, `_coerce_limit` (all pre-existing, unchanged in this task).

- [ ] **Step 1: Write the failing tests**

Open `tests/test_tools.py`. Find this exact block (it is the last content before the `_path_under_any_root` section divider):

```python
def test_create_calendar_event_success(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    api_body = json.dumps(
        {"subject": "Standup", "webLink": "https://outlook.office.com/event/1"}
    ).encode()
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', api_body),
    )
    out = tool_by_name("create_calendar_event").handler(
        {
            "subject": "Standup",
            "start": "2026-08-05T09:00:00",
            "end": "2026-08-05T09:30:00",
            "location": "Zoom",
        },
        store,
    )
    assert "Event created: Standup" in out
    assert "https://outlook.office.com/event/1" in out


# ---------------------------------------------------------------------------
# _path_under_any_root — unit tests for the private sandbox helper
# ---------------------------------------------------------------------------
```

Insert the following new content between `assert "https://outlook.office.com/event/1" in out` and the `# ---...` divider (keep the divider and everything after it unchanged):

```python


# ---------------------------------------------------------------------------
# list_onedrive_files
# ---------------------------------------------------------------------------


def test_human_size_formatting() -> None:
    assert _tools_mod._human_size(512) == "512B"
    assert _tools_mod._human_size(2048) == "2.0KB"
    assert _tools_mod._human_size(3 * 1024 * 1024) == "3.0MB"


def test_list_onedrive_files_success(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    api_body = json.dumps(
        {
            "value": [
                {
                    "name": "notes.txt",
                    "size": 512,
                    "lastModifiedDateTime": "2026-08-01T10:00:00Z",
                }
            ]
        }
    ).encode()
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', api_body),
    )
    out = tool_by_name("list_onedrive_files").handler({}, store)
    assert "notes.txt" in out
    assert "512B" in out


def test_list_onedrive_files_empty(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', b'{"value": []}'),
    )
    out = tool_by_name("list_onedrive_files").handler({}, store)
    assert out == "No files found."
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd personas/sakthai && uv run pytest ../../tests/test_tools.py -k "onedrive_files or human_size" -v` (or, if `uv` is unavailable, `pytest tests/test_tools.py -k "onedrive_files or human_size" -v` from the repo root)

Expected: FAIL — `test_human_size_formatting` fails with `AttributeError: module 'sakthai.agent.tools' has no attribute '_human_size'`; the two `list_onedrive_files` tests fail with `AttributeError: 'NoneType' object has no attribute 'handler'` (because `tool_by_name("list_onedrive_files")` returns `None` — the tool doesn't exist yet).

- [ ] **Step 3: Add the two new constants and extend `_GRAPH_SCOPES`**

In `personas/sakthai/sakthai/agent/tools.py`, find this exact block:

```python
MAX_FILE_READ_CHARS = 20_000  # read_file output cap
MAX_CMD_OUTPUT_CHARS = 20_000  # run_command output cap
_RECALL_LIMIT_MAX = 200  # cap on recall/search limit
```

Replace it with:

```python
MAX_FILE_READ_CHARS = 20_000  # read_file output cap
MAX_CMD_OUTPUT_CHARS = 20_000  # run_command output cap
_RECALL_LIMIT_MAX = 200  # cap on recall/search limit
MAX_ONEDRIVE_READ_CHARS = 50_000  # read_onedrive_file output cap
MAX_ONEDRIVE_UPLOAD_CHARS = 1_000_000  # upload_onedrive_file input cap
```

Then find this exact line:

```python
_GRAPH_SCOPES = "Mail.Send Mail.Read Calendars.ReadWrite offline_access"
```

Replace it with:

```python
_GRAPH_SCOPES = (
    "Mail.Send Mail.Read Calendars.ReadWrite offline_access "
    "Files.ReadWrite.AppFolder Contacts.Read"
)
```

(Both new constants are added now even though `MAX_ONEDRIVE_UPLOAD_CHARS` isn't used until Task 3 — this keeps the constants block in one place instead of two separate edits to the same four lines.)

- [ ] **Step 4: Implement `_human_size` and `_list_onedrive_files`**

Find this exact line:

```python
def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
    """Run a high-level task through the full SakThai agent loop."""
```

Insert the following two functions immediately before it (keep `def _run_agent_loop` and everything after untouched):

```python
def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


def _list_onedrive_files(args: dict[str, Any], store: MemoryStore) -> str:
    limit = _coerce_limit(args.get("limit"), 25)

    def _do() -> str:
        result = _graph_request(
            "GET",
            f"/me/drive/special/approot/children?$top={limit}&"
            "$select=name,size,lastModifiedDateTime",
        )
        files = (result or {}).get("value", [])
        if not files:
            return "No files found."
        lines = ["OneDrive app folder files:"]
        for f in files:
            size = _human_size(int(f.get("size", 0)))
            lines.append(
                f"  {f.get('name', '(unnamed)')}  {size}  "
                f"{f.get('lastModifiedDateTime', '')}"
            )
        return "\n".join(lines)

    return _graph_safe("listing OneDrive files", _do)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
    """Run a high-level task through the full SakThai agent loop."""
```

- [ ] **Step 5: Register the `list_onedrive_files` tool**

Find this exact block:

```python
        handler=_create_calendar_event,
    ),
    Tool(
        name="run_agent_loop",
```

Replace it with:

```python
        handler=_create_calendar_event,
    ),
    Tool(
        name="list_onedrive_files",
        description=(
            "List files in the agent's sandboxed OneDrive app folder. Requires "
            "MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum files to return.",
                    "default": 25,
                },
            },
        },
        handler=_list_onedrive_files,
    ),
    Tool(
        name="run_agent_loop",
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v` (full file — confirm nothing else broke, not just the new tests)

Expected: PASS, all tests including the 3 new ones (`test_human_size_formatting`, `test_list_onedrive_files_success`, `test_list_onedrive_files_empty`).

- [ ] **Step 7: Lint and type-check**

Run: `ruff check personas/sakthai/sakthai/agent/tools.py tests/test_tools.py`
Expected: `All checks passed!`

Run: `mypy personas/sakthai/sakthai/agent/tools.py --strict`
Expected: `Success: no issues found in 1 source file`

- [ ] **Step 8: Commit**

```bash
git add personas/sakthai/sakthai/agent/tools.py tests/test_tools.py
git commit -m "feat: add list_onedrive_files Graph tool"
```

---

### Task 2: `read_onedrive_file`

**Files:**
- Modify: `personas/sakthai/sakthai/agent/tools.py` (insert `_graph_request_raw_get` after `_graph_request`; insert `_read_onedrive_file` after `_list_onedrive_files`)
- Modify: `personas/sakthai/sakthai/agent/tools.py` (register the `read_onedrive_file` Tool, after `list_onedrive_files`)
- Test: `tests/test_tools.py` (append after Task 1's new tests)

**Interfaces:**
- Consumes: `_graph_access_token()` (unchanged), `MAX_ONEDRIVE_READ_CHARS` (added in Task 1).
- Produces: `_graph_request_raw_get(path: str) -> bytes` — a GET-only helper for endpoints whose response body is not JSON. Not used by any other task in this plan, but documented here since a later OneDrive-binary-support pass would reuse it.
- Produces: `_read_onedrive_file(args: dict[str, Any], store: MemoryStore) -> str` — registered as the `read_onedrive_file` tool.

- [ ] **Step 1: Write the failing tests**

In `tests/test_tools.py`, append the following immediately after `test_list_onedrive_files_empty` (the last test added in Task 1):

```python


# ---------------------------------------------------------------------------
# read_onedrive_file
# ---------------------------------------------------------------------------


def test_read_onedrive_file_requires_name(store) -> None:
    with pytest.raises(ValueError):
        tool_by_name("read_onedrive_file").handler({}, store)


def test_read_onedrive_file_success(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', b"hello world"),
    )
    out = tool_by_name("read_onedrive_file").handler({"name": "notes.txt"}, store)
    assert out == "hello world"


def test_read_onedrive_file_truncates(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    big = b"a" * (_tools_mod.MAX_ONEDRIVE_READ_CHARS + 100)
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', big),
    )
    out = tool_by_name("read_onedrive_file").handler({"name": "big.txt"}, store)
    assert out.endswith("\n... [truncated]")
    assert len(out) == _tools_mod.MAX_ONEDRIVE_READ_CHARS + len("\n... [truncated]")


def test_read_onedrive_file_binary_returns_error(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', b"\xff\xfe\x00\x01"),
    )
    out = tool_by_name("read_onedrive_file").handler({"name": "binary.bin"}, store)
    assert "not text-decodable" in out


def test_read_onedrive_file_not_found(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    exc = urllib.error.HTTPError("https://graph.microsoft.com", 404, "Not Found", None, None)
    exc.read = lambda: json.dumps({"error": {"message": "item not found"}}).encode()  # type: ignore[method-assign]

    def _stub(request, timeout=None):
        if "login.microsoftonline.com" in request.full_url:
            return _FakeResponse(b'{"access_token": "fake-access"}')
        raise exc

    monkeypatch.setattr(urllib.request, "urlopen", _stub)
    out = tool_by_name("read_onedrive_file").handler({"name": "missing.txt"}, store)
    assert "Microsoft Graph API Error (404)" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py -k read_onedrive_file -v`

Expected: FAIL — `test_read_onedrive_file_requires_name` fails with `AttributeError: 'NoneType' object has no attribute 'handler'`; the rest fail the same way (tool not registered yet).

- [ ] **Step 3: Implement `_graph_request_raw_get`**

Find this exact block in `personas/sakthai/sakthai/agent/tools.py`:

```python
def _graph_request(method: str, path: str, *, json_body: dict[str, Any] | None = None) -> Any:
    token = _graph_access_token()
    url = f"{_GRAPH_API_BASE}{path}"
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
        raw = response.read()
    return json.loads(raw) if raw else None
```

Insert the following function immediately after it (before `def _graph_safe`):

```python


def _graph_request_raw_get(path: str) -> bytes:
    """GET a Graph endpoint whose response body is not JSON (e.g. file content)."""
    token = _graph_access_token()
    url = f"{_GRAPH_API_BASE}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
        return response.read()
```

- [ ] **Step 4: Implement `_read_onedrive_file`**

Find this exact block (the `_list_onedrive_files` function you added in Task 1, immediately followed by `_run_agent_loop`):

```python
    return _graph_safe("listing OneDrive files", _do)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
```

Replace it with:

```python
    return _graph_safe("listing OneDrive files", _do)


def _read_onedrive_file(args: dict[str, Any], store: MemoryStore) -> str:
    name = args.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("`name` is required and must be a non-empty string.")

    def _do() -> str:
        raw = _graph_request_raw_get(
            f"/me/drive/special/approot:/{urllib.parse.quote(name)}:/content"
        )
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return "Error: file is not text-decodable (binary or unsupported encoding)."
        if len(text) > MAX_ONEDRIVE_READ_CHARS:
            text = text[:MAX_ONEDRIVE_READ_CHARS] + "\n... [truncated]"
        return text

    return _graph_safe("reading OneDrive file", _do)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
```

- [ ] **Step 5: Register the `read_onedrive_file` tool**

Find this exact block (the `list_onedrive_files` Tool entry you added in Task 1):

```python
        handler=_list_onedrive_files,
    ),
    Tool(
        name="run_agent_loop",
```

Replace it with:

```python
        handler=_list_onedrive_files,
    ),
    Tool(
        name="read_onedrive_file",
        description=(
            "Read a text file's content from the agent's sandboxed OneDrive app folder. "
            "Requires MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "File name in the app folder."},
            },
            "required": ["name"],
        },
        handler=_read_onedrive_file,
    ),
    Tool(
        name="run_agent_loop",
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`

Expected: PASS, all tests including the 5 new ones from this task.

- [ ] **Step 7: Lint and type-check**

Run: `ruff check personas/sakthai/sakthai/agent/tools.py tests/test_tools.py`
Expected: `All checks passed!`

Run: `mypy personas/sakthai/sakthai/agent/tools.py --strict`
Expected: `Success: no issues found in 1 source file`

- [ ] **Step 8: Commit**

```bash
git add personas/sakthai/sakthai/agent/tools.py tests/test_tools.py
git commit -m "feat: add read_onedrive_file Graph tool"
```

---

### Task 3: `upload_onedrive_file` (extends `_graph_request` with raw-body support)

**Files:**
- Modify: `personas/sakthai/sakthai/agent/tools.py` (extend `_graph_request` signature; insert `_upload_onedrive_file` after `_read_onedrive_file`)
- Modify: `personas/sakthai/sakthai/agent/tools.py` (register the `upload_onedrive_file` Tool, after `read_onedrive_file`)
- Test: `tests/test_tools.py` (append after Task 2's new tests)

**Interfaces:**
- Consumes: `MAX_ONEDRIVE_UPLOAD_CHARS` (added in Task 1), `_graph_request` (extended in this task — new keyword-only `raw_body: str | None = None` parameter; fully backward compatible, no existing call site changes).
- Produces: `_upload_onedrive_file(args: dict[str, Any], store: MemoryStore) -> str` — registered as the `upload_onedrive_file` tool.

- [ ] **Step 1: Write the failing tests**

In `tests/test_tools.py`, append the following immediately after `test_read_onedrive_file_not_found` (the last test added in Task 2):

```python


# ---------------------------------------------------------------------------
# upload_onedrive_file
# ---------------------------------------------------------------------------


def test_upload_onedrive_file_requires_fields(store) -> None:
    with pytest.raises(ValueError):
        tool_by_name("upload_onedrive_file").handler({"content": "hi"}, store)
    with pytest.raises(ValueError):
        tool_by_name("upload_onedrive_file").handler({"name": "a.txt"}, store)


def test_upload_onedrive_file_success(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    api_body = json.dumps({"name": "notes.txt"}).encode()
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', api_body),
    )
    out = tool_by_name("upload_onedrive_file").handler(
        {"name": "notes.txt", "content": "hello"}, store
    )
    assert out == "File uploaded: notes.txt"


def test_upload_onedrive_file_over_limit_never_calls_urlopen(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")

    def _boom(request, timeout=None):
        raise AssertionError("urlopen should not be called when content exceeds the cap")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    too_big = "a" * (_tools_mod.MAX_ONEDRIVE_UPLOAD_CHARS + 1)
    out = tool_by_name("upload_onedrive_file").handler(
        {"name": "big.txt", "content": too_big}, store
    )
    assert "exceeds" in out
    assert "1,000,000" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py -k upload_onedrive_file -v`

Expected: FAIL — `test_upload_onedrive_file_requires_fields` fails with `AttributeError: 'NoneType' object has no attribute 'handler'` (tool not registered yet); the other two fail the same way.

- [ ] **Step 3: Extend `_graph_request` with `raw_body` support**

Find this exact block (this is `_graph_request` as it exists after Task 1 — unchanged by Tasks 1-2):

```python
def _graph_request(method: str, path: str, *, json_body: dict[str, Any] | None = None) -> Any:
    token = _graph_access_token()
    url = f"{_GRAPH_API_BASE}{path}"
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:  # nosec B310
        raw = response.read()
    return json.loads(raw) if raw else None
```

Replace it with:

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

(This is additive and backward-compatible: every existing caller passes `json_body=` by keyword, never positionally, so the new `raw_body` parameter does not affect them. Do not modify any of the four existing Graph tool handlers in this step.)

- [ ] **Step 4: Implement `_upload_onedrive_file`**

Find this exact block (the `_read_onedrive_file` function you added in Task 2, immediately followed by `_run_agent_loop`):

```python
    return _graph_safe("reading OneDrive file", _do)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
```

Replace it with:

```python
    return _graph_safe("reading OneDrive file", _do)


def _upload_onedrive_file(args: dict[str, Any], store: MemoryStore) -> str:
    name = args.get("name")
    content = args.get("content")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("`name` is required and must be a non-empty string.")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("`content` is required and must be a non-empty string.")
    if len(content) > MAX_ONEDRIVE_UPLOAD_CHARS:
        return (
            f"Error: content exceeds {MAX_ONEDRIVE_UPLOAD_CHARS:,} "
            "character limit for upload."
        )

    def _do() -> str:
        _graph_request(
            "PUT",
            f"/me/drive/special/approot:/{urllib.parse.quote(name)}:/content",
            raw_body=content,
        )
        return f"File uploaded: {name}"

    return _graph_safe("uploading OneDrive file", _do)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
```

- [ ] **Step 5: Register the `upload_onedrive_file` tool**

Find this exact block (the `read_onedrive_file` Tool entry you added in Task 2):

```python
        handler=_read_onedrive_file,
    ),
    Tool(
        name="run_agent_loop",
```

Replace it with:

```python
        handler=_read_onedrive_file,
    ),
    Tool(
        name="upload_onedrive_file",
        description=(
            "Write or overwrite a text file in the agent's sandboxed OneDrive app folder. "
            "Requires MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "File name in the app folder."},
                "content": {"type": "string", "description": "Text content to write."},
            },
            "required": ["name", "content"],
        },
        handler=_upload_onedrive_file,
    ),
    Tool(
        name="run_agent_loop",
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`

Expected: PASS, all tests including the 3 new ones from this task.

- [ ] **Step 7: Lint and type-check**

Run: `ruff check personas/sakthai/sakthai/agent/tools.py tests/test_tools.py`
Expected: `All checks passed!`

Run: `mypy personas/sakthai/sakthai/agent/tools.py --strict`
Expected: `Success: no issues found in 1 source file`

- [ ] **Step 8: Commit**

```bash
git add personas/sakthai/sakthai/agent/tools.py tests/test_tools.py
git commit -m "feat: add upload_onedrive_file Graph tool"
```

---

### Task 4: `find_contact`

**Files:**
- Modify: `personas/sakthai/sakthai/agent/tools.py` (insert `_find_contact` after `_upload_onedrive_file`)
- Modify: `personas/sakthai/sakthai/agent/tools.py` (register the `find_contact` Tool, after `upload_onedrive_file`)
- Test: `tests/test_tools.py` (append after Task 3's new tests)

**Interfaces:**
- Consumes: `_graph_request`, `_graph_safe`, `_coerce_limit` (all pre-existing/already extended, unchanged by this task).
- Produces: `_find_contact(args: dict[str, Any], store: MemoryStore) -> str` — registered as the `find_contact` tool. Nothing later in this plan depends on it.

- [ ] **Step 1: Write the failing tests**

In `tests/test_tools.py`, append the following immediately after `test_upload_onedrive_file_over_limit_never_calls_urlopen` (the last test added in Task 3):

```python


# ---------------------------------------------------------------------------
# find_contact
# ---------------------------------------------------------------------------


def test_find_contact_requires_query(store) -> None:
    with pytest.raises(ValueError):
        tool_by_name("find_contact").handler({}, store)


def test_find_contact_success(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    api_body = json.dumps(
        {
            "value": [
                {
                    "displayName": "Ada Lovelace",
                    "emailAddresses": [{"address": "ada@example.com"}],
                    "businessPhones": ["+1-555-0100"],
                }
            ]
        }
    ).encode()
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', api_body),
    )
    out = tool_by_name("find_contact").handler({"query": "Ada"}, store)
    assert "Ada Lovelace" in out
    assert "ada@example.com" in out
    assert "+1-555-0100" in out


def test_find_contact_empty(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        _graph_urlopen_stub(b'{"access_token": "fake-access"}', b'{"value": []}'),
    )
    out = tool_by_name("find_contact").handler({"query": "Nobody"}, store)
    assert out == "No contacts found matching 'Nobody'."


def test_find_contact_escapes_single_quote_in_query(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path, store
) -> None:
    """A raw single quote in the query must not break the OData $filter string."""
    monkeypatch.setenv("MS_GRAPH_CLIENT_ID", "client-id")
    monkeypatch.setenv("MS_GRAPH_REFRESH_TOKEN", "seed-refresh-token")
    captured: dict[str, str] = {}

    def _stub(request, timeout=None):
        if "login.microsoftonline.com" in request.full_url:
            return _FakeResponse(b'{"access_token": "fake-access"}')
        captured["url"] = request.full_url
        return _FakeResponse(b'{"value": []}')

    monkeypatch.setattr(urllib.request, "urlopen", _stub)
    tool_by_name("find_contact").handler({"query": "O'Brien"}, store)
    assert "O''Brien" in captured["url"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py -k find_contact -v`

Expected: FAIL — `test_find_contact_requires_query` fails with `AttributeError: 'NoneType' object has no attribute 'handler'` (tool not registered yet); the other three fail the same way.

- [ ] **Step 3: Implement `_find_contact`**

Find this exact block (the `_upload_onedrive_file` function you added in Task 3, immediately followed by `_run_agent_loop`):

```python
    return _graph_safe("uploading OneDrive file", _do)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
```

Replace it with:

```python
    return _graph_safe("uploading OneDrive file", _do)


def _find_contact(args: dict[str, Any], store: MemoryStore) -> str:
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("`query` is required and must be a non-empty string.")
    limit = _coerce_limit(args.get("limit"), 10)

    def _do() -> str:
        escaped = query.replace("'", "''")  # OData string literal escaping
        result = _graph_request(
            "GET",
            f"/me/contacts?$filter=startswith(displayName,'{escaped}')&$top={limit}&"
            "$select=displayName,emailAddresses,businessPhones,mobilePhone",
        )
        contacts = (result or {}).get("value", [])
        if not contacts:
            return f"No contacts found matching '{query}'."
        lines = ["Matching contacts:"]
        for c in contacts:
            emails = c.get("emailAddresses") or []
            email = emails[0].get("address", "") if emails else ""
            phones = c.get("businessPhones") or []
            phone = phones[0] if phones else c.get("mobilePhone", "")
            parts = [p for p in (email, phone) if p]
            suffix = f" ({', '.join(parts)})" if parts else ""
            lines.append(f"  {c.get('displayName', '(no name)')}{suffix}")
        return "\n".join(lines)

    return _graph_safe("searching contacts", _do)


def _run_agent_loop(args: dict[str, Any], store: MemoryStore) -> str:
```

- [ ] **Step 4: Register the `find_contact` tool**

Find this exact block (the `upload_onedrive_file` Tool entry you added in Task 3):

```python
        handler=_upload_onedrive_file,
    ),
    Tool(
        name="run_agent_loop",
```

Replace it with:

```python
        handler=_upload_onedrive_file,
    ),
    Tool(
        name="find_contact",
        description=(
            "Search Outlook/Microsoft 365 contacts by name, returning email and phone. "
            "Requires MS_GRAPH_CLIENT_ID and MS_GRAPH_REFRESH_TOKEN in the environment."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Name or partial name to search for.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum contacts to return.",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
        handler=_find_contact,
    ),
    Tool(
        name="run_agent_loop",
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`

Expected: PASS, all tests including the 4 new ones from this task. Total suite should now be 96 (baseline) + 3 (Task 1) + 5 (Task 2) + 3 (Task 3) + 4 (Task 4) = 111 tests.

- [ ] **Step 6: Lint and type-check**

Run: `ruff check personas/sakthai/sakthai/agent/tools.py tests/test_tools.py`
Expected: `All checks passed!`

Run: `mypy personas/sakthai/sakthai/agent/tools.py --strict`
Expected: `Success: no issues found in 1 source file`

- [ ] **Step 7: Commit**

```bash
git add personas/sakthai/sakthai/agent/tools.py tests/test_tools.py
git commit -m "feat: add find_contact Graph tool"
```

---

### Task 5: Documentation updates

**Files:**
- Modify: `README.md:90` (tool count + table)
- Modify: `CLAUDE.md:208-212` (tool count + tool list)
- Modify: `.env.example:26-30` (note the two new scopes)

**Interfaces:**
- Consumes: nothing code-level — this task only touches documentation. No later task depends on it.

- [ ] **Step 1: Update `README.md`**

Find this exact block:

```markdown
### 📦 Built-in Tools (14)

| Tool | Purpose | Safety Gate |
|------|---------|-------------|
| `learn` | Store facts in memory | None (always on) |
| `recall` / `search` | Query memory by keyword | None (read-only) |
| `forget` | Delete facts | Confirmation required |
| `read_file` | Read local files | Allowlisted roots + sensitive file blocks |
| `run_command` | Execute shell commands | **Off by default** — requires `SAKTHAI_SHELL_ALLOW=<allowlist>` |
| `ingest_document` | Parse CSV/Markdown/text into facts | None (parse-only) |
| `capture_lead` | Quick fact capture (Telegram) | User ID allowlist |
| `send_telegram_message` | Send Telegram messages | Bot token required, 10s timeout |
| `send_outlook_mail` | Send email via Microsoft Graph | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `read_outlook_mail` | List recent Outlook inbox messages | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `list_calendar_events` | List upcoming Outlook calendar events | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `create_calendar_event` | Create an Outlook calendar event | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `run_agent_loop` | Spawn nested agent (MCP only) | Recursion guard via `SAKTHAI_AGENT_ACTIVE` |
```

Replace it with:

```markdown
### 📦 Built-in Tools (18)

| Tool | Purpose | Safety Gate |
|------|---------|-------------|
| `learn` | Store facts in memory | None (always on) |
| `recall` / `search` | Query memory by keyword | None (read-only) |
| `forget` | Delete facts | Confirmation required |
| `read_file` | Read local files | Allowlisted roots + sensitive file blocks |
| `run_command` | Execute shell commands | **Off by default** — requires `SAKTHAI_SHELL_ALLOW=<allowlist>` |
| `ingest_document` | Parse CSV/Markdown/text into facts | None (parse-only) |
| `capture_lead` | Quick fact capture (Telegram) | User ID allowlist |
| `send_telegram_message` | Send Telegram messages | Bot token required, 10s timeout |
| `send_outlook_mail` | Send email via Microsoft Graph | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `read_outlook_mail` | List recent Outlook inbox messages | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `list_calendar_events` | List upcoming Outlook calendar events | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `create_calendar_event` | Create an Outlook calendar event | Requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `list_onedrive_files` | List files in the agent's OneDrive app folder | Graph-enforced app-folder sandbox (`Files.ReadWrite.AppFolder`) |
| `read_onedrive_file` | Read a text file from the agent's OneDrive app folder | Graph-enforced app-folder sandbox; 50,000 char read cap |
| `upload_onedrive_file` | Write/overwrite a text file in the agent's OneDrive app folder | Graph-enforced app-folder sandbox; 1,000,000 char upload cap |
| `find_contact` | Search Outlook contacts by name | Read-only, requires `MS_GRAPH_CLIENT_ID` + refresh token |
| `run_agent_loop` | Spawn nested agent (MCP only) | Recursion guard via `SAKTHAI_AGENT_ACTIVE` |
```

- [ ] **Step 2: Update `CLAUDE.md`**

Find this exact block:

```markdown
- **`agent/tools.py`** — defines `BUILTIN_TOOLS` (14 tools, one schema + handler
  each): `learn`, `ingest_document`, `capture_lead`, `recall`, `search`, `forget`,
  `read_file`, `run_command`, `send_telegram_message`, `send_outlook_mail`,
  `read_outlook_mail`, `list_calendar_events`, `create_calendar_event`,
  `run_agent_loop`. Add a tool here and it appears in both the agent loop and
  the MCP server automatically. Note: `run_agent_loop` is filtered out of the
  in-loop tool set (it's MCP-only) to avoid recursion. The four Graph tools
  share `_graph_access_token()` / `_graph_request()` / `_graph_safe()` helpers:
  a refresh token (env `MS_GRAPH_REFRESH_TOKEN` or cached at
  `~/.sakthai/graph_token.json`, seeded via `scripts/graph_device_login.py`) is
  exchanged for a short-lived access token on every call.
```

Replace it with:

```markdown
- **`agent/tools.py`** — defines `BUILTIN_TOOLS` (18 tools, one schema + handler
  each): `learn`, `ingest_document`, `capture_lead`, `recall`, `search`, `forget`,
  `read_file`, `run_command`, `send_telegram_message`, `send_outlook_mail`,
  `read_outlook_mail`, `list_calendar_events`, `create_calendar_event`,
  `list_onedrive_files`, `read_onedrive_file`, `upload_onedrive_file`,
  `find_contact`, `run_agent_loop`. Add a tool here and it appears in both the
  agent loop and the MCP server automatically. Note: `run_agent_loop` is
  filtered out of the in-loop tool set (it's MCP-only) to avoid recursion. The
  eight Graph tools share `_graph_access_token()` / `_graph_request()` /
  `_graph_safe()` helpers: a refresh token (env `MS_GRAPH_REFRESH_TOKEN` or
  cached at `~/.sakthai/graph_token.json`, seeded via
  `scripts/graph_device_login.py`) is exchanged for a short-lived access token
  on every call. OneDrive access is sandboxed to Graph's built-in
  `special/approot` folder — the isolation is enforced by the
  `Files.ReadWrite.AppFolder` permission scope itself, not by application code.
```

- [ ] **Step 3: Update `.env.example`**

Find this exact block:

```
# Optional: enable the send_outlook_mail / read_outlook_mail /
# list_calendar_events / create_calendar_event tools (Microsoft Graph).
# Run `python scripts/graph_device_login.py` once to sign in; it fills in
# MS_GRAPH_REFRESH_TOKEN (also cached at ~/.sakthai/graph_token.json).
# MS_GRAPH_CLIENT_ID=
# MS_GRAPH_TENANT_ID=consumers
# MS_GRAPH_REFRESH_TOKEN=
```

Replace it with:

```
# Optional: enable the send_outlook_mail / read_outlook_mail /
# list_calendar_events / create_calendar_event / list_onedrive_files /
# read_onedrive_file / upload_onedrive_file / find_contact tools
# (Microsoft Graph). Run `python scripts/graph_device_login.py` once to sign
# in; it fills in MS_GRAPH_REFRESH_TOKEN (also cached at
# ~/.sakthai/graph_token.json). The OneDrive/Contacts tools need two extra
# Graph delegated permissions on the app registration: Files.ReadWrite.AppFolder
# and Contacts.Read (in addition to Mail.Send, Mail.Read,
# Calendars.ReadWrite, offline_access).
# MS_GRAPH_CLIENT_ID=
# MS_GRAPH_TENANT_ID=consumers
# MS_GRAPH_REFRESH_TOKEN=
```

- [ ] **Step 4: Verify the full suite is still green**

Run: `pytest tests/test_tools.py -q`
Expected: `111 passed` (documentation-only changes don't affect test count, but this confirms nothing was accidentally broken while editing).

- [ ] **Step 5: Commit**

```bash
git add README.md CLAUDE.md .env.example
git commit -m "docs: document the four new OneDrive/Contacts Graph tools"
```

---

## Definition of Done (whole plan)

- `BUILTIN_TOOLS` has 18 entries; `list_onedrive_files`, `read_onedrive_file`, `upload_onedrive_file`, `find_contact` all present and correctly wired.
- `_GRAPH_SCOPES` includes `Files.ReadWrite.AppFolder` and `Contacts.Read`.
- `_graph_request` accepts `raw_body`; all four pre-existing Graph tools still pass unmodified.
- 15 new tests added to `tests/test_tools.py` (3 + 5 + 3 + 4); full suite (111 tests) passes.
- `ruff check` and `mypy --strict` clean on `agent/tools.py` and `tests/test_tools.py`.
- `README.md`, `CLAUDE.md`, `.env.example` all reflect the 18-tool count and the two new scopes.
- Five commits on `feat/onedrive-contacts-graph-tools`, one per task, each independently green.
