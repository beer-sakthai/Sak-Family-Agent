from teams_copilot_mcp import catalog


def test_find_returns_matching_spec():
    spec = catalog.find("list_channels")
    assert spec.method == "GET"
    assert spec.path_template == "/teams/{team_id}/channels"


def test_find_returns_none_for_unknown_id():
    assert catalog.find("does_not_exist") is None


def test_search_matches_by_id_substring():
    results = catalog.search("meeting")
    ids = {spec.id for spec in results}
    assert "create_online_meeting" in ids
    assert "list_channels" not in ids


def test_search_matches_by_description_substring():
    # "ReadBasic" appears only in list_teams_in_org's description, not any id.
    results = catalog.search("ReadBasic")
    assert {spec.id for spec in results} == {"list_teams_in_org"}


def test_search_no_match_returns_empty_list():
    assert catalog.search("xyzzy_nonexistent_keyword_zzz") == []


def test_copilot_retrieval_query_requires_delegated_auth():
    spec = catalog.find("copilot_retrieval_query")
    assert spec.requires_delegated_auth is True


def test_most_actions_do_not_require_delegated_auth():
    spec = catalog.find("list_channels")
    assert spec.requires_delegated_auth is False
