"""The dashboard data layer (and Streamlit app, imported lazily)."""

from __future__ import annotations

from .data import collect_dashboard_data, export_dashboard_json

__all__ = ["collect_dashboard_data", "export_dashboard_json"]
