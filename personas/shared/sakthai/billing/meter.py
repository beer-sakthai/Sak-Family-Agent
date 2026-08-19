"""Thread-safe SQLite-backed Token Meter and Quota Enforcement Engine."""

from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sakthai.billing.models import (
    TIER_LIMITS,
    TIER_PRICING,
    APIKeyRecord,
    InvoiceRecord,
    TenantQuota,
    TenantTier,
    UsageEvent,
    generate_api_key,
    hash_api_key,
)


class TokenMeter:
    """Thread-safe token consumption meter and API key manager with SQLite persistence."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_env = os.getenv("SAKTHAI_BILLING_DB")
            self.db_path = Path(db_env) if db_env else Path.home() / ".sakthai" / "billing.sqlite3"
        elif str(db_path) == ":memory:":
            self.db_path = Path(":memory:")
        else:
            self.db_path = Path(db_path)

        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._shared_conn: sqlite3.Connection | None = None
        if str(self.db_path) == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False, timeout=30.0)
            self._shared_conn.row_factory = sqlite3.Row

        self._lock = threading.RLock()
        self._rate_limits: dict[str, list[float]] = {}  # key_id -> list of request timestamps
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS billing_tenants (
                    tenant_id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS billing_api_keys (
                    key_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    hashed_key TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    prefix TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    rate_limit_rpm INTEGER NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES billing_tenants(tenant_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS billing_usage_events (
                    event_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    key_id TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (tenant_id) REFERENCES billing_tenants(tenant_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_billing_keys_hash ON billing_api_keys(hashed_key);
                CREATE INDEX IF NOT EXISTS idx_billing_usage_tenant ON billing_usage_events(tenant_id, timestamp);
                """
            )

    def register_tenant(self, tenant_id: str, tier: TenantTier = TenantTier.FREE) -> TenantQuota:
        """Register a new tenant or return existing tenant quota."""
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO billing_tenants (tenant_id, tier, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(tenant_id) DO UPDATE SET tier=excluded.tier;
                """,
                (tenant_id, tier.value, datetime.now(UTC).isoformat()),
            )
        return self.get_tenant_quota(tenant_id)

    def create_api_key(
        self, tenant_id: str, name: str, prefix: str = "sak_live_"
    ) -> tuple[str, APIKeyRecord]:
        """Create and store a new API key for a tenant."""
        quota = self.get_tenant_quota(tenant_id)
        max_quota, rpm, max_keys = TIER_LIMITS[quota.tier]

        if quota.active_keys_count >= max_keys:
            raise ValueError(
                f"Tenant {tenant_id} on tier {quota.tier.value} has reached max keys limit ({max_keys})"
            )

        raw_key, hashed_key = generate_api_key(prefix=prefix)
        key_id = f"key_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()

        record = APIKeyRecord(
            key_id=key_id,
            tenant_id=tenant_id,
            hashed_key=hashed_key,
            name=name,
            prefix=raw_key[:12] + "...",
            tier=quota.tier,
            is_active=True,
            created_at=now,
            rate_limit_rpm=rpm,
        )

        with self._lock, self._get_connection() as conn:
            # Ensure tenant exists
            conn.execute(
                """
                INSERT OR IGNORE INTO billing_tenants (tenant_id, tier, created_at)
                VALUES (?, ?, ?);
                """,
                (tenant_id, quota.tier.value, now),
            )
            conn.execute(
                """
                INSERT INTO billing_api_keys (
                    key_id, tenant_id, hashed_key, name, prefix, tier, is_active, created_at, rate_limit_rpm
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.key_id,
                    record.tenant_id,
                    record.hashed_key,
                    record.name,
                    record.prefix,
                    record.tier.value,
                    1 if record.is_active else 0,
                    record.created_at,
                    record.rate_limit_rpm,
                ),
            )

        return raw_key, record

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke / deactivate an API key."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE billing_api_keys SET is_active = 0 WHERE key_id = ?;",
                (key_id,),
            )
            return cursor.rowcount > 0

    def list_api_keys(self, tenant_id: str) -> list[APIKeyRecord]:
        """List all API keys for a tenant."""
        with self._lock, self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT key_id, tenant_id, hashed_key, name, prefix, tier, is_active, created_at, last_used_at, rate_limit_rpm
                FROM billing_api_keys
                WHERE tenant_id = ?
                ORDER BY created_at DESC;
                """,
                (tenant_id,),
            ).fetchall()

            return [
                APIKeyRecord(
                    key_id=r["key_id"],
                    tenant_id=r["tenant_id"],
                    hashed_key=r["hashed_key"],
                    name=r["name"],
                    prefix=r["prefix"],
                    tier=TenantTier(r["tier"]),
                    is_active=bool(r["is_active"]),
                    created_at=r["created_at"],
                    last_used_at=r["last_used_at"],
                    rate_limit_rpm=r["rate_limit_rpm"],
                )
                for r in rows
            ]

    def authenticate_key(self, raw_key: str) -> APIKeyRecord | None:
        """Authenticate a raw API key and verify active state."""
        candidate = raw_key.strip()
        with self._lock, self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT key_id, tenant_id, hashed_key, name, prefix, tier, is_active, created_at, last_used_at, rate_limit_rpm
                FROM billing_api_keys
                WHERE is_active = 1;
                """
            ).fetchall()

            row = next((r for r in rows if hash_api_key(candidate, r["hashed_key"]) is True), None)
            if not row:
                return None

            now = datetime.now(UTC).isoformat()
            conn.execute(
                "UPDATE billing_api_keys SET last_used_at = ? WHERE key_id = ?;",
                (now, row["key_id"]),
            )

            return APIKeyRecord(
                key_id=row["key_id"],
                tenant_id=row["tenant_id"],
                hashed_key=row["hashed_key"],
                name=row["name"],
                prefix=row["prefix"],
                tier=TenantTier(row["tier"]),
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                last_used_at=now,
                rate_limit_rpm=row["rate_limit_rpm"],
            )

    def check_rate_limit(self, key_id: str, limit_rpm: int) -> bool:
        """Sliding window rate limit check for a key."""
        with self._lock:
            now = time.time()
            window_start = now - 60.0
            timestamps = self._rate_limits.setdefault(key_id, [])
            # Filter out timestamps older than 60s
            self._rate_limits[key_id] = [t for t in timestamps if t >= window_start]
            if len(self._rate_limits[key_id]) >= limit_rpm:
                return False
            self._rate_limits[key_id].append(now)
            return True

    def calculate_cost(self, tier: TenantTier, prompt_tokens: int, completion_tokens: int) -> float:
        """Compute USD cost for token usage according to tier rates."""
        prompt_rate, completion_rate = TIER_PRICING[tier]
        cost = (prompt_tokens / 1_000_000.0) * prompt_rate + (
            completion_tokens / 1_000_000.0
        ) * completion_rate
        return cost

    def record_usage(
        self,
        tenant_id: str,
        key_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> UsageEvent:
        """Atomically record token consumption and deduct from quota."""
        total_tokens = prompt_tokens + completion_tokens
        quota = self.get_tenant_quota(tenant_id)
        cost_usd = self.calculate_cost(quota.tier, prompt_tokens, completion_tokens)

        event = UsageEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            key_id=key_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
        )

        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO billing_usage_events (
                    event_id, tenant_id, key_id, model, prompt_tokens, completion_tokens, total_tokens, cost_usd, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    event.event_id,
                    event.tenant_id,
                    event.key_id,
                    event.model,
                    event.prompt_tokens,
                    event.completion_tokens,
                    event.total_tokens,
                    event.cost_usd,
                    event.timestamp,
                ),
            )

        return event

    def get_tenant_quota(self, tenant_id: str) -> TenantQuota:
        """Get monthly token quota, consumption, and costs for a tenant."""
        with self._lock, self._get_connection() as conn:
            tenant_row = conn.execute(
                "SELECT tier FROM billing_tenants WHERE tenant_id = ?;",
                (tenant_id,),
            ).fetchone()

            tier = TenantTier(tenant_row["tier"]) if tenant_row else TenantTier.FREE
            max_quota, _, _ = TIER_LIMITS[tier]

            # Aggregate usage for current month
            now = datetime.now(UTC)
            month_start = datetime(now.year, now.month, 1, tzinfo=UTC).isoformat()

            usage_row = conn.execute(
                """
                SELECT COALESCE(SUM(total_tokens), 0) as consumed_tokens,
                       COALESCE(SUM(cost_usd), 0.0) as total_cost
                FROM billing_usage_events
                WHERE tenant_id = ? AND timestamp >= ?;
                """,
                (tenant_id, month_start),
            ).fetchone()

            consumed = int(usage_row["consumed_tokens"]) if usage_row else 0
            total_cost = float(usage_row["total_cost"]) if usage_row else 0.0

            keys_count_row = conn.execute(
                "SELECT COUNT(*) as count FROM billing_api_keys WHERE tenant_id = ? AND is_active = 1;",
                (tenant_id,),
            ).fetchone()
            active_keys = int(keys_count_row["count"]) if keys_count_row else 0

            # Calculate next reset date (first day of next month)
            if now.month == 12:
                next_reset = datetime(now.year + 1, 1, 1, tzinfo=UTC).isoformat()
            else:
                next_reset = datetime(now.year, now.month + 1, 1, tzinfo=UTC).isoformat()

            remaining = max(0, max_quota - consumed)

            return TenantQuota(
                tenant_id=tenant_id,
                tier=tier,
                monthly_token_quota=max_quota,
                consumed_tokens=consumed,
                remaining_tokens=remaining,
                total_cost_usd=total_cost,
                active_keys_count=active_keys,
                reset_date=next_reset,
            )

    def check_quota(
        self, tenant_id: str, estimated_tokens: int = 1
    ) -> tuple[bool, str, TenantQuota]:
        """Check if tenant has remaining quota for execution."""
        quota = self.get_tenant_quota(tenant_id)
        if quota.tier == TenantTier.PAY_AS_YOU_GO:
            return True, "OK", quota
        if quota.remaining_tokens < estimated_tokens:
            return (
                False,
                f"Monthly token quota exceeded ({quota.consumed_tokens}/{quota.monthly_token_quota} tokens used). Upgrade tier to continue.",
                quota,
            )
        return True, "OK", quota

    def get_usage_events(self, tenant_id: str, limit: int = 50) -> list[UsageEvent]:
        """Retrieve recent usage events for a tenant."""
        with self._lock, self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT event_id, tenant_id, key_id, model, prompt_tokens, completion_tokens, total_tokens, cost_usd, timestamp
                FROM billing_usage_events
                WHERE tenant_id = ?
                ORDER BY timestamp DESC
                LIMIT ?;
                """,
                (tenant_id, limit),
            ).fetchall()

            return [
                UsageEvent(
                    event_id=r["event_id"],
                    tenant_id=r["tenant_id"],
                    key_id=r["key_id"],
                    model=r["model"],
                    prompt_tokens=r["prompt_tokens"],
                    completion_tokens=r["completion_tokens"],
                    total_tokens=r["total_tokens"],
                    cost_usd=r["cost_usd"],
                    timestamp=r["timestamp"],
                )
                for r in rows
            ]

    def generate_invoice(self, tenant_id: str) -> InvoiceRecord:
        """Generate monthly summary invoice record."""
        quota = self.get_tenant_quota(tenant_id)
        now = datetime.now(UTC)
        period_start = datetime(now.year, now.month, 1, tzinfo=UTC).isoformat()
        period_end = now.isoformat()

        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) as count,
                       COALESCE(SUM(total_tokens), 0) as total_tokens,
                       COALESCE(SUM(cost_usd), 0.0) as total_cost
                FROM billing_usage_events
                WHERE tenant_id = ? AND timestamp >= ?;
                """,
                (tenant_id, period_start),
            ).fetchone()

            total_requests = int(row["count"]) if row else 0
            total_tokens = int(row["total_tokens"]) if row else 0
            amount_due = float(row["total_cost"]) if row else 0.0

            invoice_id = f"inv_{now.strftime('%Y%m')}_{uuid.uuid4().hex[:6]}"

            return InvoiceRecord(
                invoice_id=invoice_id,
                tenant_id=tenant_id,
                period_start=period_start,
                period_end=period_end,
                total_requests=total_requests,
                total_tokens=total_tokens,
                amount_due_usd=amount_due,
                status="paid" if amount_due == 0.0 else "due",
            )
