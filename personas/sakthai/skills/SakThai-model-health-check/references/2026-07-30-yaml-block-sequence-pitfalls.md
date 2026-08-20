# YAML Generation Pitfalls — Block Sequence vs Flow Mapping

From the 7B health-check session (2026-07-30).

## Problem: Invalid flow mapping comma requirement

When producing YAML list items from Python dicts, do NOT use inline flow mapping (`{key: value}`) unless every entry has a **comma** between key-value pairs:

```yaml
# VALID — flow mapping with commas:
- {model: "sakthai-7b", downloads: 744}

# INVALID — flow mapping WITHOUT commas (what the naive `add()` produces):
- {
    model: "sakthai-7b"
    downloads: 744
  }
```

The invalid form silently fails YAML parsers. Always use **block sequence** format for multi-key dicts in lists:

```yaml
# VALID — block sequence (correct):
-
  model: "sakthai-7b"
  downloads: 744
```

### Fix in the `add()` helper

Instead of writing dict items inside `{` `}` (flow mapping), render each dict as a block sequence item:

```python
# WRONG — produces invalid YAML:
lines.append(prefix + '  - {')
for sk, sv in item.items():
    lines.append(prefix + '      ' + sk + ': "' + sv + '"')
lines.append(prefix + '    }')

# CORRECT — block sequence format:
lines.append(prefix + '  -')
for sk, sv in item.items():
    sv_prefix = prefix + '    '
    lines.append(sv_prefix + sk + ': ' + str(sv))
```

## Problem: Empty lists render as bare key with no content

A Python `[]` value passes `isinstance(v, list)` True, enters the list branch, produces the key name, then generates zero items below it. The result is:

```yaml
deductions_list:        # ← just a key, YAML sees this as null
```

### Fix

Post-process with string replacement for known empty-list keys:

```python
output = output.replace('deductions_list:\n', 'deductions_list: []\n')
```

Or handle empty lists explicitly in the `add()` helper:

```python
elif isinstance(v, list):
    if len(v) == 0:
        lines.append(prefix + k + ': []')
    else:
        lines.append(prefix + k + ':')
        for item in v:
            ...
```

## Problem: Variable-ordering bugs in generation scripts

Python dict literals evaluate ALL their values at construction time (not lazily). If a variable used inside a dict literal is defined later in the script, you get `NameError`:

```python
# BUG — rank_pos_in_all used before definition:
add('sibling_comparison', {
    'rank_among_all_author': f'{rank_pos_in_all} of {rank_among_all}',
    ...
})

# rank_pos_in_all defined here — too late!
rank_pos_in_all = compute_rank(...)
```

### Fix

Always compute ALL derived values before building any dict that uses them. Group computation at the top, YAML assembly at the bottom:

```python
# === COMPUTE FIRST ===
rank_pos_in_all = compute_rank(...)
velocities = compute_velocities(...)
sib_entries = build_siblings(...)

# === THEN BUILD YAML ===
add('sibling_comparison', {
    'rank_among_all_author': f'{rank_pos_in_all} of ...',
    ...
})
```

## Problem: F-string quoting hell with escaped quotes

Inside a `write_file`-written `.py` script, f-strings containing escaped double-quotes (`\\\"true\\\"`) produce syntax errors because the escaping layers interact unexpectedly:

```python
# SyntaxError — unexpected character after line continuation
lines.append(f'{prefix}{k}: {\\"true\\" if v else \\"false\\"}')
```

### Fix

Use string concatenation instead of f-strings for YAML value formatting, or extract the conditional into a helper function:

```python
def fmt_bool(b):
    return 'true' if b else 'false'

# No f-string, no escaping issues:
lines.append(prefix + k + ': ' + fmt_bool(v))
```

This avoids all f-string quoting layers and works identically.
