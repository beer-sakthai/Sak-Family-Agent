"""The dashboard data layer (snapshot builder for the React dashboard UI)."""

from __future__ import annotations

from .data import collect_dashboard_data, export_dashboard_json

__all__ = ["collect_dashboard_data", "export_dashboard_json"]
