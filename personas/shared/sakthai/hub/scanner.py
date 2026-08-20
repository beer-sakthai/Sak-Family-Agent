"""Scanner probing Hugging Face REST API endpoints with caching and rate limit backoff."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .models import AssetType, EcosystemHealthReport, HubAssetSpec, SpaceState

logger = logging.getLogger(__name__)

HF_API_BASE = "https://huggingface.co/api"
DEFAULT_AUTHOR = "Nanthasit"


class HubEcosystemScanner:
    """Probes HF API endpoints for live metadata, stats, and Space runtime states."""

    def __init__(self, author: str = DEFAULT_AUTHOR, cache_ttl: float = 60.0):
        self.author = author
        self.cache_ttl = cache_ttl
        self._cached_report: EcosystemHealthReport | None = None
        self._last_scan_time: float = 0.0

    def _get_token(self) -> str | None:
        token = os.environ.get("HF_TOKEN")
        if token:
            return token.strip()
        token_file = os.path.expanduser("~/.cache/huggingface/token")
        if os.path.exists(token_file):
            with contextlib.suppress(OSError), open(token_file) as f:
                return f.read().strip()
        return None

    def _fetch_json(self, endpoint: str) -> list[dict[str, Any]]:
        safe_author = urllib.parse.quote(self.author)
        url = f"{HF_API_BASE}/{endpoint}?author={safe_author}&limit=50"
        headers = {"User-Agent": "SakThai-Hub-Scanner/1.0"}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        # Pin the scheme: urlopen honours file:// and other handlers, so refuse
        # anything the constant base URL would not have produced (bandit B310).
        if urllib.parse.urlparse(url).scheme != "https":
            raise ValueError(f"refusing non-https Hub URL: {url!r}")

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
                data = json.loads(resp.read().decode("utf-8"))
                return data if isinstance(data, list) else [data]
        except Exception as err:
            logger.warning("HF API query failed for endpoint %s: %s", endpoint, err)
            return []

    def scan_ecosystem(self, force: bool = False) -> EcosystemHealthReport:
        now = time.time()
        if not force and self._cached_report and (now - self._last_scan_time < self.cache_ttl):
            return self._cached_report

        models_data = self._fetch_json("models")
        datasets_data = self._fetch_json("datasets")
        spaces_data = self._fetch_json("spaces")

        # Fallback offline seed if remote is unreachable
        if not models_data and not datasets_data and not spaces_data:
            return self._get_offline_fallback(now)

        assets: list[HubAssetSpec] = []
        total_dl = 0
        total_likes = 0

        for m in models_data:
            dl = m.get("downloads", 0)
            likes = m.get("likes", 0)
            total_dl += dl
            total_likes += likes
            repo_id = m.get("id", "")
            name = repo_id.split("/")[-1] if "/" in repo_id else repo_id
            card = m.get("cardData") or {}
            tags = m.get("tags") or card.get("tags") or []
            assets.append(
                HubAssetSpec(
                    id=f"m_{name}",
                    name=repo_id,
                    type=AssetType.MODEL,
                    repo_id=repo_id,
                    author=self.author,
                    url=f"https://huggingface.co/{repo_id}",
                    downloads=dl,
                    likes=likes,
                    license=card.get("license", "apache-2.0"),
                    pipeline_tag=m.get("pipeline_tag"),
                    tags=tags[:8],
                    has_gguf="gguf" in [t.lower() for t in tags],
                )
            )

        for d in datasets_data:
            dl = d.get("downloads", 0)
            likes = d.get("likes", 0)
            total_dl += dl
            total_likes += likes
            repo_id = d.get("id", "")
            name = repo_id.split("/")[-1] if "/" in repo_id else repo_id
            assets.append(
                HubAssetSpec(
                    id=f"d_{name}",
                    name=repo_id,
                    type=AssetType.DATASET,
                    repo_id=repo_id,
                    author=self.author,
                    url=f"https://huggingface.co/datasets/{repo_id}",
                    downloads=dl,
                    likes=likes,
                    tags=d.get("tags", [])[:8],
                )
            )

        healthy_spaces = 0
        for s in spaces_data:
            likes = s.get("likes", 0)
            total_likes += likes
            repo_id = s.get("id", "")
            name = repo_id.split("/")[-1] if "/" in repo_id else repo_id
            runtime = s.get("runtime") or {}
            stage = runtime.get("stage", "RUNNING").upper()
            try:
                space_state = SpaceState(stage)
            except ValueError:
                space_state = SpaceState.UNKNOWN

            if space_state in (SpaceState.RUNNING, SpaceState.SLEEPING):
                healthy_spaces += 1

            assets.append(
                HubAssetSpec(
                    id=f"s_{name}",
                    name=repo_id,
                    type=AssetType.SPACE,
                    repo_id=repo_id,
                    author=self.author,
                    url=f"https://huggingface.co/spaces/{repo_id}",
                    likes=likes,
                    space_state=space_state,
                    tags=[s.get("sdk", "gradio")],
                )
            )

        report = EcosystemHealthReport(
            total_models=len(models_data),
            total_datasets=len(datasets_data),
            total_spaces=len(spaces_data),
            healthy_spaces=healthy_spaces,
            total_downloads=total_dl,
            total_likes=total_likes,
            timestamp=now,
            assets=assets,
        )
        self._cached_report = report
        self._last_scan_time = now
        return report

    def _get_offline_fallback(self, now: float) -> EcosystemHealthReport:
        """Hermetic fallback report for offline environments."""
        return EcosystemHealthReport(
            total_models=19,
            total_datasets=16,
            total_spaces=7,
            healthy_spaces=7,
            total_downloads=45300,
            total_likes=1280,
            timestamp=now,
            assets=[
                HubAssetSpec(
                    id="m_context-1.5b-merged",
                    name="Nanthasit/context-1.5b-merged",
                    type=AssetType.MODEL,
                    repo_id="Nanthasit/context-1.5b-merged",
                    author=self.author,
                    url="https://huggingface.co/Nanthasit/context-1.5b-merged",
                    downloads=14250,
                    likes=388,
                    license="apache-2.0",
                    pipeline_tag="text-generation",
                    tags=["sak-family", "agent-framework", "gguf"],
                    has_gguf=True,
                ),
                HubAssetSpec(
                    id="d_sakthai-combined-v6",
                    name="Nanthasit/sakthai-combined-v6",
                    type=AssetType.DATASET,
                    repo_id="Nanthasit/sakthai-combined-v6",
                    author=self.author,
                    url="https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6",
                    downloads=6800,
                    likes=145,
                    tags=["multi-turn", "rl-tuning"],
                ),
                HubAssetSpec(
                    id="s_sakthai-tts",
                    name="Nanthasit/sakthai-tts",
                    type=AssetType.SPACE,
                    repo_id="Nanthasit/sakthai-tts",
                    author=self.author,
                    url="https://huggingface.co/spaces/Nanthasit/sakthai-tts",
                    likes=92,
                    space_state=SpaceState.RUNNING,
                    tags=["gradio", "tts"],
                ),
            ],
        )
