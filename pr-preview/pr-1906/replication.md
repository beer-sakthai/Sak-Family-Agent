# SQLite Replication in SakThai Agent

While `sakthai memory sync` handles flat-file and Git-based backups (which works well for local-first workflows), true real-time database replication requires streaming the SQLite Write-Ahead Log (WAL).

## Evaluation

We evaluated two primary methods for true DB replication:

### 1. Litestream
- **Pros:** Extremely robust, streams directly to S3/GCS.
- **Cons:** Requires a separate Go binary to run as a background daemon. Violates SakThai's zero-dependency Python-only goal.

### 2. Turso (libsql-experimental)
- **Pros:** Native Python package (`libsql-experimental`), allows local reads and async remote writes to a serverless DB.
- **Cons:** Requires a third-party account (Turso) and a hosted endpoint.

## Proposed Integration (Turso)

To implement this in the future without breaking the local-first nature of SakThai, users could provide a `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`. 

Instead of standard `sqlite3`, the `MemoryStore` would use `libsql_experimental`:

```python
import libsql_experimental as libsql

def connect_db(db_path, sync_url=None, auth_token=None):
    if sync_url and auth_token:
        # Replicated mode: writes sync to cloud in background
        return libsql.connect(db_path, sync_url=sync_url, auth_token=auth_token)
    else:
        # Local-only mode
        return libsql.connect(db_path)
```

## Conclusion
For v2, the improved Git/JSONL auto-merge mechanism satisfies the synchronization requirement without forcing users into a SaaS ecosystem. The Turso wrapper architecture is documented here and can be cleanly dropped into `sakthai/memory/store.py` in Phase 12 or v3 if the Git-based sync proves insufficient at scale.
