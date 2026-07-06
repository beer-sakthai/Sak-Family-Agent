"""Explicit fact capture."""

from __future__ import annotations

from .capture import learn
from .ingest import ingest_document

__all__ = ["ingest_document", "learn"]
