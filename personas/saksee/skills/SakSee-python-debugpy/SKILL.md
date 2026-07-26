---
name: SakSee-python-debugpy
description: Debug Python: pdb REPL + debugpy remote (DAP).
category: software-development
tags: [python, debugger, pdb]
---

# Python Debugging

## pdb (Built-in)

```python
import pdb; pdb.set_trace()  # Python 3.6+
breakpoint()  # Python 3.7+
```

### Commands
- `n` — next line
- `s` — step into
- `c` — continue
- `p var` — print variable
- `l` — list source
- `q` — quit

## debugpy (Remote DAP)

```bash
pip install debugpy
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client app.py
```

Connect VS Code: create launch.json with `"debugServer": 5678`.
