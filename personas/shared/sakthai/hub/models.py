"""Data models for Hugging Face Hub asset catalog, card validation, and health reports."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class AssetType(enum.StrEnum):
    MODEL = "model"
    DATASET = "dataset"
    SPACE = "space"


class SpaceState(enum.StrEnum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    SLEEPING = "SLEEPING"
    BUILD_ERROR = "BUILD_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass
class HubAssetSpec:
    id: str
    name: str
    type: AssetType
    repo_id: str
    author: str
    url: str
    downloads: int = 0
    likes: int = 0
    license: str = "apache-2.0"
    pipeline_tag: str | None = None
    tags: list[str] = field(default_factory=list)
    has_gguf: bool = False
    quantizations: list[str] = field(default_factory=list)
    status: str = "active"
    space_state: SpaceState | None = None


@dataclass
class CardValidationIssue:
    rule: str
    message: str
    severity: str  # "error", "warning"
    line: int | None = None


@dataclass
class CardValidationReport:
    repo_id: str
    valid: bool
    score: int  # 0 - 100
    issues: list[CardValidationIssue] = field(default_factory=list)


@dataclass
class EcosystemHealthReport:
    total_models: int
    total_datasets: int
    total_spaces: int
    healthy_spaces: int
    total_downloads: int
    total_likes: int
    timestamp: float
    assets: list[HubAssetSpec] = field(default_factory=list)
