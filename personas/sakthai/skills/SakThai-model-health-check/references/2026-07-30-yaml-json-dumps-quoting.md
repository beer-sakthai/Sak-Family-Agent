# YAML Quoting: `json.dumps()` Inside Double-Quoted Strings

Observed 2026-07-30 on `Nanthasit/sakthai-plus-1.5b` health check.

## The Problem

Embedding `json.dumps(changes)` inside a YAML double-quoted string produces invalid YAML:

```yaml
changes_since_previous: "{"last_modified": "see below"}"
```

The inner double quotes clash with the outer YAML double-quoted string delimiter. PyYAML raises `ParserError: while parsing a block mapping`.

## The Fix

Expand the dict as a YAML mapping instead of embedding JSON:

```python
if changes:
    lines.append("  changes_since_previous:")
    for k, v in changes.items():
        lines.append(f"    {k}: \"{v}\"")
else:
    lines.append("  changes_since_previous: \"none\"")
```

Produces:

```yaml
changes_since_previous:
  last_modified: "see below"
```

## Detection

YAML parser error at the `changes_since_previous` line containing `\"` characters from JSON.
