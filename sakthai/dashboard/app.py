"""SakThai dashboard — a Streamlit view of the memory store.

Run via ``sakthai dashboard`` (recommended) or directly with
``streamlit run sakthai/dashboard/app.py``. Reads live data from the memory DB
and falls back to a small demo sample when the store is empty.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sakthai.config import memory_db_path
from sakthai.dashboard.data import SOURCE_DEMO, collect_dashboard_data


def _kpi_row(kpis: dict[str, Any]) -> None:
    left, right = st.columns(2)
    left.metric("Facts", kpis["total_facts"], delta=f"+{kpis['total_facts_delta']} this week")
    right.metric(
        "Observations",
        kpis["total_observations"],
        delta=f"+{kpis['total_observations_delta']} this week",
    )


def _growth_chart(growth: dict[str, Any]) -> None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=growth["labels"], y=growth["facts"], name="Facts", mode="lines"))
    fig.add_trace(
        go.Scatter(x=growth["labels"], y=growth["observations"], name="Observations", mode="lines")
    )
    fig.update_layout(
        title="Cumulative memory growth",
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=320,
        legend={"orientation": "h"},
    )
    st.plotly_chart(fig, use_container_width=True)


def _category_chart(categories: list[dict[str, Any]]) -> None:
    if not categories:
        return
    fig = go.Figure(
        go.Bar(
            x=[c["count"] for c in categories],
            y=[c["name"] for c in categories],
            orientation="h",
            marker_color=[c["color"] for c in categories],
        )
    )
    fig.update_layout(
        title="By category",
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=320,
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.set_page_config(layout="wide", page_title="SakThai Dashboard")
    data = collect_dashboard_data(memory_db_path())

    st.title("SakThai — Memory Dashboard")
    if data["source"] == SOURCE_DEMO:
        st.info('Memory is empty — showing demo data. Try `sakthai learn "..."`.')
    else:
        st.caption(f"Live data · generated {data['generated_at']}")

    _kpi_row(data["kpis"])

    left, right = st.columns(2)
    with left:
        _growth_chart(data["growth"])
    with right:
        _category_chart(data["categories"])

    st.subheader("Recent facts")
    if data["recent_facts"]:
        st.dataframe(pd.DataFrame(data["recent_facts"]), use_container_width=True, hide_index=True)
    else:
        st.write("No facts yet.")

    st.subheader("Top observations")
    if data["top_observations"]:
        st.dataframe(
            pd.DataFrame(data["top_observations"]), use_container_width=True, hide_index=True
        )
    else:
        st.write("No observations yet.")


if __name__ == "__main__":
    main()
