"""Curated catalog of Graph/Teams/Copilot actions, backing search_actions.

This is a hand-picked subset of the Graph v1.0 surface, not a full mirror of
it — the full surface is thousands of endpoints. Entries marked
stability="beta" or "verify" are less certain (newer Graph Copilot APIs move
fast); double-check against https://learn.microsoft.com/graph/api/overview
before relying on them in production. Anything not listed here is still
reachable via `execute_action` with a raw Graph path.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionSpec:
    id: str
    method: str
    path_template: str
    description: str
    params: tuple[str, ...] = ()
    stability: str = "stable"  # "stable" | "beta" | "verify"
    # True for endpoints Microsoft Graph documents as delegated-auth-only
    # (Application permissions explicitly "Not supported"). This server only
    # implements app-only (client-credentials) auth, so execute_action must
    # refuse these rather than send a call that will always 403.
    requires_delegated_auth: bool = False


CATALOG: tuple[ActionSpec, ...] = (
    # --- Teams & channels ---
    ActionSpec(
        "list_joined_teams",
        "GET",
        "/me/joinedTeams",
        "List teams the calling identity's delegated user is a member of. "
        "Note: app-only auth has no signed-in user — use list_teams_in_org "
        "or a specific /users/{id}/joinedTeams instead in that mode.",
    ),
    ActionSpec(
        "list_teams_in_org",
        "GET",
        "/teams",
        "List all Teams-enabled groups in the tenant (requires Team.ReadBasic.All).",
    ),
    ActionSpec(
        "list_channels",
        "GET",
        "/teams/{team_id}/channels",
        "List channels in a team.",
        params=("team_id",),
    ),
    ActionSpec(
        "list_channel_messages",
        "GET",
        "/teams/{team_id}/channels/{channel_id}/messages",
        "List recent messages in a channel.",
        params=("team_id", "channel_id"),
    ),
    ActionSpec(
        "send_channel_message",
        "POST",
        "/teams/{team_id}/channels/{channel_id}/messages",
        "Post a message to a channel. Body: {'body': {'content': '<html or text>'}}.",
        params=("team_id", "channel_id"),
    ),
    ActionSpec(
        "list_team_members",
        "GET",
        "/teams/{team_id}/members",
        "List members of a team.",
        params=("team_id",),
    ),
    # --- Chats (1:1 / group, not channels) ---
    ActionSpec(
        "list_chat_messages",
        "GET",
        "/chats/{chat_id}/messages",
        "List messages in a 1:1 or group chat.",
        params=("chat_id",),
    ),
    ActionSpec(
        "send_chat_message",
        "POST",
        "/chats/{chat_id}/messages",
        "Send a message to a 1:1 or group chat. Body: {'body': {'content': '<html or text>'}}.",
        params=("chat_id",),
    ),
    # --- Online meetings & transcripts ---
    ActionSpec(
        "create_online_meeting",
        "POST",
        "/users/{user_id}/onlineMeetings",
        "Create a Teams online meeting on behalf of a user.",
        params=("user_id",),
    ),
    ActionSpec(
        "get_online_meeting",
        "GET",
        "/users/{user_id}/onlineMeetings/{meeting_id}",
        "Get details of an online meeting.",
        params=("user_id", "meeting_id"),
    ),
    ActionSpec(
        "list_meeting_transcripts",
        "GET",
        "/users/{user_id}/onlineMeetings/{meeting_id}/transcripts",
        "List transcript artifacts for a meeting (metadata only, not content).",
        params=("user_id", "meeting_id"),
    ),
    ActionSpec(
        "get_meeting_transcript_content",
        "GET",
        "/users/{user_id}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content",
        "Fetch the actual transcript content (VTT format) for a meeting.",
        params=("user_id", "meeting_id", "transcript_id"),
    ),
    # --- Calendar ---
    ActionSpec(
        "list_calendar_events",
        "GET",
        "/users/{user_id}/calendar/events",
        "List calendar events for a user.",
        params=("user_id",),
    ),
    ActionSpec(
        "create_calendar_event",
        "POST",
        "/users/{user_id}/calendar/events",
        "Create a calendar event for a user.",
        params=("user_id",),
    ),
    # --- Users & presence ---
    ActionSpec(
        "get_user",
        "GET",
        "/users/{user_id}",
        "Get a user's profile by id or userPrincipalName.",
        params=("user_id",),
    ),
    ActionSpec(
        "list_users",
        "GET",
        "/users",
        "List users in the tenant (supports $filter, $search via execute_action params).",
    ),
    ActionSpec(
        "get_user_presence",
        "GET",
        "/users/{user_id}/presence",
        "Get a user's Teams presence (available/busy/away/offline).",
        params=("user_id",),
    ),
    # --- Copilot (newer Graph surface; verify before relying on in prod) ---
    ActionSpec(
        "copilot_retrieval_query",
        "POST",
        "/copilot/retrieval",
        "Query the Microsoft Graph Copilot Retrieval API for grounding content "
        "across connected data sources. Body: {queryString, dataSource: "
        "'sharePoint'|'oneDriveBusiness'|'externalItem', filterExpression?, "
        "dataSourceConfiguration?, maximumNumberOfResults? (max 25)}. Requires "
        "delegated (signed-in-user) auth — Application permissions are not "
        "supported by this endpoint. Not usable via this server's app-only "
        "auth; see the dedicated copilot_retrieval_query tool for details.",
        stability="verify",
        requires_delegated_auth=True,
    ),
)


def find(action_id: str) -> ActionSpec | None:
    for spec in CATALOG:
        if spec.id == action_id:
            return spec
    return None


def search(query: str) -> list[ActionSpec]:
    q = query.lower()
    return [
        spec
        for spec in CATALOG
        if q in spec.id.lower() or q in spec.description.lower()
    ]
