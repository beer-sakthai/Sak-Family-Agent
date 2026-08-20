# YAML `add()` Helper Pattern — Clean Generation Without Quoting Hell

A proven alternative to both `json.dumps` + key replacement and manual f-string
building. Uses a small `add()` function that formats each key-value pair as YAML
with correct indentation, types, and quoting — completely sidestepping the
nested f-string quoting issues that plague inline YAML generation.

## The `add()` helper

```python
def add(key, value, indent=0):
    pad = '  ' * indent
    if isinstance(value, bool):
        lines.append(pad + key + ': ' + ('true' if value else 'false'))
    elif isinstance(value, (int, float)):
        lines.append(pad + key + ': ' + str(value))
    elif value is None:
        lines.append(pad + key + ': null')
    else:
        lines.append(pad + key + ': "' + str(value) + '"')

def add_raw(line):
    lines.append(line)
```

## Usage pattern

```python
lines = []
add_raw('metadata:')
add('model_id', 'Nanthasit/sakthai-0.5b', 1)
add('downloads', 1370, 1)
add('private', False, 1)
add('score', None, 1)  # produces 'score: null'
```

Produces clean YAML:
```yaml
metadata:
  model_id: "Nanthasit/sakthai-0.5b"
  downloads: 1370
  private: false
  score: null
```

## Pre-compute ALL string values first

The key insight: **never embed dict access or method calls inside the YAML
builder**. Pre-compute every value before the builder phase:

```python
# BAD — quoting nightmare:
yaml_lines.append(f'  details: "License={cd.get("license")}, {len(tags)} tags"')

# GOOD — pre-compute, then embed simple variables:
lic = cd.get('license', 'unknown')
tag_count = len(tags)
yaml_lines.append(f'  details: "License={lic}, {tag_count} tags"')

# BEST — avoid f-strings entirely in the builder:
add('details', f'License={lic}, {tag_count} tags', 1)
```

## When to use

- Any health-check generator with 20+ YAML fields
- When `pyyaml` is not available (cron mode bare python3)
- When the previous session hit `SyntaxError: unexpected character after line
  continuation character` from nested `\"` inside f-strings

## Proven in production

Used successfully in `gen_ctx05b_health.py` (2026-07-30 health check for
`sakthai-context-0.5b-merged`). Zero quoting errors, lint passed first time,
204-line YAML produced clean.
