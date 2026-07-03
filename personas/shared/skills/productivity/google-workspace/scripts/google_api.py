#!/usr/bin/env python3
"""Google Workspace API CLI for Hermes Agent.

Uses the Google Workspace CLI (`gws`) when available, but preserves the
existing Hermes-facing JSON contract and falls back to the Python client
libraries if `gws` is not installed.

Usage:
  python google_api.py gmail search "is:unread" [--max 10]
  python google_api.py gmail get MESSAGE_ID
  python google_api.py gmail send --to user@example.com --subject "Hi" --body "Hello"
  python google_api.py gmail reply MESSAGE_ID --body "Thanks"
  python google_api.py calendar list [--from DATE] [--to DATE] [--calendar primary]
  python google_api.py calendar create --summary "Meeting" --start DATETIME --end DATETIME
  python google_api.py drive search "budget report" [--max 10]
  python google_api.py contacts list [--max 20]
  python google_api.py sheets get SHEET_ID RANGE
  python google_api.py sheets update SHEET_ID RANGE --values '[[...]]'
  python google_api.py sheets append SHEET_ID RANGE --values '[[...]]'
  python google_api.py docs get DOC_ID
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from pathlib import Path

# Ensure sibling modules (_hermes_home) are importable when run standalone.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from _hermes_home import get_hermes_home

HERMES_HOME = get_hermes_home()
TOKEN_PATH = HERMES_HOME / "google_token.json"
CLIENT_SECRET_PATH = HERMES_HOME / "google_client_secret.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]


def _normalize_authorized_user_payload(payload: dict) -> dict:
    normalized = dict(payload)
    if not normalized.get("type"):
        normalized["type"] = "authorized_user"
    return normalized


def _ensure_authenticated():
    if not TOKEN_PATH.exists():
        print("Not authenticated. Run the setup script first:", file=sys.stderr)
        print(f"  python {Path(__file__).parent / 'setup.py'}", file=sys.stderr)
        sys.exit(1)


def _stored_token_scopes() -> list[str]:
    try:
        data = json.loads(TOKEN_PATH.read_text())
    except Exception:
        return list(SCOPES)
    scopes = data.get("scopes")
    if isinstance(scopes, list) and scopes:
        return scopes
    return list(SCOPES)


def _gws_binary() -> str | None:
    override = os.getenv("HERMES_GWS_BIN")
    if override:
        return override
    return shutil.which("gws")


def _gws_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = str(TOKEN_PATH)
    return env


def _run_gws(parts: list[str], *, params: dict | None = None, body: dict | None = None):
    binary = _gws_binary()
    if not binary:
        raise RuntimeError("gws not installed")

    _ensure_authenticated()

    cmd = [binary, *parts]
    if params is not None:
        cmd.extend(["--params", json.dumps(params)])
    if body is not None:
        cmd.extend(["--json", json.dumps(body)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=_gws_env(),
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "Unknown gws error"
        print(err, file=sys.stderr)
        sys.exit(result.returncode or 1)

    stdout = result.stdout.strip()
    if not stdout:
        return {}

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        print("ERROR: Unexpected non-JSON output from gws:", file=sys.stderr)
        print(stdout, file=sys.stderr)
        sys.exit(1)


def _headers_dict(msg: dict) -> dict[str, str]:
    return {
        h["name"].lower(): h["value"]
        for h in msg.get("payload", {}).get("headers", [])
        if h.get("name")
    }


def _extract_message_body(msg: dict) -> str:
    body = ""
    payload = msg.get("payload", {})
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                break
        if not body:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    break
    return body


def _extract_doc_text(doc: dict) -> str:
    text_parts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph", {})
        for pe in paragraph.get("elements", []):
            text_run = pe.get("textRun", {})
            if text_run.get("content"):
                text_parts.append(text_run["content"])
    return "".join(text_parts)


def _datetime_with_timezone(value: str) -> str:
    if not value:
        return value
    if "T" not in value:
        return value
    if value.endswith("Z"):
        return value
    tail = value[10:]
    if "+" in tail or "-" in tail:
        return value
    return value + "Z"


def get_credentials():
    """Load and refresh credentials from token file."""
    _ensure_authenticated()

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), _stored_token_scopes())
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(
            json.dumps(
                _normalize_authorized_user_payload(json.loads(creds.to_json())),
                indent=2,
            )
        )
    if not creds.valid:
        print("Token is invalid. Re-run setup.", file=sys.stderr)
        sys.exit(1)
    return creds


def build_service(api, version):
    from googleapiclient.discovery import build

    return build(api, version, credentials=get_credentials())


class ApiService:
    """A wrapper that decides whether to use gws or the Python client."""

    def __init__(self, api: str, version: str):
        self.api = api
        self.version = version
        self._service = None

    @property
    def service(self):
        """Lazy-load the Python client service."""
        if self._service is None:
            self._service = build_service(self.api, self.version)
        return self._service

    def execute(self, gws_parts: list[str], py_func, gws_params: dict | None = None, gws_body: dict | None = None):
        """Execute the API call using either gws or the Python client."""
        if _gws_binary():
            return _run_gws(
                [self.api, *gws_parts],
                params=gws_params,
                body=gws_body,
            )
        return py_func().execute()

# =========================================================================
# Gmail
# =========================================================================

def _fetch_message_details(msg_meta: dict, gmail_service: ApiService) -> dict:
    """Worker function to fetch details for a single message."""
    get_params = {
        "userId": "me",
        "id": msg_meta["id"],
        "format": "metadata",
        "metadataHeaders": ["From", "To", "Subject", "Date"],
    }
    msg = gmail_service.execute(
        gws_parts=["users", "messages", "get"],
        gws_params=get_params,
        py_func=lambda: gmail_service.service.users().messages().get(**get_params),
    )
    headers = _headers_dict(msg)
    return {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": msg.get("snippet", ""),
        "labels": msg.get("labelIds", []),
    }

def gmail_search(args):
    gmail_service = ApiService("gmail", "v1")
    list_params = {"userId": "me", "q": args.query, "maxResults": args.max}

    results = gmail_service.execute(
        gws_parts=["users", "messages", "list"],
        gws_params=list_params,
        py_func=lambda: gmail_service.service.users().messages().list(**list_params),
    )

    messages = results.get("messages", [])
    if not messages:
        print("No messages found.")
        return

    from concurrent.futures import ThreadPoolExecutor
    from functools import partial

    # Use a ThreadPoolExecutor to fetch message details in parallel.
    # max_workers=10 is a reasonable default to avoid overwhelming the API.
    with ThreadPoolExecutor(max_workers=10) as executor:
        worker_func = partial(_fetch_message_details, gmail_service=gmail_service)
        output = list(executor.map(worker_func, messages))

    print(json.dumps(output, indent=2, ensure_ascii=False))

def gmail_get(args):
    gmail_service = ApiService("gmail", "v1")
    msg = gmail_service.execute(
        gws_parts=["users", "messages", "get"],
        gws_params={"userId": "me", "id": args.message_id, "format": "full"},
        py_func=lambda: gmail_service.service.users().messages().get(
            userId="me", id=args.message_id, format="full"
        ),
    )
    headers = _headers_dict(msg)
    result = {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "labels": msg.get("labelIds", []),
        "body": _extract_message_body(msg),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def gmail_send(args):
    message = MIMEText(args.body, "html" if args.html else "plain")
    message["To"] = args.to
    message["Subject"] = args.subject
    if args.cc:
        message["Cc"] = args.cc
    if args.from_header:
        message["From"] = args.from_header

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw}
    if args.thread_id:
        body["threadId"] = args.thread_id

    gmail_service = ApiService("gmail", "v1")
    result = gmail_service.execute(
        gws_parts=["users", "messages", "send"],
        gws_params={"userId": "me"},
        gws_body=body,
        py_func=lambda: gmail_service.service.users().messages().send(userId="me", body=body),
    )
    print(json.dumps({"status": "sent", "id": result["id"], "threadId": result.get("threadId", "")}, indent=2))


def gmail_reply(args):
    # The gws and python-native logic are slightly different here, so a full
    # abstraction is more complex. We can still simplify.
    service = build_service("gmail", "v1")
    original = service.users().messages().get(
        userId="me", id=args.message_id, format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID"],
    ).execute()
    headers = _headers_dict(original)

    subject = headers.get("subject", "")
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"

    message = MIMEText(args.body)
    message["To"] = headers.get("from", "")
    message["Subject"] = subject
    if args.from_header:
        message["From"] = args.from_header
    if headers.get("message-id"):
        message["In-Reply-To"] = headers["message-id"]
        message["References"] = headers["message-id"]

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw, "threadId": original["threadId"]}

    gmail_service = ApiService("gmail", "v1")
    result = gmail_service.execute(
        gws_parts=["users", "messages", "send"],
        gws_params={"userId": "me"},
        gws_body=body,
        py_func=lambda: gmail_service.service.users().messages().send(userId="me", body=body),
    )
    print(json.dumps({"status": "sent", "id": result["id"], "threadId": result.get("threadId", "")}, indent=2))


def gmail_labels(args):
    gmail_service = ApiService("gmail", "v1")
    results = gmail_service.execute(
        gws_parts=["users", "labels", "list"],
        gws_params={"userId": "me"},
        py_func=lambda: gmail_service.service.users().labels().list(userId="me"),
    )
    labels = [{"id": l["id"], "name": l["name"], "type": l.get("type", "")} for l in results.get("labels", [])]
    print(json.dumps(labels, indent=2))


def gmail_modify(args):
    body = {}
    if args.add_labels:
        body["addLabelIds"] = args.add_labels.split(",")
    if args.remove_labels:
        body["removeLabelIds"] = args.remove_labels.split(",")

    gmail_service = ApiService("gmail", "v1")
    result = gmail_service.execute(
        gws_parts=["users", "messages", "modify"],
        gws_params={"userId": "me", "id": args.message_id},
        gws_body=body,
        py_func=lambda: gmail_service.service.users().messages().modify(userId="me", id=args.message_id, body=body),
    )
    print(json.dumps({"id": result["id"], "labels": result.get("labelIds", [])}, indent=2))


# =========================================================================
# Calendar
# =========================================================================


def calendar_list(args):
    now = datetime.now(timezone.utc)
    time_min = _datetime_with_timezone(args.start or now.isoformat())
    time_max = _datetime_with_timezone(args.end or (now + timedelta(days=7)).isoformat())

    params = {
        "calendarId": args.calendar,
        "timeMin": time_min,
        "timeMax": time_max,
        "maxResults": args.max,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    cal_service = ApiService("calendar", "v3")
    results = cal_service.execute(
        gws_parts=["events", "list"],
        gws_params=params,
        py_func=lambda: cal_service.service.events().list(**params),
    )

    events = []
    for e in results.get("items", []):
        events.append({
            "id": e["id"],
            "summary": e.get("summary", "(no title)"),
            "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
            "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date", "")),
            "location": e.get("location", ""),
            "description": e.get("description", ""),
            "status": e.get("status", ""),
            "htmlLink": e.get("htmlLink", ""),
        })
    print(json.dumps(events, indent=2, ensure_ascii=False))


def calendar_create(args):
    event = {
        "summary": args.summary,
        "start": {"dateTime": args.start},
        "end": {"dateTime": args.end},
    }
    if args.location:
        event["location"] = args.location
    if args.description:
        event["description"] = args.description
    if args.attendees:
        event["attendees"] = [{"email": e.strip()} for e in args.attendees.split(",") if e.strip()]

    cal_service = ApiService("calendar", "v3")
    result = cal_service.execute(
        gws_parts=["events", "insert"],
        gws_params={"calendarId": args.calendar},
        gws_body=event,
        py_func=lambda: cal_service.service.events().insert(calendarId=args.calendar, body=event),
    )
    print(json.dumps({
        "status": "created",
        "id": result["id"],
        "summary": result.get("summary", ""),
        "htmlLink": result.get("htmlLink", ""),
    }, indent=2))


def calendar_delete(args):
    cal_service = ApiService("calendar", "v3")
    cal_service.execute(
        gws_parts=["events", "delete"],
        gws_params={"calendarId": args.calendar, "eventId": args.event_id},
        py_func=lambda: cal_service.service.events().delete(calendarId=args.calendar, eventId=args.event_id),
    )
    print(json.dumps({"status": "deleted", "eventId": args.event_id}))


# =========================================================================
# Drive
# =========================================================================


def drive_search(args):
    query = args.query if args.raw_query else f"fullText contains '{args.query}'"
    params = {
        "q": query,
        "pageSize": args.max,
        "fields": "files(id, name, mimeType, modifiedTime, webViewLink)",
    }

    drive_service = ApiService("drive", "v3")
    results = drive_service.execute(
        gws_parts=["files", "list"],
        gws_params=params,
        py_func=lambda: drive_service.service.files().list(**params),
    )
    print(json.dumps(results.get("files", []), indent=2, ensure_ascii=False))


def drive_get(args):
    """Get metadata for a single Drive file by ID."""
    fields = "id, name, mimeType, modifiedTime, size, webViewLink, parents, owners(emailAddress)"
    drive_service = ApiService("drive", "v3")
    result = drive_service.execute(
        gws_parts=["files", "get"],
        gws_params={"fileId": args.file_id, "fields": fields},
        py_func=lambda: drive_service.service.files().get(fileId=args.file_id, fields=fields),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def drive_upload(args):
    """Upload a local file to Drive. Falls through to Python client even when gws
    is installed, because gws doesn't do multipart uploads."""
    import mimetypes
    from googleapiclient.http import MediaFileUpload

    local_path = Path(args.path).expanduser()
    if not local_path.exists():
        print(f"ERROR: file not found: {local_path}", file=sys.stderr)
        sys.exit(1)

    mime = args.mime_type or mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    metadata = {"name": args.name or local_path.name}
    if args.parent:
        metadata["parents"] = [args.parent]

    service = build_service("drive", "v3")
    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)
    result = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, mimeType, webViewLink",
    ).execute()
    print(json.dumps({
        "status": "uploaded",
        "id": result["id"],
        "name": result.get("name", ""),
        "mimeType": result.get("mimeType", ""),
        "webViewLink": result.get("webViewLink", ""),
    }, indent=2, ensure_ascii=False))


def drive_download(args):
    """Download a Drive file to a local path. Google-native files (Docs/Sheets/Slides)
    must be exported; binary files are downloaded as-is."""
    import io
    from googleapiclient.http import MediaIoBaseDownload

    service = build_service("drive", "v3")

    # Look up the file to decide download vs export.
    meta = service.files().get(fileId=args.file_id, fields="id, name, mimeType").execute()
    mime = meta.get("mimeType", "")
    name = meta.get("name", args.file_id)

    # Map Google-native MIME types to a sensible export default.
    native_export_map = {
        "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
        "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
        "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
        "application/vnd.google-apps.drawing": ("image/png", ".png"),
    }

    out_path = Path(args.output).expanduser() if args.output else Path.cwd() / name

    if mime in native_export_map:
        export_mime = args.export_mime or native_export_map[mime][0]
        default_ext = native_export_map[mime][1]
        if not args.output and not out_path.suffix:
            out_path = out_path.with_suffix(default_ext)
        request = service.files().export_media(fileId=args.file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=args.file_id)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fh = io.FileIO(str(out_path), "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()

    print(json.dumps({
        "status": "downloaded",
        "id": args.file_id,
        "name": name,
        "path": str(out_path),
        "mimeType": mime,
    }, indent=2, ensure_ascii=False))


def drive_create_folder(args):
    body = {
        "name": args.name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if args.parent:
        body["parents"] = [args.parent]

    drive_service = ApiService("drive", "v3")
    result = drive_service.execute(
        gws_parts=["files", "create"],
        gws_params={"fields": "id, name, webViewLink"},
        gws_body=body,
        py_func=lambda: drive_service.service.files().create(body=body, fields="id, name, webViewLink"),
    )
    print(json.dumps({
        "status": "created",
        "id": result["id"],
        "name": result.get("name", ""),
        "webViewLink": result.get("webViewLink", ""),
    }, indent=2, ensure_ascii=False))


def drive_share(args):
    permission = {
        "type": args.type,
        "role": args.role,
    }
    if args.type in {"user", "group"}:
        if not args.email:
            print("ERROR: --email is required for type=user or type=group", file=sys.stderr)
            sys.exit(1)
        permission["emailAddress"] = args.email
    elif args.type == "domain":
        if not args.domain:
            print("ERROR: --domain is required for type=domain", file=sys.stderr)
            sys.exit(1)
        permission["domain"] = args.domain

    drive_service = ApiService("drive", "v3")
    result = drive_service.execute(
        gws_parts=["permissions", "create"],
        gws_params={"fileId": args.file_id, "sendNotificationEmail": args.notify},
        gws_body=permission,
        py_func=lambda: drive_service.service.permissions().create(
            fileId=args.file_id,
            body=permission,
            sendNotificationEmail=args.notify,
            fields="id",
        ),
    )
    print(json.dumps({
        "status": "shared",
        "permissionId": result.get("id", ""),
        "fileId": args.file_id,
        "role": permission["role"],
        "type": permission["type"],
    }, indent=2, ensure_ascii=False))


def drive_delete(args):
    """Trash or permanently delete a Drive file. Defaults to trash (reversible)."""
    drive_service = ApiService("drive", "v3")
    if args.permanent:
        drive_service.execute(
            gws_parts=["files", "delete"],
            gws_params={"fileId": args.file_id},
            py_func=lambda: drive_service.service.files().delete(fileId=args.file_id),
        )
        print(json.dumps({"status": "deleted", "fileId": args.file_id, "permanent": True}))
        return

    # Trash (reversible). Use files.update with trashed=True.
    body = {"trashed": True}
    drive_service.execute(
        gws_parts=["files", "update"],
        gws_params={"fileId": args.file_id},
        gws_body=body,
        py_func=lambda: drive_service.service.files().update(fileId=args.file_id, body=body),
    )
    print(json.dumps({"status": "trashed", "fileId": args.file_id, "permanent": False}))


# =========================================================================
# Contacts
# =========================================================================


def contacts_list(args):
    params = {
        "resourceName": "people/me",
        "pageSize": args.max,
        "personFields": "names,emailAddresses,phoneNumbers",
    }
    people_service = ApiService("people", "v1")
    results = people_service.execute(
        gws_parts=["people", "connections", "list"],
        gws_params=params,
        py_func=lambda: people_service.service.people().connections().list(**params),
    )
    contacts = []
    for person in results.get("connections", []):
        names = person.get("names", [{}])
        emails = person.get("emailAddresses", [])
        phones = person.get("phoneNumbers", [])
        contacts.append({
            "name": names[0].get("displayName", "") if names else "",
            "emails": [e.get("value", "") for e in emails],
            "phones": [p.get("value", "") for p in phones],
        })
    print(json.dumps(contacts, indent=2, ensure_ascii=False))


# =========================================================================
# Sheets
# =========================================================================


def sheets_get(args):
    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "values", "get"],
        gws_params={"spreadsheetId": args.sheet_id, "range": args.range},
        py_func=lambda: sheets_service.service.spreadsheets().values().get(
            spreadsheetId=args.sheet_id, range=args.range
        ),
    )
    print(json.dumps(result.get("values", []), indent=2, ensure_ascii=False))


def sheets_update(args):
    values = json.loads(args.values)
    body = {"values": values}
    params = {
        "spreadsheetId": args.sheet_id,
        "range": args.range,
        "valueInputOption": "USER_ENTERED",
    }

    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "values", "update"],
        gws_params=params,
        gws_body=body,
        py_func=lambda: sheets_service.service.spreadsheets().values().update(**params, body=body),
    )
    print(json.dumps({"updatedCells": result.get("updatedCells", 0), "updatedRange": result.get("updatedRange", "")}, indent=2))


def sheets_append(args):
    values = json.loads(args.values)
    body = {"values": values}
    params = {
        "spreadsheetId": args.sheet_id,
        "range": args.range,
        "valueInputOption": "USER_ENTERED",
        "insertDataOption": "INSERT_ROWS",
    }

    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "values", "append"],
        gws_params=params,
        gws_body=body,
        py_func=lambda: sheets_service.service.spreadsheets().values().append(**params, body=body),
    )
    print(json.dumps({"updatedCells": result.get("updates", {}).get("updatedCells", 0)}, indent=2))


def sheets_create(args):
    """Create a new spreadsheet. Returns the new spreadsheet ID and URL."""
    body = {"properties": {"title": args.title}}
    if args.sheet_name:
        body["sheets"] = [{"properties": {"title": args.sheet_name}}]

    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "create"],
        gws_body=body,
        py_func=lambda: sheets_service.service.spreadsheets().create(
            body=body, fields="spreadsheetId,properties,spreadsheetUrl"
        ),
    )
    print(json.dumps({
        "status": "created",
        "spreadsheetId": result.get("spreadsheetId", ""),
        "title": result.get("properties", {}).get("title", ""),
        "spreadsheetUrl": result.get("spreadsheetUrl", ""),
    }, indent=2, ensure_ascii=False))


# =========================================================================
# Docs
# =========================================================================


def docs_get(args):
    docs_service = ApiService("docs", "v1")
    doc = docs_service.execute(
        gws_parts=["documents", "get"],
        gws_params={"documentId": args.doc_id},
        py_func=lambda: docs_service.service.documents().get(documentId=args.doc_id),
    )
    result = {
        "title": doc.get("title", ""),
        "documentId": doc.get("documentId", ""),
        "body": _extract_doc_text(doc),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def docs_create(args):
    """Create a new Doc. Optionally seed it with initial body text."""
    body = {"title": args.title}

    docs_service = ApiService("docs", "v1")
    doc = docs_service.execute(
        gws_parts=["documents", "create"],
        gws_body=body,
        py_func=lambda: docs_service.service.documents().create(body=body),
    )

    doc_id = doc.get("documentId", "")

    if args.body and doc_id:
        _docs_insert_text(doc_id, args.body, index=1)

    print(json.dumps({
        "status": "created",
        "documentId": doc_id,
        "title": doc.get("title", ""),
        "url": f"https://docs.google.com/document/d/{doc_id}/edit" if doc_id else "",
    }, indent=2, ensure_ascii=False))


def docs_append(args):
    """Append text to the end of an existing Doc."""
    docs_service = ApiService("docs", "v1")
    doc = docs_service.execute(
        gws_parts=["documents", "get"],
        gws_params={"documentId": args.doc_id},
        py_func=lambda: docs_service.service.documents().get(documentId=args.doc_id),
    )

    # The end-of-body index is one less than the segment endIndex of the body
    # (trailing newline is always at length-1). Docs indexes are 1-based; use
    # endIndex - 1 to insert before the final newline.
    content = doc.get("body", {}).get("content", [])
    end_index = 1
    for element in content:
        ei = element.get("endIndex")
        if isinstance(ei, int) and ei > end_index:
            end_index = ei
    insert_index = max(end_index - 1, 1)

    text = args.text if args.text.endswith("\n") else args.text + "\n"
    _docs_insert_text(args.doc_id, text, index=insert_index)

    print(json.dumps({
        "status": "appended",
        "documentId": args.doc_id,
        "inserted_at": insert_index,
        "characters": len(text),
    }, indent=2, ensure_ascii=False))


def _docs_insert_text(doc_id: str, text: str, index: int) -> None:
    """Send a batchUpdate with a single insertText request."""
    requests = [{
        "insertText": {
            "location": {"index": index},
            "text": text,
        }
    }]
    docs_service = ApiService("docs", "v1")
    docs_service.execute(
        gws_parts=["documents", "batchUpdate"],
        gws_params={"documentId": doc_id},
        gws_body={"requests": requests},
        py_func=lambda: docs_service.service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}),
    )


# =========================================================================
# CLI parser
# =========================================================================


def main():
    parser = argparse.ArgumentParser(description="Google Workspace API for Hermes Agent")
    sub = parser.add_subparsers(dest="service", required=True)

    # --- Gmail ---
    gmail = sub.add_parser("gmail")
    gmail_sub = gmail.add_subparsers(dest="action", required=True)

    p = gmail_sub.add_parser("search")
    p.add_argument("query", help="Gmail search query (e.g. 'is:unread')")
    p.add_argument("--max", type=int, default=10)
    p.set_defaults(func=gmail_search)

    p = gmail_sub.add_parser("get")
    p.add_argument("message_id")
    p.set_defaults(func=gmail_get)

    p = gmail_sub.add_parser("send")
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--cc", default="")
    p.add_argument("--from", dest="from_header", default="", help="Custom From header (e.g. '\"Agent Name\" <user@example.com>')")
    p.add_argument("--html", action="store_true", help="Send body as HTML")
    p.add_argument("--thread-id", default="", help="Thread ID for threading")
    p.set_defaults(func=gmail_send)

    p = gmail_sub.add_parser("reply")
    p.add_argument("message_id", help="Message ID to reply to")
    p.add_argument("--body", required=True)
    p.add_argument("--from", dest="from_header", default="", help="Custom From header (e.g. '\"Agent Name\" <user@example.com>')")
    p.set_defaults(func=gmail_reply)

    p = gmail_sub.add_parser("labels")
    p.set_defaults(func=gmail_labels)

    p = gmail_sub.add_parser("modify")
    p.add_argument("message_id")
    p.add_argument("--add-labels", default="", help="Comma-separated label IDs to add")
    p.add_argument("--remove-labels", default="", help="Comma-separated label IDs to remove")
    p.set_defaults(func=gmail_modify)

    # --- Calendar ---
    cal = sub.add_parser("calendar")
    cal_sub = cal.add_subparsers(dest="action", required=True)

    p = cal_sub.add_parser("list")
    p.add_argument("--start", default="", help="Start time (ISO 8601)")
    p.add_argument("--end", default="", help="End time (ISO 8601)")
    p.add_argument("--max", type=int, default=25)
    p.add_argument("--calendar", default="primary")
    p.set_defaults(func=calendar_list)

    p = cal_sub.add_parser("create")
    p.add_argument("--summary", required=True)
    p.add_argument("--start", required=True, help="Start (ISO 8601 with timezone)")
    p.add_argument("--end", required=True, help="End (ISO 8601 with timezone)")
    p.add_argument("--location", default="")
    p.add_argument("--description", default="")
    p.add_argument("--attendees", default="", help="Comma-separated email addresses")
    p.add_argument("--calendar", default="primary")
    p.set_defaults(func=calendar_create)

    p = cal_sub.add_parser("delete")
    p.add_argument("event_id")
    p.add_argument("--calendar", default="primary")
    p.set_defaults(func=calendar_delete)

    # --- Drive ---
    drv = sub.add_parser("drive")
    drv_sub = drv.add_subparsers(dest="action", required=True)

    p = drv_sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--max", type=int, default=10)
    p.add_argument("--raw-query", action="store_true", help="Use query as raw Drive API query")
    p.set_defaults(func=drive_search)

    p = drv_sub.add_parser("get")
    p.add_argument("file_id")
    p.set_defaults(func=drive_get)

    p = drv_sub.add_parser("upload")
    p.add_argument("path", help="Local file path to upload")
    p.add_argument("--name", default="", help="Override file name in Drive (defaults to local filename)")
    p.add_argument("--parent", default="", help="Parent folder ID")
    p.add_argument("--mime-type", default="", help="Override MIME type (auto-detected if omitted)")
    p.set_defaults(func=drive_upload)

    p = drv_sub.add_parser("download")
    p.add_argument("file_id")
    p.add_argument("--output", default="", help="Local output path (defaults to ./<name> in cwd)")
    p.add_argument("--export-mime", default="", help="Export MIME for Google-native files (overrides defaults: pdf for Docs/Slides, csv for Sheets, png for Drawings)")
    p.set_defaults(func=drive_download)

    p = drv_sub.add_parser("create-folder")
    p.add_argument("name")
    p.add_argument("--parent", default="", help="Parent folder ID (defaults to root)")
    p.set_defaults(func=drive_create_folder)

    p = drv_sub.add_parser("share")
    p.add_argument("file_id")
    p.add_argument("--role", default="reader", choices=["reader", "commenter", "writer", "fileOrganizer", "organizer", "owner"])
    p.add_argument("--type", default="user", choices=["user", "group", "domain", "anyone"])
    p.add_argument("--email", default="", help="Email address (required for type=user or type=group)")
    p.add_argument("--domain", default="", help="Domain (required for type=domain)")
    p.add_argument("--notify", action="store_true", help="Send notification email")
    p.set_defaults(func=drive_share)

    p = drv_sub.add_parser("delete")
    p.add_argument("file_id")
    p.add_argument("--permanent", action="store_true", help="Permanently delete (default is trash, which is reversible)")
    p.set_defaults(func=drive_delete)

    # --- Contacts ---
    con = sub.add_parser("contacts")
    con_sub = con.add_subparsers(dest="action", required=True)

    p = con_sub.add_parser("list")
    p.add_argument("--max", type=int, default=50)
    p.set_defaults(func=contacts_list)

    # --- Sheets ---
    sh = sub.add_parser("sheets")
    sh_sub = sh.add_subparsers(dest="action", required=True)

    p = sh_sub.add_parser("get")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.set_defaults(func=sheets_get)

    p = sh_sub.add_parser("update")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.add_argument("--values", required=True, help="JSON array of arrays")
    p.set_defaults(func=sheets_update)

    p = sh_sub.add_parser("append")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.add_argument("--values", required=True, help="JSON array of arrays")
    p.set_defaults(func=sheets_append)

    p = sh_sub.add_parser("create")
    p.add_argument("--title", required=True, help="Spreadsheet title")
    p.add_argument("--sheet-name", default="", help="Name of the first tab (defaults to 'Sheet1')")
    p.set_defaults(func=sheets_create)

    # --- Docs ---
    docs = sub.add_parser("docs")
    docs_sub = docs.add_subparsers(dest="action", required=True)

    p = docs_sub.add_parser("get")
    p.add_argument("doc_id")
    p.set_defaults(func=docs_get)

    p = docs_sub.add_parser("create")
    p.add_argument("--title", required=True, help="Document title")
    p.add_argument("--body", default="", help="Initial body text (optional)")
    p.set_defaults(func=docs_create)

    p = docs_sub.add_parser("append")
    p.add_argument("doc_id")
    p.add_argument("--text", required=True, help="Text to append to the end of the document")
    p.set_defaults(func=docs_append)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
        result = {
            "id": msg["id"],
            "threadId": msg["threadId"],
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "labels": msg.get("labelIds", []),
            "body": _extract_message_body(msg),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    service = build_service("gmail", "v1")
    msg = service.users().messages().get(
        userId="me", id=args.message_id, format="full"
    ).execute()

    headers = _headers_dict(msg)
    result = {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "labels": msg.get("labelIds", []),
        "body": _extract_message_body(msg),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))



def gmail_send(args):
    message = MIMEText(args.body, "html" if args.html else "plain")
    message["To"] = args.to
    message["Subject"] = args.subject
    if args.cc:
        message["Cc"] = args.cc
    if args.from_header:
        message["From"] = args.from_header

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw}
    if args.thread_id:
        body["threadId"] = args.thread_id

    gmail_service = ApiService("gmail", "v1")
    result = gmail_service.execute(
        gws_parts=["users", "messages", "send"],
        gws_params={"userId": "me"},
        gws_body=body,
        py_func=lambda: gmail_service.service.users().messages().send(userId="me", body=body),
    )
    print(json.dumps({"status": "sent", "id": result["id"], "threadId": result.get("threadId", "")}, indent=2))



def gmail_reply(args):
    # The gws and python-native logic are slightly different here, so a full
    # abstraction is more complex. We can still simplify.
    service = build_service("gmail", "v1")
    original = service.users().messages().get(
        userId="me", id=args.message_id, format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID"],
    ).execute()
    headers = _headers_dict(original)

    subject = headers.get("subject", "")
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"

    message = MIMEText(args.body)
    message["To"] = headers.get("from", "")
    message["Subject"] = subject
    if args.from_header:
        message["From"] = args.from_header
    if headers.get("message-id"):
        message["In-Reply-To"] = headers["message-id"]
        message["References"] = headers["message-id"]

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw, "threadId": original["threadId"]}

    gmail_service = ApiService("gmail", "v1")
    result = gmail_service.execute(
        gws_parts=["users", "messages", "send"],
        gws_params={"userId": "me"},
        gws_body=body,
        py_func=lambda: gmail_service.service.users().messages().send(userId="me", body=body),
    )
    print(json.dumps({"status": "sent", "id": result["id"], "threadId": result.get("threadId", "")}, indent=2))



def gmail_labels(args):
    gmail_service = ApiService("gmail", "v1")
    results = gmail_service.execute(
        gws_parts=["users", "labels", "list"],
        gws_params={"userId": "me"},
        py_func=lambda: gmail_service.service.users().labels().list(userId="me"),
    )
    labels = [{"id": l["id"], "name": l["name"], "type": l.get("type", "")} for l in results.get("labels", [])]
    print(json.dumps(labels, indent=2))



def gmail_modify(args):
    body = {}
    if args.add_labels:
        body["addLabelIds"] = args.add_labels.split(",")
    if args.remove_labels:
        body["removeLabelIds"] = args.remove_labels.split(",")

    gmail_service = ApiService("gmail", "v1")
    result = gmail_service.execute(
        gws_parts=["users", "messages", "modify"],
        gws_params={"userId": "me", "id": args.message_id},
        gws_body=body,
        py_func=lambda: gmail_service.service.users().messages().modify(userId="me", id=args.message_id, body=body),
    )
    print(json.dumps({"id": result["id"], "labels": result.get("labelIds", [])}, indent=2))


# =========================================================================
# Calendar
# =========================================================================


def calendar_list(args):
    now = datetime.now(timezone.utc)
    time_min = _datetime_with_timezone(args.start or now.isoformat())
    time_max = _datetime_with_timezone(args.end or (now + timedelta(days=7)).isoformat())

    params = {
        "calendarId": args.calendar,
        "timeMin": time_min,
        "timeMax": time_max,
        "maxResults": args.max,
        "singleEvents": True,
        "orderBy": "startTime",
    }

    cal_service = ApiService("calendar", "v3")
    results = cal_service.execute(
        gws_parts=["events", "list"],
        gws_params=params,
        py_func=lambda: cal_service.service.events().list(**params),
    )

    events = []
    for e in results.get("items", []):
        events.append({
            "id": e["id"],
            "summary": e.get("summary", "(no title)"),
            "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
            "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date", "")),
            "location": e.get("location", ""),
            "description": e.get("description", ""),
            "status": e.get("status", ""),
            "htmlLink": e.get("htmlLink", ""),
        })
    print(json.dumps(events, indent=2, ensure_ascii=False))



def calendar_create(args):
    event = {
        "summary": args.summary,
        "start": {"dateTime": args.start},
        "end": {"dateTime": args.end},
    }
    if args.location:
        event["location"] = args.location
    if args.description:
        event["description"] = args.description
    if args.attendees:
        event["attendees"] = [{"email": e.strip()} for e in args.attendees.split(",") if e.strip()]

    cal_service = ApiService("calendar", "v3")
    result = cal_service.execute(
        gws_parts=["events", "insert"],
        gws_params={"calendarId": args.calendar},
        gws_body=event,
        py_func=lambda: cal_service.service.events().insert(calendarId=args.calendar, body=event),
    )
    print(json.dumps({
        "status": "created",
        "id": result["id"],
        "summary": result.get("summary", ""),
        "htmlLink": result.get("htmlLink", ""),
    }, indent=2))



def calendar_delete(args):
    cal_service = ApiService("calendar", "v3")
    cal_service.execute(
        gws_parts=["events", "delete"],
        gws_params={"calendarId": args.calendar, "eventId": args.event_id},
        py_func=lambda: cal_service.service.events().delete(calendarId=args.calendar, eventId=args.event_id),
    )
    print(json.dumps({"status": "deleted", "eventId": args.event_id}))


# =========================================================================
# Drive
# =========================================================================


def drive_search(args):
    query = args.query if args.raw_query else f"fullText contains '{args.query}'"
    params = {
        "q": query,
        "pageSize": args.max,
        "fields": "files(id, name, mimeType, modifiedTime, webViewLink)",
    }

    drive_service = ApiService("drive", "v3")
    results = drive_service.execute(
        gws_parts=["files", "list"],
        gws_params=params,
        py_func=lambda: drive_service.service.files().list(**params),
    )
    print(json.dumps(results.get("files", []), indent=2, ensure_ascii=False))


def drive_get(args):
    """Get metadata for a single Drive file by ID."""
    fields = "id, name, mimeType, modifiedTime, size, webViewLink, parents, owners(emailAddress)"
    drive_service = ApiService("drive", "v3")
    result = drive_service.execute(
        gws_parts=["files", "get"],
        gws_params={"fileId": args.file_id, "fields": fields},
        py_func=lambda: drive_service.service.files().get(fileId=args.file_id, fields=fields),
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def drive_upload(args):
    """Upload a local file to Drive. Falls through to Python client even when gws
    is installed, because gws doesn't do multipart uploads."""
    import mimetypes
    from googleapiclient.http import MediaFileUpload

    local_path = Path(args.path).expanduser()
    if not local_path.exists():
        print(f"ERROR: file not found: {local_path}", file=sys.stderr)
        sys.exit(1)

    mime = args.mime_type or mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    metadata = {"name": args.name or local_path.name}
    if args.parent:
        metadata["parents"] = [args.parent]

    service = build_service("drive", "v3")
    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=True)
    result = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, mimeType, webViewLink",
    ).execute()
    print(json.dumps({
        "status": "uploaded",
        "id": result["id"],
        "name": result.get("name", ""),
        "mimeType": result.get("mimeType", ""),
        "webViewLink": result.get("webViewLink", ""),
    }, indent=2, ensure_ascii=False))


def drive_download(args):
    """Download a Drive file to a local path. Google-native files (Docs/Sheets/Slides)
    must be exported; binary files are downloaded as-is."""
    import io
    from googleapiclient.http import MediaIoBaseDownload

    service = build_service("drive", "v3")

    # Look up the file to decide download vs export.
    meta = service.files().get(fileId=args.file_id, fields="id, name, mimeType").execute()
    mime = meta.get("mimeType", "")
    name = meta.get("name", args.file_id)

    # Map Google-native MIME types to a sensible export default.
    native_export_map = {
        "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
        "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
        "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
        "application/vnd.google-apps.drawing": ("image/png", ".png"),
    }

    out_path = Path(args.output).expanduser() if args.output else Path.cwd() / name

    if mime in native_export_map:
        export_mime = args.export_mime or native_export_map[mime][0]
        default_ext = native_export_map[mime][1]
        if not args.output and not out_path.suffix:
            out_path = out_path.with_suffix(default_ext)
        request = service.files().export_media(fileId=args.file_id, mimeType=export_mime)
    else:
        request = service.files().get_media(fileId=args.file_id)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fh = io.FileIO(str(out_path), "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()

    print(json.dumps({
        "status": "downloaded",
        "id": args.file_id,
        "name": name,
        "path": str(out_path),
        "mimeType": mime,
    }, indent=2, ensure_ascii=False))


def drive_create_folder(args):
    body = {
        "name": args.name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if args.parent:
        body["parents"] = [args.parent]

    drive_service = ApiService("drive", "v3")
    result = drive_service.execute(
        gws_parts=["files", "create"],
        gws_params={"fields": "id, name, webViewLink"},
        gws_body=body,
        py_func=lambda: drive_service.service.files().create(body=body, fields="id, name, webViewLink"),
    )
    print(json.dumps({
        "status": "created",
        "id": result["id"],
        "name": result.get("name", ""),
        "webViewLink": result.get("webViewLink", ""),
    }, indent=2, ensure_ascii=False))


def drive_share(args):
    permission = {
        "type": args.type,
        "role": args.role,
    }
    if args.type in {"user", "group"}:
        if not args.email:
            print("ERROR: --email is required for type=user or type=group", file=sys.stderr)
            sys.exit(1)
        permission["emailAddress"] = args.email
    elif args.type == "domain":
        if not args.domain:
            print("ERROR: --domain is required for type=domain", file=sys.stderr)
            sys.exit(1)
        permission["domain"] = args.domain

    drive_service = ApiService("drive", "v3")
    result = drive_service.execute(
        gws_parts=["permissions", "create"],
        gws_params={"fileId": args.file_id, "sendNotificationEmail": args.notify},
        gws_body=permission,
        py_func=lambda: drive_service.service.permissions().create(
            fileId=args.file_id,
            body=permission,
            sendNotificationEmail=args.notify,
            fields="id",
        ),
    )
    print(json.dumps({
        "status": "shared",
        "permissionId": result.get("id", ""),
        "fileId": args.file_id,
        "role": permission["role"],
        "type": permission["type"],
    }, indent=2, ensure_ascii=False))


def drive_delete(args):
    """Trash or permanently delete a Drive file. Defaults to trash (reversible)."""
    drive_service = ApiService("drive", "v3")
    if args.permanent:
        drive_service.execute(
            gws_parts=["files", "delete"],
            gws_params={"fileId": args.file_id},
            py_func=lambda: drive_service.service.files().delete(fileId=args.file_id),
        )
        print(json.dumps({"status": "deleted", "fileId": args.file_id, "permanent": True}))
        return

    # Trash (reversible). Use files.update with trashed=True.
    body = {"trashed": True}
    drive_service.execute(
        gws_parts=["files", "update"],
        gws_params={"fileId": args.file_id},
        gws_body=body,
        py_func=lambda: drive_service.service.files().update(fileId=args.file_id, body=body),
    )
    print(json.dumps({"status": "trashed", "fileId": args.file_id, "permanent": False}))


# =========================================================================
# Contacts
# =========================================================================


def contacts_list(args):
    params = {
        "resourceName": "people/me",
        "pageSize": args.max,
        "personFields": "names,emailAddresses,phoneNumbers",
    }
    people_service = ApiService("people", "v1")
    results = people_service.execute(
        gws_parts=["people", "connections", "list"],
        gws_params=params,
        py_func=lambda: people_service.service.people().connections().list(**params),
    )
    contacts = []
    for person in results.get("connections", []):
        names = person.get("names", [{}])
        emails = person.get("emailAddresses", [])
        phones = person.get("phoneNumbers", [])
        contacts.append({
            "name": names[0].get("displayName", "") if names else "",
            "emails": [e.get("value", "") for e in emails],
            "phones": [p.get("value", "") for p in phones],
        })
    print(json.dumps(contacts, indent=2, ensure_ascii=False))


# =========================================================================
# Sheets
# =========================================================================


def sheets_get(args):
    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "values", "get"],
        gws_params={"spreadsheetId": args.sheet_id, "range": args.range},
        py_func=lambda: sheets_service.service.spreadsheets().values().get(
            spreadsheetId=args.sheet_id, range=args.range
        ),
    )
    print(json.dumps(result.get("values", []), indent=2, ensure_ascii=False))



def sheets_update(args):
    values = json.loads(args.values)
    body = {"values": values}
    params = {
        "spreadsheetId": args.sheet_id,
        "range": args.range,
        "valueInputOption": "USER_ENTERED",
    }

    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "values", "update"],
        gws_params=params,
        gws_body=body,
        py_func=lambda: sheets_service.service.spreadsheets().values().update(**params, body=body),
    )
    print(json.dumps({"updatedCells": result.get("updatedCells", 0), "updatedRange": result.get("updatedRange", "")}, indent=2))



def sheets_append(args):
    values = json.loads(args.values)
    body = {"values": values}
    params = {
        "spreadsheetId": args.sheet_id,
        "range": args.range,
        "valueInputOption": "USER_ENTERED",
        "insertDataOption": "INSERT_ROWS",
    }

    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "values", "append"],
        gws_params=params,
        gws_body=body,
        py_func=lambda: sheets_service.service.spreadsheets().values().append(**params, body=body),
    )
    print(json.dumps({"updatedCells": result.get("updates", {}).get("updatedCells", 0)}, indent=2))


def sheets_create(args):
    """Create a new spreadsheet. Returns the new spreadsheet ID and URL."""
    body = {"properties": {"title": args.title}}
    if args.sheet_name:
        body["sheets"] = [{"properties": {"title": args.sheet_name}}]

    sheets_service = ApiService("sheets", "v4")
    result = sheets_service.execute(
        gws_parts=["spreadsheets", "create"],
        gws_body=body,
        py_func=lambda: sheets_service.service.spreadsheets().create(
            body=body, fields="spreadsheetId,properties,spreadsheetUrl"
        ),
    )
    print(json.dumps({
        "status": "created",
        "spreadsheetId": result.get("spreadsheetId", ""),
        "title": result.get("properties", {}).get("title", ""),
        "spreadsheetUrl": result.get("spreadsheetUrl", ""),
    }, indent=2, ensure_ascii=False))


# =========================================================================
# Docs
# =========================================================================


def docs_get(args):
    docs_service = ApiService("docs", "v1")
    doc = docs_service.execute(
        gws_parts=["documents", "get"],
        gws_params={"documentId": args.doc_id},
        py_func=lambda: docs_service.service.documents().get(documentId=args.doc_id),
    )
    result = {
        "title": doc.get("title", ""),
        "documentId": doc.get("documentId", ""),
        "body": _extract_doc_text(doc),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def docs_create(args):
    """Create a new Doc. Optionally seed it with initial body text."""
    body = {"title": args.title}

    docs_service = ApiService("docs", "v1")
    doc = docs_service.execute(
        gws_parts=["documents", "create"],
        gws_body=body,
        py_func=lambda: docs_service.service.documents().create(body=body),
    )
    
    doc_id = doc.get("documentId", "")

    if args.body and doc_id:
        _docs_insert_text(doc_id, args.body, index=1)

    print(json.dumps({
        "status": "created",
        "documentId": doc_id,
        "title": doc.get("title", ""),
        "url": f"https://docs.google.com/document/d/{doc_id}/edit" if doc_id else "",
    }, indent=2, ensure_ascii=False))


def docs_append(args):
    """Append text to the end of an existing Doc."""
    docs_service = ApiService("docs", "v1")
    doc = docs_service.execute(
        gws_parts=["documents", "get"],
        gws_params={"documentId": args.doc_id},
        py_func=lambda: docs_service.service.documents().get(documentId=args.doc_id),
    )
    
    # The end-of-body index is one less than the segment endIndex of the body
    # (trailing newline is always at length-1). Docs indexes are 1-based; use
    # endIndex - 1 to insert before the final newline.
    content = doc.get("body", {}).get("content", [])
    end_index = 1
    for element in content:
        ei = element.get("endIndex")
        if isinstance(ei, int) and ei > end_index:
            end_index = ei
    insert_index = max(end_index - 1, 1)

    text = args.text if args.text.endswith("\n") else args.text + "\n"
    _docs_insert_text(args.doc_id, text, index=insert_index)

    print(json.dumps({
        "status": "appended",
        "documentId": args.doc_id,
        "inserted_at": insert_index,
        "characters": len(text),
    }, indent=2, ensure_ascii=False))


def _docs_insert_text(doc_id: str, text: str, index: int) -> None:
    """Send a batchUpdate with a single insertText request."""
    requests = [{
        "insertText": {
            "location": {"index": index},
            "text": text,
        }
    }]
    docs_service = ApiService("docs", "v1")
    docs_service.execute(
        gws_parts=["documents", "batchUpdate"],
        gws_params={"documentId": doc_id},
        gws_body={"requests": requests},
        py_func=lambda: docs_service.service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}),
    )

# =========================================================================
# CLI parser
# =========================================================================


def main():
    parser = argparse.ArgumentParser(description="Google Workspace API for Hermes Agent")
    sub = parser.add_subparsers(dest="service", required=True)

    # --- Gmail ---
    gmail = sub.add_parser("gmail")
    gmail_sub = gmail.add_subparsers(dest="action", required=True)

    p = gmail_sub.add_parser("search")
    p.add_argument("query", help="Gmail search query (e.g. 'is:unread')")
    p.add_argument("--max", type=int, default=10)
    p.set_defaults(func=gmail_search)

    p = gmail_sub.add_parser("get")
    p.add_argument("message_id")
    p.set_defaults(func=gmail_get)

    p = gmail_sub.add_parser("send")
    p.add_argument("--to", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--cc", default="")
    p.add_argument("--from", dest="from_header", default="", help="Custom From header (e.g. '\"Agent Name\" <user@example.com>')")
    p.add_argument("--html", action="store_true", help="Send body as HTML")
    p.add_argument("--thread-id", default="", help="Thread ID for threading")
    p.set_defaults(func=gmail_send)

    p = gmail_sub.add_parser("reply")
    p.add_argument("message_id", help="Message ID to reply to")
    p.add_argument("--body", required=True)
    p.add_argument("--from", dest="from_header", default="", help="Custom From header (e.g. '\"Agent Name\" <user@example.com>')")
    p.set_defaults(func=gmail_reply)

    p = gmail_sub.add_parser("labels")
    p.set_defaults(func=gmail_labels)

    p = gmail_sub.add_parser("modify")
    p.add_argument("message_id")
    p.add_argument("--add-labels", default="", help="Comma-separated label IDs to add")
    p.add_argument("--remove-labels", default="", help="Comma-separated label IDs to remove")
    p.set_defaults(func=gmail_modify)

    # --- Calendar ---
    cal = sub.add_parser("calendar")
    cal_sub = cal.add_subparsers(dest="action", required=True)

    p = cal_sub.add_parser("list")
    p.add_argument("--start", default="", help="Start time (ISO 8601)")
    p.add_argument("--end", default="", help="End time (ISO 8601)")
    p.add_argument("--max", type=int, default=25)
    p.add_argument("--calendar", default="primary")
    p.set_defaults(func=calendar_list)

    p = cal_sub.add_parser("create")
    p.add_argument("--summary", required=True)
    p.add_argument("--start", required=True, help="Start (ISO 8601 with timezone)")
    p.add_argument("--end", required=True, help="End (ISO 8601 with timezone)")
    p.add_argument("--location", default="")
    p.add_argument("--description", default="")
    p.add_argument("--attendees", default="", help="Comma-separated email addresses")
    p.add_argument("--calendar", default="primary")
    p.set_defaults(func=calendar_create)

    p = cal_sub.add_parser("delete")
    p.add_argument("event_id")
    p.add_argument("--calendar", default="primary")
    p.set_defaults(func=calendar_delete)

    # --- Drive ---
    drv = sub.add_parser("drive")
    drv_sub = drv.add_subparsers(dest="action", required=True)

    p = drv_sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--max", type=int, default=10)
    p.add_argument("--raw-query", action="store_true", help="Use query as raw Drive API query")
    p.set_defaults(func=drive_search)

    p = drv_sub.add_parser("get")
    p.add_argument("file_id")
    p.set_defaults(func=drive_get)

    p = drv_sub.add_parser("upload")
    p.add_argument("path", help="Local file path to upload")
    p.add_argument("--name", default="", help="Override file name in Drive (defaults to local filename)")
    p.add_argument("--parent", default="", help="Parent folder ID")
    p.add_argument("--mime-type", default="", help="Override MIME type (auto-detected if omitted)")
    p.set_defaults(func=drive_upload)

    p = drv_sub.add_parser("download")
    p.add_argument("file_id")
    p.add_argument("--output", default="", help="Local output path (defaults to ./<name> in cwd)")
    p.add_argument("--export-mime", default="", help="Export MIME for Google-native files (overrides defaults: pdf for Docs/Slides, csv for Sheets, png for Drawings)")
    p.set_defaults(func=drive_download)

    p = drv_sub.add_parser("create-folder")
    p.add_argument("name")
    p.add_argument("--parent", default="", help="Parent folder ID (defaults to root)")
    p.set_defaults(func=drive_create_folder)

    p = drv_sub.add_parser("share")
    p.add_argument("file_id")
    p.add_argument("--role", default="reader", choices=["reader", "commenter", "writer", "fileOrganizer", "organizer", "owner"])
    p.add_argument("--type", default="user", choices=["user", "group", "domain", "anyone"])
    p.add_argument("--email", default="", help="Email address (required for type=user or type=group)")
    p.add_argument("--domain", default="", help="Domain (required for type=domain)")
    p.add_argument("--notify", action="store_true", help="Send notification email")
    p.set_defaults(func=drive_share)

    p = drv_sub.add_parser("delete")
    p.add_argument("file_id")
    p.add_argument("--permanent", action="store_true", help="Permanently delete (default is trash, which is reversible)")
    p.set_defaults(func=drive_delete)

    # --- Contacts ---
    con = sub.add_parser("contacts")
    con_sub = con.add_subparsers(dest="action", required=True)

    p = con_sub.add_parser("list")
    p.add_argument("--max", type=int, default=50)
    p.set_defaults(func=contacts_list)

    # --- Sheets ---
    sh = sub.add_parser("sheets")
    sh_sub = sh.add_subparsers(dest="action", required=True)

    p = sh_sub.add_parser("get")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.set_defaults(func=sheets_get)

    p = sh_sub.add_parser("update")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.add_argument("--values", required=True, help="JSON array of arrays")
    p.set_defaults(func=sheets_update)

    p = sh_sub.add_parser("append")
    p.add_argument("sheet_id")
    p.add_argument("range")
    p.add_argument("--values", required=True, help="JSON array of arrays")
    p.set_defaults(func=sheets_append)

    p = sh_sub.add_parser("create")
    p.add_argument("--title", required=True, help="Spreadsheet title")
    p.add_argument("--sheet-name", default="", help="Name of the first tab (defaults to 'Sheet1')")
    p.set_defaults(func=sheets_create)

    # --- Docs ---
    docs = sub.add_parser("docs")
    docs_sub = docs.add_subparsers(dest="action", required=True)

    p = docs_sub.add_parser("get")
    p.add_argument("doc_id")
    p.set_defaults(func=docs_get)

    p = docs_sub.add_parser("create")
    p.add_argument("--title", required=True, help="Document title")
    p.add_argument("--body", default="", help="Initial body text (optional)")
    p.set_defaults(func=docs_create)

    p = docs_sub.add_parser("append")
    p.add_argument("doc_id")
    p.add_argument("--text", required=True, help="Text to append to the end of the document")
    p.set_defaults(func=docs_append)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
