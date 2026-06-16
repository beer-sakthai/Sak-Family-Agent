"""SakThai dashboard — a multi-page Streamlit view of the agent and its memory.

Run via ``sakthai dashboard`` (recommended) or directly with
``streamlit run sakthai/dashboard/app.py``.

The app reads a live snapshot from the SQLite memory store (falling back to a
small demo sample when the store is empty) and presents seven pages: Overview,
Chat & Reasoning, Memory Explorer, Evolution, Agent Activity, Integrations &
Settings, and Skills. The Chat page drives ``sakthai.agent.loop.run_agent``
against the configured provider when credentials are present.

This module is presentation glue: all testable data logic lives in
``sakthai.dashboard.data``. mypy is loosened here (see ``pyproject.toml``) and
coverage omits it; a guarded smoke test exercises the figure builders.
"""

from __future__ import annotations

import datetime
import hashlib
import itertools
import math
import os
import sqlite3
import time
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sakthai.config import memory_db_path
from sakthai.dashboard.data import (
    _KIND_COLORS,
    SOURCE_DEMO,
    SOURCE_LIVE,
    collect_dashboard_data,
    collect_session_data,
)

# Repository the Overview page reports live metrics for, when a token is given.
_GITHUB_REPO = "beer-sakthai/sakthai-agent-v2"

st.set_page_config(
    layout="wide",
    page_title="SakThai-Agent Dashboard",
    initial_sidebar_state="expanded",
)


# ── Theme ────────────────────────────────────────────────────────────────────
# Targets stable [data-testid] selectors rather than hashed .css-* class names,
# which change between Streamlit releases.
_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [data-testid="stApp"] { font-family: 'Inter', sans-serif; }

/* Sidebar — glassmorphism */
[data-testid="stSidebar"] {
    background: rgba(10, 12, 16, 0.6) !important;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
[data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.05); }

/* Headings */
h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    background: linear-gradient(to right, #ffffff, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
}
.subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    margin-bottom: 1.6rem;
    line-height: 1.6;
}

/* Cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(13, 17, 23, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: transform 0.3s ease, border-color 0.3s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-2px);
    border-color: rgba(168, 85, 247, 0.2) !important;
}

/* Metrics */
[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #ffffff;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.03);
}

/* Chat avatars */
[data-testid="chatAvatarIcon-user"] {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
}
[data-testid="chatAvatarIcon-assistant"] {
    background: linear-gradient(135deg, #a855f7, #7c3aed) !important;
}

/* Reasoning box + tool badges */
.reasoning-box {
    background: linear-gradient(145deg, rgba(15, 17, 23, 0.8), rgba(10, 12, 16, 0.9));
    border: 1px solid rgba(168, 85, 247, 0.15);
    border-left: 3px solid #a855f7;
    border-radius: 14px;
    padding: 18px;
    margin-top: 16px;
    line-height: 1.6;
}
.tool-badge {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 18px;
    padding: 5px 12px;
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', monospace;
    display: inline-block;
    margin: 0 8px 8px 0;
    color: #e2e8f0;
}

/* Status dot */
.status-dot {
    display: inline-block;
    width: 11px;
    height: 11px;
    background-color: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 12px #10b981;
    margin-right: 10px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.1) !important;
}

/* Mobile */
@media (max-width: 768px) {
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { padding: 16px !important; }
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
    h1 { font-size: 1.5rem !important; }
}
</style>
"""

_LIGHT_OVERRIDE_CSS = """
<style>
body, [data-testid="stApp"] { background-color: #f8fafc !important; color: #0f172a !important; }
[data-testid="stSidebar"] {
    background: rgba(248, 250, 252, 0.98) !important;
    border-right: 1px solid rgba(0, 0, 0, 0.08) !important;
}
[data-testid="stSidebar"] * { color: #1e293b !important; }
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.8) !important;
    border-color: rgba(0, 0, 0, 0.08) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
}
h1, h2, h3 {
    background: linear-gradient(to right, #0f172a, #334155) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}
.subtitle { color: #475569 !important; }
[data-testid="stMetricValue"] { color: #0f172a !important; }
</style>
"""


# ── Cached data sources ──────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def _cached_dashboard_data() -> dict[str, Any]:
    """Live memory snapshot, refreshed every 30s."""
    return collect_dashboard_data(memory_db_path())


@st.cache_data(ttl=30, show_spinner=False)
def _cached_session_data() -> dict[str, Any]:
    """Agent session-log snapshot, refreshed every 30s."""
    return collect_session_data()


def _token_fingerprint(token: str) -> str:
    """Stable, non-reversible cache key for a token (or "anonymous")."""
    if not token:
        return "anonymous"
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


@st.cache_data(ttl=300, show_spinner=False)
def _github_snapshot(token_fingerprint: str, token: str) -> dict[str, Any]:
    """Cached repository metadata, keyed on a token fingerprint so rotating the
    token invalidates the cache without leaking the secret into the cache key."""
    del token_fingerprint  # only used to key the cache
    from github import Github  # type: ignore[import-untyped]

    gh = Github(token) if token else Github()
    repo = gh.get_repo(_GITHUB_REPO)
    commits = []
    for commit in itertools.islice(repo.get_commits(), 5):
        author = commit.commit.author
        message = commit.commit.message or ""
        commits.append(
            {
                "Date": (author.date.strftime("%Y-%m-%d %H:%M") if author and author.date else "—"),
                "Message": message.split("\n", 1)[0] if message else "No message",
                "Author": author.name if author else "Unknown",
            }
        )
    return {
        "stars": repo.stargazers_count,
        "open_issues": repo.open_issues_count,
        "forks": repo.forks_count,
        "subscribers": repo.subscribers_count,
        "description": repo.description or "No description provided.",
        "commits": commits,
    }


# ── Notifications ────────────────────────────────────────────────────────────
def _notify(message: str) -> None:
    """Append a timestamped notification to the session queue (capped at 20)."""
    notes: list[dict[str, str]] = st.session_state.get("notifications", [])
    notes.append({"msg": message, "ts": datetime.datetime.now().strftime("%H:%M:%S")})
    st.session_state["notifications"] = notes[-20:]


# ── Pages ────────────────────────────────────────────────────────────────────
def _render_overview(data: dict[str, Any], token: str) -> None:
    st.header("Project Overview")
    st.markdown(
        f'<p class="subtitle">Platform metrics and live integration status — '
        f"<b>{data['source']}</b> snapshot at {data['generated_at']}.</p>",
        unsafe_allow_html=True,
    )

    kpis = data["kpis"]
    graph = data["graph"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Total Facts",
        kpis["total_facts"],
        delta=(f"+{kpis['total_facts_delta']} this week" if kpis["total_facts_delta"] else None),
    )
    c2.metric(
        "Observations",
        kpis["total_observations"],
        delta=(
            f"+{kpis['total_observations_delta']} this week"
            if kpis["total_observations_delta"]
            else None
        ),
    )
    c3.metric("Knowledge Nodes", graph["total_nodes"])
    c4.metric("Connections", graph["connections"])

    st.subheader("Memory Growth")
    growth_df = pd.DataFrame(
        {
            "date": data["growth"]["labels"],
            "facts": data["growth"]["facts"],
            "observations": data["growth"]["observations"],
        }
    )
    fig = px.line(
        growth_df.melt(id_vars="date", var_name="series", value_name="count"),
        x="date",
        y="count",
        color="series",
        color_discrete_map={"facts": "#a855f7", "observations": "#22d3ee"},
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#cbd5e1"},
        height=300,
        margin={"t": 10, "b": 0, "l": 0, "r": 0},
        legend_title_text="",
    )
    st.plotly_chart(fig, use_container_width=True)

    if not token:
        st.info(f"Add a GitHub token in the sidebar to see live metrics for `{_GITHUB_REPO}`.")
        return

    try:
        with st.spinner("Connecting to GitHub..."):
            snap = _github_snapshot(_token_fingerprint(token), token)
    except Exception as exc:  # noqa: BLE001 — surface any GitHub/network failure
        st.error(f"Could not load GitHub data: {exc}")
        return

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Stars", snap["stars"])
    g2.metric("Open Issues", snap["open_issues"])
    g3.metric("Forks", snap["forks"])
    g4.metric("Watchers", snap["subscribers"])

    st.subheader("Repository Description")
    st.info(snap["description"])

    st.subheader("Recent Commits")
    if snap["commits"]:
        st.dataframe(pd.DataFrame(snap["commits"]), use_container_width=True, hide_index=True)
    else:
        st.write("No recent commits found.")


def _run_chat_turn(prompt: str, tool_slot: Any) -> str:
    """Dispatch one chat turn through the local agent loop, rendering tool badges
    into ``tool_slot``. Returns the assistant's text."""
    from sakthai.agent.loop import AgentError, run_agent
    from sakthai.memory.store import MemoryStore

    try:
        store = MemoryStore(memory_db_path())
    except (OSError, sqlite3.Error) as exc:
        return f":warning: Could not open memory store: {exc}"

    try:
        result = run_agent(prompt, store=store)
    except AgentError as exc:
        return f":warning: Agent unavailable: {exc}"
    finally:
        store.close()

    if result.tool_calls:
        badges = "".join(
            f'<span class="tool-badge">{call.get("name", "tool")}</span>'
            for call in result.tool_calls
        )
        tool_slot.markdown(
            f'<div class="reasoning-box"><b style="color:#c4b5fd;">Tools used</b><br>{badges}</div>',
            unsafe_allow_html=True,
        )
    return result.text


def _render_chat(data: dict[str, Any]) -> None:
    st.header("Chat with SakThai")
    st.markdown(
        '<p class="subtitle">Conversational agent with persistent memory and tool use.</p>',
        unsafe_allow_html=True,
    )

    chat_col, reason_col = st.columns([2.5, 1.5], gap="large")

    with chat_col:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if prompt := st.chat_input("Ask me anything..."):
            st.chat_message("user").write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("assistant"):
                tool_slot = st.empty()
                with st.spinner("Thinking..."):
                    response = _run_chat_turn(prompt, tool_slot)
                st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    with reason_col:
        st.subheader("Thought Process")
        steps_html: list[str] = []
        for group in data["chat"]["thought_process"]:
            details = "".join(f"<div style='color:#94a3b8;'>• {s}</div>" for s in group["steps"])
            steps_html.append(
                f"<div style='margin-bottom:14px;'>"
                f"<b style='color:#e2e8f0;'>{group['group']}</b>{details}</div>"
            )
        confidence = data["chat"]["confidence"]
        st.markdown(
            f"""
            <div style="background:rgba(13,17,23,0.5); padding:18px; border-radius:14px;
                        border:1px solid rgba(255,255,255,0.06);">
                {"".join(steps_html)}
                <hr style="border-color:rgba(255,255,255,0.08); margin:16px 0;">
                <p style="margin:0 0 8px; color:#e2e8f0; font-weight:600;">Context Confidence</p>
                <h2 style="margin:0; color:#10b981;">{confidence}%</h2>
                <div style="width:100%; background:#1e293b; border-radius:6px; height:8px; margin-top:8px;">
                    <div style="width:{confidence}%; height:100%; border-radius:6px;
                                background:linear-gradient(90deg,#3b82f6,#10b981);"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_knowledge_graph(graph: dict[str, Any]) -> None:
    categories = graph["categories"] or []
    nodes_x, nodes_y = [0.0], [0.0]
    labels = ["Core"]
    colors = ["#7c3aed"]
    for i, cat in enumerate(categories):
        angle = 2 * math.pi * i / max(len(categories), 1)
        nodes_x.append(math.cos(angle))
        nodes_y.append(math.sin(angle))
        labels.append(cat["name"])
        colors.append(cat.get("color") or _KIND_COLORS.get(cat["name"].lower(), "#3b82f6"))

    fig = go.Figure()
    for i in range(1, len(nodes_x)):
        fig.add_trace(
            go.Scatter(
                x=[nodes_x[0], nodes_x[i]],
                y=[nodes_y[0], nodes_y[i]],
                mode="lines",
                line={"color": "#2d2b4a", "width": 2},
                hoverinfo="none",
                showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=nodes_x,
            y=nodes_y,
            mode="markers+text",
            text=labels,
            textposition="bottom center",
            marker={
                "size": [30 if i == 0 else 20 for i in range(len(nodes_x))],
                "color": colors,
                "line": {"width": 2, "color": "white"},
            },
            textfont={"color": "#cbd5e1"},
            showlegend=False,
        )
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_memory(data: dict[str, Any]) -> None:
    st.header("Memory Explorer")
    st.markdown(
        f'<p class="subtitle">Facts and observations from the memory store '
        f"({data['source']} data).</p>",
        unsafe_allow_html=True,
    )

    search_col, kind_col = st.columns([2, 1])
    search_q = search_col.text_input("🔍 Search memory", placeholder="keyword…", key="mem_search")
    all_kinds = sorted(
        {f.get("kind", "note") for f in data["recent_facts"]}
        | {"note", "pref", "fact", "project", "profile", "skill"}
    )
    kind_filter = kind_col.multiselect("Filter by kind", all_kinds, default=[], key="mem_kinds")

    mem_col, graph_col = st.columns([1.5, 1], gap="large")

    with mem_col:
        live_store = None
        try:
            from sakthai.memory.store import MemoryStore

            live_store = MemoryStore(memory_db_path())
        except (OSError, sqlite3.Error):
            live_store = None

        st.subheader("Recent Facts")
        is_live = data["source"] == SOURCE_LIVE
        if search_q and live_store is not None:
            raw_facts, _ = live_store.search_memory(search_q, limit=50)
            facts_to_show = [
                {
                    "id": f.id,
                    "kind": f.kind,
                    "key": f.key or "",
                    "value": f.value,
                    "created": str(f.created_at),
                }
                for f in raw_facts
            ]
        else:
            facts_to_show = list(data["recent_facts"])
        if kind_filter:
            facts_to_show = [f for f in facts_to_show if f["kind"] in kind_filter]

        if facts_to_show:
            st.caption(f"{len(facts_to_show)} fact(s) shown")
            for fact in facts_to_show:
                fact_id = fact.get("id")
                label = f"[{fact['kind']}] {fact.get('key') or ''}: {fact['value'][:70]}"
                with st.expander(label, expanded=False):
                    st.caption(f"Created: {fact.get('created', '')}  |  ID: {fact_id}")
                    if is_live and fact_id is not None and live_store is not None:
                        new_val = st.text_area(
                            "Value", value=fact["value"], key=f"edit_val_{fact_id}"
                        )
                        save_col, del_col = st.columns(2)
                        if save_col.button("💾 Save", key=f"save_{fact_id}"):
                            try:
                                live_store.update_fact(int(fact_id), value=str(new_val))
                                _cached_dashboard_data.clear()
                                _notify(f"Fact #{fact_id} updated.")
                                st.toast(f"Fact #{fact_id} saved!", icon="✅")
                                time.sleep(0.4)
                                st.rerun()
                            except (ValueError, sqlite3.Error) as exc:
                                st.error(str(exc))
                        if del_col.button("🗑 Delete", key=f"del_{fact_id}"):
                            if st.session_state.get(f"confirm_del_{fact_id}"):
                                live_store.forget_fact(int(fact_id))
                                _cached_dashboard_data.clear()
                                st.session_state.pop(f"confirm_del_{fact_id}", None)
                                _notify(f"Fact #{fact_id} deleted.")
                                st.toast(f"Fact #{fact_id} deleted.", icon="🗑️")
                                time.sleep(0.4)
                                st.rerun()
                            else:
                                st.session_state[f"confirm_del_{fact_id}"] = True
                                st.warning("Click Delete again to confirm.")
                    else:
                        st.text_area(
                            "Value",
                            value=fact["value"],
                            key=f"view_val_{fact_id or label}",
                            disabled=True,
                        )
        else:
            st.info('No facts yet. Run `sakthai learn "..."` to add some.')

        if live_store is not None:
            live_store.close()

        st.subheader("Top Observations")
        if data["top_observations"]:
            obs_df = pd.DataFrame(data["top_observations"]).rename(
                columns={"summary": "Observation", "weight": "Weight"}
            )
            st.dataframe(obs_df, use_container_width=True, hide_index=True)
        else:
            st.info("No observations yet.")

    with graph_col, st.container(border=True):
        st.subheader("Knowledge Graph")
        graph = data["graph"]
        _render_knowledge_graph(graph)
        a, b, c = st.columns(3)
        a.metric("Nodes", graph["total_nodes"])
        b.metric("Connections", graph["connections"])
        c.metric("Categories", len(graph["categories"]))


def _render_evolution(data: dict[str, Any]) -> None:
    evolution = data["evolution"]
    st.header("Evolution")
    st.markdown(
        '<p class="subtitle">Self-improvement across iterations of the evolution cycle.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Version", evolution["current_version"])
    c2.metric("Performance Gain", evolution["performance_gain"])
    c3.metric("Evolution Runs", evolution["runs"])
    c4.metric("Success Rate", f"{evolution['success_rate']}%")

    hist_col, charts_col = st.columns([1, 1.5], gap="large")

    with hist_col:
        st.subheader("Evolution History")
        rows: list[str] = []
        for entry in evolution["history"]:
            badge = (
                '<span style="background:#7c3aed; padding:2px 6px; border-radius:4px; '
                'font-size:0.7em; margin-right:6px;">LATEST</span>'
                if entry.get("latest")
                else ""
            )
            rows.append(
                '<div style="display:flex; justify-content:space-between; margin-bottom:12px; '
                'border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:8px;">'
                f"<div>{badge}<b>{entry['version']}</b> "
                f'<span style="color:#8b949e; font-size:0.85em;">{entry["date"]}</span></div>'
                f'<div style="color:#10b981; font-weight:bold;">{entry["success"]}%</div></div>'
            )
        st.markdown(
            '<div style="background:rgba(13,17,23,0.5); padding:16px; border-radius:14px; '
            f'border:1px solid rgba(255,255,255,0.06);">{"".join(rows)}</div>',
            unsafe_allow_html=True,
        )

    with charts_col:
        st.subheader("Before vs. After")
        ba = evolution["before_after"]["accuracy"]
        df_acc = pd.DataFrame(
            {"Version": ["Before", "After"], "Accuracy (%)": [ba["before"], ba["after"]]}
        )
        fig_acc = px.bar(
            df_acc,
            x="Version",
            y="Accuracy (%)",
            color="Version",
            color_discrete_sequence=["#3b2b5a", "#3b82f6"],
            text_auto=".1f",
        )
        fig_acc.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#cbd5e1"},
            showlegend=False,
            height=250,
            margin={"t": 10, "b": 0, "l": 0, "r": 0},
        )
        st.plotly_chart(fig_acc, use_container_width=True)

        with st.container(border=True):
            st.write("**Neural Optimization**")
            st.caption("Active optimization paths")
            for focus in evolution["neural_focus"][:3]:
                st.write(focus["name"])
                st.progress(int(focus["pct"]))


def _render_activity() -> None:
    st.header("Agent Activity")
    st.markdown(
        '<p class="subtitle">Token usage and run history from the agent session logs.</p>',
        unsafe_allow_html=True,
    )
    sessions = _cached_session_data()
    if sessions["source"] != SOURCE_LIVE:
        st.info('No agent runs recorded yet. Run `sakthai run "..."` to populate this page.')

    totals = sessions["totals"]
    s1, s2, s3 = st.columns(3)
    s1.metric("Sessions", totals["sessions"])
    s2.metric("Total Tokens", totals["total_tokens"])
    s3.metric("Output Tokens", totals["output_tokens"])

    left, right = st.columns(2, gap="large")
    with left:
        by_day = sessions["by_day"]
        if by_day["labels"]:
            fig = go.Figure(
                go.Bar(x=by_day["labels"], y=by_day["sessions"], marker_color="#3b82f6")
            )
            fig.update_layout(
                title="Sessions per day",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "#cbd5e1"},
                height=300,
                margin={"t": 40, "b": 10, "l": 10, "r": 10},
            )
            st.plotly_chart(fig, use_container_width=True)
    with right:
        by_model = sessions["by_model"]
        if by_model:
            fig = go.Figure(
                go.Bar(
                    x=[m["total_tokens"] for m in by_model],
                    y=[m["model"] for m in by_model],
                    orientation="h",
                    marker_color="#a855f7",
                )
            )
            fig.update_layout(
                title="Tokens by model",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "#cbd5e1"},
                height=300,
                margin={"t": 40, "b": 10, "l": 10, "r": 10},
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Sessions")
    if sessions["recent_sessions"]:
        st.dataframe(
            pd.DataFrame(sessions["recent_sessions"]), use_container_width=True, hide_index=True
        )
    else:
        st.write('No agent sessions yet. Run `sakthai run "..."`.')


def _render_settings(token: str) -> None:
    st.header("Integrations & Settings")
    st.markdown(
        '<p class="subtitle">Manage external connections and run diagnostics.</p>',
        unsafe_allow_html=True,
    )

    st.subheader("API Configuration")
    st.text_input("GitHub Token", type="password", value=token, disabled=True, key="settings_token")
    st.caption("Set the token in the sidebar; it is held only for this session.")

    st.subheader("Memory Export / Import")
    exp_col, imp_col = st.columns(2)

    with exp_col:
        st.markdown("**Export Memory**")
        fmt = st.selectbox("Format", ["json", "csv", "jsonl"], key="export_fmt")
        if st.button("Prepare Export", use_container_width=True, key="export_btn"):
            import json as _json

            from sakthai.memory.store import MemoryStore, snapshot_to_csv, snapshot_to_jsonl

            try:
                with MemoryStore(memory_db_path()) as store:
                    snap = store.export_to_dict()
                if fmt == "json":
                    payload = _json.dumps(snap, indent=2, ensure_ascii=False).encode("utf-8")
                    mime, filename = "application/json", "sakthai_memory.json"
                elif fmt == "csv":
                    payload = snapshot_to_csv(snap).encode("utf-8")
                    mime, filename = "text/csv", "sakthai_memory.csv"
                else:
                    payload = snapshot_to_jsonl(snap).encode("utf-8")
                    mime, filename = "application/x-ndjson", "sakthai_memory.jsonl"
                st.download_button(
                    f"⬇ Download {filename}",
                    data=payload,
                    file_name=filename,
                    mime=mime,
                    key="export_dl_btn",
                )
                _notify(f"Memory exported as {fmt.upper()}.")
            except Exception as exc:  # noqa: BLE001 — report any export failure inline
                st.error(f"Export failed: {exc}")

    with imp_col:
        st.markdown("**Import Memory**")
        replace_mode = st.checkbox("Replace existing data (destructive)", key="import_replace")
        uploaded = st.file_uploader("Upload JSON snapshot", type=["json"], key="import_file")
        if uploaded is not None and st.button("Import", use_container_width=True, key="import_btn"):
            import json as _json

            from sakthai.memory.store import MemoryStore

            try:
                raw = _json.loads(uploaded.read())
                mode = "replace" if replace_mode else "merge"
                with MemoryStore(memory_db_path()) as store:
                    n_facts, n_obs = store.import_from_dict(raw, mode=mode)
                _cached_dashboard_data.clear()
                st.success(f"Imported {n_facts} facts and {n_obs} observations ({mode} mode).")
                _notify(f"Imported {n_facts} facts, {n_obs} obs ({mode}).")
                st.rerun()
            except Exception as exc:  # noqa: BLE001 — report any import failure inline
                st.error(f"Import failed: {exc}")

    st.subheader("System Diagnostics")
    if st.button("Run Doctor"):
        from sakthai.config import check_env

        report = check_env()
        if report.get("ready"):
            st.success("System ready")
        else:
            st.warning("Some checks need attention")
        st.json(report)


def _render_skills(catalog: list[dict[str, Any]]) -> None:
    st.header("Skill Library")
    total = sum(g["count"] for g in catalog)
    st.markdown(
        f'<p class="subtitle">{total} skills across {len(catalog)} categories — from the local '
        "<code>skills/</code> directory and the curated <code>library/</code>.</p>",
        unsafe_allow_html=True,
    )
    if not catalog:
        st.info("No skills found.")
        return

    categories = [g["category"] for g in catalog]
    chosen = st.multiselect("Filter by category", categories, default=[])
    query = st.text_input("Search skills", placeholder="name, tag, or keyword…").strip().lower()

    for group in catalog:
        if chosen and group["category"] not in chosen:
            continue
        skills_in = group["skills"]
        if query:
            skills_in = [
                s
                for s in skills_in
                if query in str(s["name"]).lower()
                or query in str(s["description"] or "").lower()
                or any(query in str(t).lower() for t in s["tags"])
            ]
        if not skills_in:
            continue

        st.subheader(f"{group['category'].title()}  ·  {len(skills_in)}")
        cols = st.columns(3)
        for i, skill in enumerate(skills_in):
            with cols[i % 3]:
                desc = (skill["description"] or "").replace("\n", " ").strip()
                if len(desc) > 140:
                    desc = desc[:139] + "…"
                desc_html = desc or '<em style="color:#64748b">No description.</em>'
                source_color = "#10b981" if skill.get("source") == "skills" else "#a855f7"
                tags_html = "".join(
                    f'<span style="font-size:0.7em; background:rgba(59,130,246,0.12); '
                    "color:#93c5fd; border:1px solid rgba(59,130,246,0.25); border-radius:10px; "
                    f'padding:2px 7px; margin:2px 2px 0 0; display:inline-block;">{t}</span>'
                    for t in skill["tags"][:5]
                )
                ver_badge = (
                    '<span style="font-size:0.68em; background:rgba(168,85,247,0.15); '
                    "color:#d8b4fe; border:1px solid rgba(168,85,247,0.3); border-radius:6px; "
                    f'padding:2px 7px; margin-left:6px;">v{skill["version"]}</span>'
                    if skill["version"]
                    else ""
                )
                st.markdown(
                    "<div style='background:linear-gradient(145deg,rgba(13,17,23,0.7),"
                    "rgba(15,20,30,0.5));border:1px solid rgba(168,85,247,0.15);"
                    f"border-top:2px solid {source_color};border-radius:16px;"
                    "padding:18px 16px 14px;margin-bottom:12px;'>"
                    f"<div style='font-weight:700;font-size:0.95rem;color:#e2e8f0;'>"
                    f"{skill['name']}{ver_badge}</div>"
                    f"<div style='font-size:0.82rem;color:#94a3b8;margin-top:6px;"
                    f"line-height:1.45;'>{desc_html}</div>"
                    f"<div style='margin-top:10px;'>{tags_html}</div></div>",
                    unsafe_allow_html=True,
                )


# ── Sidebar + chrome ─────────────────────────────────────────────────────────
def _render_sidebar(data: dict[str, Any]) -> tuple[str, str]:
    """Render the sidebar; return (selected_page, github_token)."""
    with st.sidebar:
        st.markdown(
            '<h2 style="margin:4px 0 0; text-align:center;">'
            '<span style="color:#a855f7;">SakThai</span>-Agent</h2>'
            '<p style="color:#8b949e; font-size:0.85em; text-align:center; margin:0 0 4px;">'
            "AI Agent Platform · v2</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        page = st.radio(
            "Navigation",
            [
                "Overview",
                "Chat & Reasoning",
                "Memory",
                "Evolution",
                "Agent Activity",
                "Integrations & Settings",
                "Skills",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.subheader("Settings & Connections")
        token = st.text_input(
            "GitHub Token",
            type="password",
            value=os.environ.get("GITHUB_TOKEN", ""),
            help="Required for live repository metrics.",
        )
        if st.button("Refresh Data", use_container_width=True):
            _cached_dashboard_data.clear()
            _cached_session_data.clear()
            _github_snapshot.clear()
            _notify("Dashboard data refreshed.")
            st.rerun()

        current_theme = st.session_state.get("theme", "dark")
        toggle_label = "☀️ Light Mode" if current_theme == "dark" else "🌙 Dark Mode"
        if st.button(toggle_label, use_container_width=True, key="theme_toggle"):
            st.session_state["theme"] = "light" if current_theme == "dark" else "dark"
            st.rerun()

        st.session_state["live_updates"] = st.toggle(
            "Live Updates (30s)",
            value=st.session_state.get("live_updates", True),
            key="live_updates_toggle",
        )

        st.markdown(
            f'<div style="margin-top:12px; padding:14px; border-radius:12px; '
            f'background:rgba(10,12,16,0.6); border:1px solid rgba(255,255,255,0.06);">'
            f'<span class="status-dot"></span>'
            f'<span style="font-weight:600; color:#22c55e;">System Online</span>'
            f'<div style="color:#64748b; font-size:0.75rem; margin-top:6px;">'
            f"{data['source']} · {data['generated_at']}</div></div>",
            unsafe_allow_html=True,
        )

        notes: list[dict[str, str]] = st.session_state.get("notifications", [])
        bell = f"🔔 Notifications ({len(notes)})" if notes else "🔔 Notifications"
        with st.expander(bell, expanded=False):
            if notes:
                for note in reversed(notes[-10:]):
                    st.caption(f"{note['ts']} — {note['msg']}")
                if st.button("Clear all", key="clear_notifs"):
                    st.session_state["notifications"] = []
                    st.rerun()
            else:
                st.caption("No notifications yet.")

    return page, token


def _inject_auto_refresh(enabled: bool, interval_s: int = 30) -> None:
    """Reload the page after ``interval_s`` seconds when live updates are on."""
    if not enabled:
        return
    st.markdown(
        f"""<script>
        (function() {{
            if (window.__sakRefreshTimer) clearTimeout(window.__sakRefreshTimer);
            window.__sakRefreshTimer = setTimeout(function() {{
                window.location.reload();
            }}, {interval_s * 1000});
        }})();
        </script>""",
        unsafe_allow_html=True,
    )


def main() -> None:
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"
    if "notifications" not in st.session_state:
        st.session_state["notifications"] = []

    st.markdown(_THEME_CSS, unsafe_allow_html=True)
    if st.session_state.get("theme") == "light":
        st.markdown(_LIGHT_OVERRIDE_CSS, unsafe_allow_html=True)

    data = _cached_dashboard_data()
    if data["source"] == SOURCE_DEMO:
        st.toast("Memory is empty — showing demo data.", icon="ℹ️")

    page, token = _render_sidebar(data)

    from sakthai.config import LIBRARY_DIR, SKILLS_DIR
    from sakthai.skills import build_catalog

    if page == "Overview":
        _render_overview(data, token)
    elif page == "Chat & Reasoning":
        _render_chat(data)
    elif page == "Memory":
        _render_memory(data)
    elif page == "Evolution":
        _render_evolution(data)
    elif page == "Agent Activity":
        _render_activity()
    elif page == "Integrations & Settings":
        _render_settings(token)
    elif page == "Skills":
        _render_skills(build_catalog(SKILLS_DIR, LIBRARY_DIR))

    _inject_auto_refresh(enabled=st.session_state.get("live_updates", True))


if __name__ == "__main__":
    main()
