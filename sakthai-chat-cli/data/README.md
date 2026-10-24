# data/

Sample data and the on-disk format of a memory snapshot.

## Snapshot format

`sakthai memory export <file>` writes a portable JSON snapshot of the store:

```json
{
  "version": 1,
  "exported_at": 1718450000,
  "db_path": "/home/you/.sakthai/memory.db",
  "facts": [ { "id": 1, "kind": "pref", "key": "theme", "value": "dark",
               "source_session": null, "created_at": 0, "updated_at": 0,
               "tags": ["ui"] } ],
  "observations": [ { "id": 1, "summary": "prefers dark UIs", "weight": 1.0,
                      "confidence": 0.5, "evidence_session_id": null,
                      "created_at": 0 } ]
}
```

`memory import <file>` restores it (`--replace` preserves IDs; default merges
with fresh IDs). `--format csv|jsonl` produces flat exports instead.

## Files

- [`sample-memory.jsonl`](./sample-memory.jsonl) — a tiny example export
  (`sakthai memory export sample.jsonl --format jsonl`), one record per line,
  each tagged with `type`. Useful as a fixture or a dataset seed.
