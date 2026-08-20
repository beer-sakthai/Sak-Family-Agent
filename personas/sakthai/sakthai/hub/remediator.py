"""Space remediation and runtime health healer for Hugging Face Spaces."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Any

from .models import SpaceState

logger = logging.getLogger(__name__)

HF_API_BASE = "https://huggingface.co/api"


class SpaceRemediator:
    """Diagnoses Space runtime failures and executes container heal actions."""

    def __init__(self, author: str = "Nanthasit") -> None:
        self.author = author

    def _get_token(self) -> str | None:
        token = os.environ.get("HF_TOKEN")
        if token:
            return token.strip()
        token_file = os.path.expanduser("~/.cache/huggingface/token")
        if os.path.exists(token_file):
            with contextlib.suppress(Exception), open(token_file) as f:
                return f.read().strip()
        return None

    def diagnose_space(self, repo_id: str) -> dict[str, Any]:
        """Fetch real-time container runtime diagnosis for a Hugging Face Space."""
        safe_repo = urllib.parse.quote(repo_id, safe="/")
        url = f"{HF_API_BASE}/spaces/{safe_repo}"
        headers = {"User-Agent": "SakThai-Space-Remediator/1.0"}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310 - safe: HTTPS Hugging Face API base
                data = json.loads(resp.read().decode("utf-8"))
                runtime = data.get("runtime", {})
                raw_stage = runtime.get("stage", "STOPPED").upper()
                try:
                    state = SpaceState(raw_stage)
                except ValueError:
                    state = SpaceState.STOPPED

                return {
                    "repo_id": repo_id,
                    "state": state.value,
                    "hardware": runtime.get("hardware", {}).get("current", "cpu-basic"),
                    "gc_timeout": runtime.get("gcTimeout"),
                    "healthy": state == SpaceState.RUNNING,
                    "errorMessage": runtime.get("errorMessage"),
                }
        except Exception as err:
            logger.warning("Space diagnosis failed for %s: %s", repo_id, err)
            return {
                "repo_id": repo_id,
                "state": SpaceState.STOPPED.value,
                "hardware": "cpu-basic",
                "healthy": False,
                "errorMessage": str(err),
            }

    def restart_space(self, repo_id: str, factory_rebuild: bool = False) -> bool:
        """Trigger container restart or factory rebuild via HF API."""
        safe_repo = urllib.parse.quote(repo_id, safe="/")
        action = "restart" if not factory_rebuild else "restart?factory=true"
        url = f"{HF_API_BASE}/spaces/{safe_repo}/{action}"
        token = self._get_token()
        if not token:
            logger.warning(
                "HF_TOKEN missing; cannot perform live restart for %s (dry-run mode)", repo_id
            )
            return True

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "SakThai-Space-Remediator/1.0",
        }
        req = urllib.request.Request(url, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310 - safe: HTTPS Hugging Face API base
                return resp.status in (200, 201, 204)
        except Exception as err:
            logger.error("Failed to restart space %s: %s", repo_id, err)
            return False

    def auto_heal_all_spaces(self, space_ids: list[str]) -> dict[str, Any]:
        """Probe all given spaces and trigger remediation on failing containers."""
        remediated: list[str] = []
        failed: list[str] = []
        healthy_count = 0

        for space_id in space_ids:
            diag = self.diagnose_space(space_id)
            if diag.get("healthy"):
                healthy_count += 1
            else:
                logger.info(
                    "Space %s is unhealthy (%s); triggering restart...", space_id, diag.get("state")
                )
                success = self.restart_space(
                    space_id, factory_rebuild=diag.get("state") == SpaceState.BUILD_ERROR.value
                )
                if success:
                    remediated.append(space_id)
                else:
                    failed.append(space_id)
        return {
            "probed": len(space_ids),
            "healthy": healthy_count,
            "remediated": remediated,
            "failed": failed,
        }
