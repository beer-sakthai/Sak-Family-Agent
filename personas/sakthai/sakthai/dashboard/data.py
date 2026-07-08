"""Dashboard data collection module for SakThai and ServiceQuoteBot."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..memory.store import MemoryStore

logger = logging.getLogger(__name__)


def _parse_team_roster() -> list[dict[str, str]]:
    """Parse the team roster dynamically from docs/SOUL.md."""
    try:
        repo_root = Path(__file__).resolve().parents[4]
        soul_path = repo_root / "docs" / "SOUL.md"
        if not soul_path.exists():
            return []

        content = soul_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        roster = []
        in_table = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "| Agent | Handle | Role | Model |" in line:
                in_table = True
                continue
            if in_table:
                if line.startswith("|---") or line.startswith("| :---") or line.startswith("|:---"):
                    continue
                if not line.startswith("|"):
                    in_table = False
                    continue
                # Parse row
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 4:
                    agent = parts[0].replace("**", "")
                    handle = parts[1].replace("`", "")
                    role = parts[2]
                    model = parts[3].replace("`", "")
                    roster.append({"agent": agent, "handle": handle, "role": role, "model": model})
        return roster
    except Exception as e:
        logger.warning("Failed to parse team roster from SOUL.md: %s", e)
        return []


def collect_dashboard_data(days: int = 30) -> dict[str, Any]:
    """Collect KPI and timeline metrics for both SakKing OS and ServiceQuoteBot."""
    now_ts = int(time.time())
    period_ago_ts = now_ts - (days * 86400)
    seven_days_ago_ts = now_ts - (7 * 86400)

    try:
        with MemoryStore() as store:
            # 1. Base SakKing OS KPIs (Facts & Observations count)
            # Fetch facts
            all_facts = store.list_facts(limit=1000)
            all_obs = store.top_observations(limit=200)

            db_stats = store.stats()
            total_facts = db_stats["facts"]["total"]
            total_obs = db_stats["observations"]["total"]

            facts_delta = sum(1 for f in all_facts if f.created_at >= seven_days_ago_ts)
            obs_delta = sum(1 for o in all_obs if o.created_at >= seven_days_ago_ts)

            # Filtering recent general facts (exclude lead and revenue kinds to avoid noise)
            recent_general = [
                {"id": f.id, "kind": f.kind, "value": f.value, "key": f.key}
                for f in all_facts
                if f.kind not in ("lead", "revenue")
            ][:10]

            top_obs = [
                {
                    "id": o.id,
                    "label": o.summary,
                    "value": f"Weight: {o.weight:.2f}, Conf: {o.confidence:.2f}",
                }
                for o in all_obs
            ][:10]

            # 2. ServiceQuoteBot KPIs
            lead_facts = [f for f in all_facts if f.kind == "lead"]
            revenue_facts = [f for f in all_facts if f.kind == "revenue"]

            # Parse lead facts
            leads_list = []
            for lf in lead_facts:
                try:
                    payload = json.loads(lf.value)
                    if not isinstance(payload, dict):
                        payload = {"query": str(payload)}
                except (TypeError, ValueError):
                    payload = {"query": lf.value}
                payload["id"] = lf.id
                payload["date"] = datetime.fromtimestamp(lf.created_at, UTC).strftime("%Y-%m-%d")
                leads_list.append(payload)

            # Parse revenue facts
            revenue_list = []
            total_revenue = 0.0
            mrr = 0.0

            for rf in revenue_facts:
                try:
                    payload = json.loads(rf.value)
                except (TypeError, ValueError):
                    # Fallback if key/value are not JSON
                    payload = {
                        "client": rf.key or "Unknown",
                        "amount": 0.0,
                        "type": "setup",
                        "date": "",
                    }

                amount = float(payload.get("amount") or 0.0)
                payload["id"] = rf.id

                # Use value date, default to created_at
                date_str = payload.get("date") or datetime.fromtimestamp(
                    rf.created_at, UTC
                ).strftime("%Y-%m-%d")
                payload["date"] = date_str
                payload["amount"] = amount

                revenue_list.append(payload)
                total_revenue += amount

                # MRR logic: subscription/monthly revenue in the last 30 days
                # Or simply sum all active monthly subscriptions
                rev_type = payload.get("type", "setup").lower()
                if rev_type in ("monthly", "subscription"):
                    # Check if within last 30 days
                    try:
                        f_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if datetime.now() - f_date <= timedelta(days=30):
                            mrr += amount
                    except Exception:
                        # Fallback to created_at check
                        if now_ts - rf.created_at <= 30 * 86400:
                            mrr += amount

            # Lead Conversion Rate logic
            # Match lead contacts to revenue clients
            converted_leads_count = 0
            for lead in leads_list:
                lead_name = lead.get("name", "").strip().lower()
                lead_email = lead.get("email", "").strip().lower()
                lead_phone = lead.get("phone", "").strip().lower()

                matched = False
                for rev in revenue_list:
                    rev_client = rev.get("client", "").strip().lower()
                    if not rev_client:
                        continue
                    # Match on name, or email username, or if name is in client name
                    if (lead_name and lead_name in rev_client) or (rev_client in lead_name):
                        matched = True
                        break
                    if lead_email and lead_email in rev_client:
                        matched = True
                        break
                    if lead_phone and lead_phone in rev_client:
                        matched = True
                        break

                lead["converted"] = matched
                if matched:
                    converted_leads_count += 1

            total_leads = len(leads_list)
            conversion_rate = (
                (converted_leads_count / total_leads * 100.0) if total_leads > 0 else 0.0
            )

            # Revenue Growth Timeline
            # Sort revenue by date
            sorted_rev = sorted(revenue_list, key=lambda r: r.get("date", ""))
            timeline_labels = []
            timeline_values = []
            cumulative = 0.0

            # Group by date to show a clean cumulative progression
            date_groups: dict[str, float] = {}
            for rev in sorted_rev:
                d = rev.get("date", "Unknown")
                date_groups[d] = date_groups.get(d, 0.0) + rev["amount"]

            for d in sorted(date_groups.keys()):
                cumulative += date_groups[d]
                timeline_labels.append(d)
                timeline_values.append(cumulative)

            team_roster = _parse_team_roster()

            return {
                "generated_at": datetime.now(UTC).isoformat(),
                "source": "database",
                "kpis": {
                    "total_facts": total_facts,
                    "total_facts_delta": facts_delta,
                    "total_observations": total_obs,
                    "total_observations_delta": obs_delta,
                },
                "growth": {"labels": [], "facts": [], "observations": []},
                "recent_facts": recent_general,
                "top_observations": top_obs,
                "team_roster": team_roster,
                "servicequotebot": {
                    "total_revenue": total_revenue,
                    "mrr": mrr,
                    "total_leads": total_leads,
                    "conversion_rate": round(conversion_rate, 1),
                    "recent_leads": leads_list[:20],
                    "recent_revenue": revenue_list[:20],
                    "revenue_growth": {
                        "labels": timeline_labels,
                        "values": timeline_values,
                    },
                },
            }

    except Exception as e:
        logger.warning("Error fetching dashboard stats: %s", e, exc_info=True)
        # Return fallback stub
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "source": "fallback_stub",
            "kpis": {
                "total_facts": 0,
                "total_facts_delta": 0,
                "total_observations": 0,
                "total_observations_delta": 0,
            },
            "growth": {"labels": [], "facts": [], "observations": []},
            "recent_facts": [],
            "top_observations": [],
            "team_roster": [],
            "servicequotebot": {
                "total_revenue": 0.0,
                "mrr": 0.0,
                "total_leads": 0,
                "conversion_rate": 0.0,
                "recent_leads": [],
                "recent_revenue": [],
                "revenue_growth": {
                    "labels": [],
                    "values": [],
                },
            },
        }
