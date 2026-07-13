"""Script to load mock leads and revenue into SQLite memory.db for dashboard testing."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ensure sakthai package is in path
sys.path.insert(0, str((Path(__file__).resolve().parent.parent / "personas" / "sakthai").resolve()))
from sakthai.memory.store import MemoryStore


def load_mock_data():
    print("Opening MemoryStore...")
    with MemoryStore() as store:
        # Clear existing mock data first to avoid duplicate spam
        print("Clearing existing lead and revenue facts...")
        store._conn.execute("DELETE FROM facts WHERE kind IN ('lead', 'revenue')")
        store._conn.commit()

        now = datetime.now()

        # 1. Add some leads (some will convert, some won't)
        leads = [
            {
                "name": "Alice Smith",
                "email": "alice@gmail.com",
                "phone": "+1 (555) 019-2834",
                "query": "Need a quote for house cleaning: 3 bedrooms, 2 bathrooms, bi-weekly.",
                "days_ago": 15,
            },
            {
                "name": "Bob Jones",
                "email": "bob.jones@yahoo.com",
                "phone": "+1 (555) 014-9988",
                "query": "Looking for commercial window washing rates for 3-story office building.",
                "days_ago": 12,
            },
            {
                "name": "Charlie Davis",
                "email": "charlie.d@davisconsulting.com",
                "phone": "",
                "query": "Quote requested for custom digital marketing setup and SEO audit.",
                "days_ago": 8,
            },
            {
                "name": "Diana Prince",
                "email": "diana@themyscira.org",
                "phone": "+1 (555) 999-1111",
                "query": "Can you provide pricing for standard monthly landscaping package?",
                "days_ago": 4,
            },
            {
                "name": "Evan Wright",
                "email": "evan.wright@outlook.com",
                "phone": "+1 (555) 234-5678",
                "query": "Urgent: Burst pipe in basement. Need a plumber immediately.",
                "days_ago": 2,
            },
        ]

        print("Adding mock leads...")
        for lead in leads:
            created_dt = now - timedelta(days=lead["days_ago"])
            created_ts = int(created_dt.timestamp())

            payload = {
                "name": lead["name"],
                "email": lead["email"],
                "phone": lead["phone"],
                "query": lead["query"],
            }
            encoded = json.dumps(payload)

            # Insert via cursor to set custom created_at/updated_at timestamps
            store._conn.execute(
                "INSERT INTO facts (kind, key, value, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                ("lead", lead["name"], encoded, created_ts, created_ts),
            )
        store._conn.commit()

        # 2. Add some revenue transactions
        # Note: Alice Smith, Bob Jones, and Charlie Davis will convert.
        revenue = [
            {"client": "Alice Smith", "amount": 200.0, "type": "setup", "days_ago": 14},
            {"client": "Alice Smith", "amount": 50.0, "type": "monthly", "days_ago": 14},
            {"client": "Bob Jones", "amount": 450.0, "type": "setup", "days_ago": 10},
            {"client": "Charlie Davis", "amount": 300.0, "type": "setup", "days_ago": 7},
            {"client": "Charlie Davis", "amount": 100.0, "type": "monthly", "days_ago": 7},
            # A customer who came direct (not via lead capture bot)
            {"client": "Direct Corp", "amount": 150.0, "type": "subscription", "days_ago": 5},
        ]

        print("Adding mock revenue transactions...")
        for rev in revenue:
            created_dt = now - timedelta(days=rev["days_ago"])
            created_ts = int(created_dt.timestamp())
            date_str = created_dt.strftime("%Y-%m-%d")

            payload = {
                "client": rev["client"],
                "amount": rev["amount"],
                "type": rev["type"],
                "date": date_str,
            }
            encoded = json.dumps(payload)

            store._conn.execute(
                "INSERT INTO facts (kind, key, value, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                ("revenue", rev["client"], encoded, created_ts, created_ts),
            )
        store._conn.commit()

        print("Successfully loaded mock metrics into memory.db!")
        print("KPI Targets:")
        print("  - Total Revenue: $1,250.00")
        print("  - MRR: $300.00 ($50 + $100 + $150)")
        print("  - Total Leads: 5")
        print("  - Converted Leads: 3 (Alice, Bob, Charlie)")
        print("  - Conversion Rate: 60.0%")


if __name__ == "__main__":
    load_mock_data()
