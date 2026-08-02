# HF Spaces Secrets Management — Reference

## Core Difference: Secrets vs Variables

| Feature | Variables | Secrets |
|---------|-----------|---------|
| Value readable back? | Yes | No (write-once) |
| Visible in settings UI? | Yes | Masked |
| Duplicated on fork? | Yes | No |
| Use case | Non-sensitive config | Credentials, tokens, keys |

## Python API (`HfApi` methods)

### Adding/Updating
```python
api.add_space_secret(repo_id, key, value, *, description=None, token=None)
api.add_space_variable(repo_id, key, value, *, description=None, token=None)
```

### Reading
```python
api.get_space_secrets(repo_id, *, token=None)    # -> dict[str, SpaceSecret]
api.get_space_variables(repo_id, *, token=None)   # -> dict[str, SpaceVariable]
```

### Deleting
```python
api.delete_space_secret(repo_id, key, *, token=None)
api.delete_space_variable(repo_id, key, *, token=None)
```

## REST Endpoints
- `GET|POST|DELETE /api/spaces/{repo_id}/secrets`
- `GET|POST|DELETE /api/spaces/{repo_id}/variables`

## Data Classes

**SpaceSecret**: key, description (str|None), updated_at (datetime|None)
- No value field — value is write-only

**SpaceVariable**: key, value (str), description (str|None), updated_at (datetime|None)
- Value IS readable

## Docker Buildtime
- Variables: `ARG KEY` in Dockerfile
- Secrets: `RUN --mount=type=secret,id=KEY`

## Runtime
Both are injected as env vars: `os.getenv("KEY")`

## Space Creation
```python
api.create_repo(..., space_secrets=[{"key":"K", "value":"V", "description":"..."}], space_variables=[...])
```

## Secrets Scanner
HF auto-scans Spaces for hardcoded secrets and warns owners.
Always use the Secrets API instead of hardcoding tokens.

## Zero-Cost
All API operations are free. No cost for managing secrets programmatically.
