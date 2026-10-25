"""Helper for Google Maps tool with privacy redaction."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Fields that should never be returned in the LLM output for privacy.
SENSITIVE_OUTPUT_KEYS = {
    "lat",
    "lng",
    "latitude",
    "longitude",
    "geometry",
    "location",
    "viewport",
    "plus_code",
    "formatted_phone_number",
    "international_phone_number",
    "adr_address",
    "vicinity",
    "url",
    "website",
    "permanently_closed",
    "postcode",
}


def _redact_sensitive_data(value: Any) -> Any:
    """Return a copy of value with sensitive fields redacted."""
    if isinstance(value, dict):
        redacted = {}
        for k, v in value.items():
            normalized_key = k.lower() if isinstance(k, str) else None
            if normalized_key in SENSITIVE_OUTPUT_KEYS:
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = _redact_sensitive_data(v)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive_data(item) for item in value]
    return value


def search_place(query: str, api_key: str | None = None) -> str:
    """Search for a place via Google Maps Text Search."""
    key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        return "Error: GOOGLE_MAPS_API_KEY not set."

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    try:
        resp = requests.get(url, params={"query": query, "key": key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Redact before returning
        clean_data = _redact_sensitive_data(data)
        return json.dumps(clean_data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error searching place: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: maps_client.py <query>")
        sys.exit(1)

    print(search_place(sys.argv[1]))
