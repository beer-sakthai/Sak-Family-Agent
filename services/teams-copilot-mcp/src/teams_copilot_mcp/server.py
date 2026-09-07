"""MCP server exposing Microsoft Teams (Graph) and M365 Copilot operations.

Tool design: a handful of dedicated tools for the common Teams operations,
plus search_actions/execute_action for the long tail of the Graph surface —
see catalog.py for what's curated vs. reachable only via the raw passthrough.
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from teams_copilot_mcp import catalog
from teams_copilot_mcp.graph_client import get_client

mcp = FastMCP("teams-copilot-mcp")


def _resolve_path(template: str, path_params: dict[str, Any]) -> str:
    try:
        return template.format(**path_params)
    except KeyError as exc:
        raise ValueError(f"Missing required path param: {exc}") from exc


# --- Long-tail escape hatch --------------------------------------------


@mcp.tool()
def search_actions(query: str) -> list[dict[str, Any]]:
    """Search the curated catalog of Teams/Graph/Copilot actions by keyword.

    Returns matching entries with their id, method, path template, required
    path params, a stability marker ("stable" | "beta" | "verify"), and
    whether the endpoint requires delegated auth this server doesn't support.
    Feed the returned `id` into execute_action to run one.
    """
    return [
        {
            "id": spec.id,
            "method": spec.method,
            "path_template": spec.path_template,
            "description": spec.description,
            "params": list(spec.params),
            "stability": spec.stability,
            "requires_delegated_auth": spec.requires_delegated_auth,
        }
        for spec in catalog.search(query)
    ]


@mcp.tool()
def execute_action(
    action_id: str,
    path_params: dict[str, Any] | None = None,
    query_params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a catalog action by id (from search_actions) against Graph.

    path_params fill the {placeholders} in the action's path template
    (e.g. {"team_id": "...", "channel_id": "..."}). query_params become
    Graph OData query params (e.g. {"$filter": "...", "$top": 10}). body is
    the JSON payload for POST/PATCH actions.
    """
    spec = catalog.find(action_id)
    if spec is None:
        raise ValueError(
            f"Unknown action_id '{action_id}'. Use search_actions to find valid ids, "
            "or execute_raw for a Graph path not in the catalog."
        )
    if spec.requires_delegated_auth:
        raise NotImplementedError(
            f"'{action_id}' requires delegated (signed-in-user) Graph auth — this "
            "server only implements app-only auth, so the call would always fail. "
            "See the action's description via search_actions for details."
        )
    path = _resolve_path(spec.path_template, path_params or {})
    return get_client().request(spec.method, path, params=query_params, json_body=body)


@mcp.tool()
def execute_raw(
    method: str,
    path: str,
    query_params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call an arbitrary Microsoft Graph v1.0 endpoint not in the catalog.

    `path` is relative to https://graph.microsoft.com/v1.0 (e.g.
    "/users/{id}/joinedTeams") or a full @odata.nextLink URL for pagination.
    Use this for anything search_actions/execute_action doesn't cover —
    the full Graph reference is at https://learn.microsoft.com/graph/api/overview.
    """
    return get_client().request(method, path, params=query_params, json_body=body)


# --- Dedicated convenience tools (most common Teams operations) --------


@mcp.tool()
def list_channels(team_id: str) -> dict[str, Any]:
    """List channels in a Team."""
    return get_client().request("GET", f"/teams/{team_id}/channels")


@mcp.tool()
def send_channel_message(team_id: str, channel_id: str, content: str) -> dict[str, Any]:
    """Post a message to a Teams channel. `content` may be plain text or HTML."""
    return get_client().request(
        "POST",
        f"/teams/{team_id}/channels/{channel_id}/messages",
        json_body={"body": {"content": content}},
    )


@mcp.tool()
def list_calendar_events(user_id: str, top: int = 25) -> dict[str, Any]:
    """List upcoming calendar events for a user (by id or userPrincipalName)."""
    return get_client().request(
        "GET",
        f"/users/{user_id}/calendar/events",
        params={"$top": top, "$orderby": "start/dateTime"},
    )


@mcp.tool()
def get_meeting_transcript(user_id: str, meeting_id: str, transcript_id: str) -> dict[str, Any]:
    """Fetch a Teams meeting transcript's content (VTT format)."""
    return get_client().request(
        "GET",
        f"/users/{user_id}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content",
    )


@mcp.tool()
def copilot_retrieval_query(
    query_text: str,
    data_source: str,
    filter_expression: str | None = None,
    connection_id: str | None = None,
    maximum_number_of_results: int = 25,
) -> dict[str, Any]:
    """Query the M365 Copilot Retrieval API for grounding content.

    NOT CURRENTLY USABLE: this Graph endpoint explicitly does not support
    application (client-credentials) permissions — only delegated
    (signed-in-user) auth works, per
    https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/copilotroot-retrieval.
    This server only implements app-only auth (see graph_client.py), so this
    tool always raises before making a network call. It's kept registered
    (rather than removed) so the schema stays correct and ready once
    delegated auth is added as a separate feature.

    query_text: search string, max 1,500 chars (queryString).
    data_source: one of "sharePoint", "oneDriveBusiness", "externalItem" —
        exactly one source per call, no interleaving.
    filter_expression: optional KQL scoping (e.g. path, file type, author,
        date range).
    connection_id: optional Copilot connector connection id, used when
        data_source="externalItem" (maps to
        dataSourceConfiguration.externalItem.connections[].connectionId).
    maximum_number_of_results: capped at 25 by the API.
    """
    raise NotImplementedError(
        "copilot_retrieval_query requires delegated (signed-in-user) Graph auth — "
        "the Retrieval API explicitly does not support application/client-credentials "
        "permissions (Microsoft Learn: 'Application: Not supported'). This server only "
        "implements app-only auth. Adding delegated auth (device-code flow, token "
        "caching) is tracked as separate follow-up work, not yet built."
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
