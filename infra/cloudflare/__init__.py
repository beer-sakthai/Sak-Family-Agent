"""Cloudflare infrastructure management package."""

from __future__ import annotations

from .dns_manager import (
    create_nameserver_set,
    get_cloudflare_client,
    list_nameserver_sets,
    upsert_dns_record,
)

__all__ = [
    "create_nameserver_set",
    "get_cloudflare_client",
    "list_nameserver_sets",
    "upsert_dns_record",
]
