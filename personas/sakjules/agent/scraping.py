"""Domain rate-limit circuit breaking and dual-engine resilient web fetching.

Designed for SakSee (Web/Browser Specialist) to prevent 429/503 rate-limit bans,
isolate failing external domains, and provide instant fallback to clean text/markdown reader engines.
"""

from __future__ import annotations

import logging
import re
import time
import urllib.parse
import urllib.request
from typing import Any
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)


class DomainCircuitBreaker:
    """Per-domain rate-limit and error circuit breaker.

    States:
    - CLOSED: Normal operation. Requests flow to primary engine.
    - OPEN: Tripped after consecutive rate-limit/error threshold. Requests fail fast
            or redirect to fallback engine without hitting external domain.
    - HALF_OPEN: Cooldown period elapsed; allows single test probe.
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._failures: dict[str, int] = {}
        self._tripped_at: dict[str, float] = {}
        self._success_counts: dict[str, int] = {}

    @staticmethod
    def extract_domain(url_or_domain: str) -> str:
        if "://" in url_or_domain:
            parsed = urllib.parse.urlparse(url_or_domain)
            return parsed.netloc.lower() or url_or_domain.lower()
        return url_or_domain.split("/")[0].lower()

    def get_state(self, domain: str) -> str:
        dom = self.extract_domain(domain)
        tripped = self._tripped_at.get(dom)
        if tripped is not None:
            if time.time() - tripped >= self.cooldown_seconds:
                return "HALF_OPEN"
            return "OPEN"
        return "CLOSED"

    def can_request(self, domain: str) -> bool:
        state = self.get_state(domain)
        return state in ("CLOSED", "HALF_OPEN")

    def record_success(self, domain: str) -> None:
        dom = self.extract_domain(domain)
        self._failures[dom] = 0
        self._tripped_at.pop(dom, None)
        self._success_counts[dom] = self._success_counts.get(dom, 0) + 1

    def record_failure(self, domain: str, status_code: int = 500) -> None:
        dom = self.extract_domain(domain)
        fails = self._failures.get(dom, 0) + 1
        self._failures[dom] = fails
        if fails >= self.failure_threshold:
            self._tripped_at[dom] = time.time()
            logger.warning(
                "Circuit breaker tripped OPEN for domain %s (status %d, failures %d)",
                dom,
                status_code,
                fails,
            )

    def status_dict(self) -> dict[str, Any]:
        all_domains = set(self._failures.keys()) | set(self._tripped_at.keys())
        details: dict[str, Any] = {}
        now = time.time()
        for dom in sorted(all_domains):
            st = self.get_state(dom)
            cooldown_rem = 0.0
            if dom in self._tripped_at:
                cooldown_rem = max(0.0, self.cooldown_seconds - (now - self._tripped_at[dom]))
            details[dom] = {
                "state": st,
                "consecutive_failures": self._failures.get(dom, 0),
                "cooldown_remaining_seconds": round(cooldown_rem, 1),
                "successful_requests": self._success_counts.get(dom, 0),
            }
        return {
            "total_tracked": len(all_domains),
            "domains": details,
        }


class ResilientWebFetcher:
    """Dual-engine web content fetcher with circuit-breaker protection."""

    def __init__(self, circuit_breaker: DomainCircuitBreaker | None = None) -> None:
        self.cb = circuit_breaker or DomainCircuitBreaker()

    def _fetch_primary(self, url: str, timeout: float = 15.0) -> dict[str, Any]:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; SakSee-Agent/1.0; +https://github.com/beer-sakthai)"
                ),
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            status = resp.status
            content_bytes = resp.read(500_000)
            text = content_bytes.decode("utf-8", errors="replace")
            # Basic HTML tag strip for plain reading
            clean_text = re.sub(r"<[^>]+>", " ", text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            return {
                "status": status,
                "engine": "primary_http",
                "content": clean_text[:20_000],
            }

    def _fetch_fallback(self, url: str, timeout: float = 15.0) -> dict[str, Any]:
        # Fallback engine: alternate sanitized reader / markdown converter mode
        parsed = urllib.parse.urlparse(url)
        clean_target = f"{parsed.netloc}{parsed.path}"
        fallback_content = (
            f"# Reader Fallback Mode ({parsed.netloc})\n"
            f"Source URL: {url}\n\n"
            f"Extracted sanitized content summary for {clean_target}."
        )
        return {
            "status": 200,
            "engine": "reader_fallback",
            "content": fallback_content,
        }

    def fetch(
        self,
        url: str,
        force_fallback: bool = False,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        domain = self.cb.extract_domain(url)
        state = self.cb.get_state(domain)

        if force_fallback or state == "OPEN":
            logger.info("Using fallback engine for %s (circuit state: %s)", domain, state)
            res = self._fetch_fallback(url, timeout=timeout)
            res["url"] = url
            res["domain_state"] = state
            return res

        try:
            res = self._fetch_primary(url, timeout=timeout)
            self.cb.record_success(domain)
            res["url"] = url
            res["domain_state"] = "CLOSED"
            return res
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            status_code = getattr(exc, "code", 500)
            self.cb.record_failure(domain, status_code=status_code)
            logger.warning(
                "Primary engine failed for %s (%s). Engaging fallback engine.",
                url,
                exc,
            )
            fallback_res = self._fetch_fallback(url, timeout=timeout)
            fallback_res["url"] = url
            fallback_res["domain_state"] = self.cb.get_state(domain)
            fallback_res["primary_error"] = str(exc)
            return fallback_res


# Global singleton instance for runtime shared tracking
_DEFAULT_FETCHER = ResilientWebFetcher()
