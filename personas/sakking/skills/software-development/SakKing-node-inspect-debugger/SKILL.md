---
name: SakKing-node-inspect-debugger
description: Debug Node.js via --inspect + Chrome DevTools Protocol CLI.
category: software-development
tags: [nodejs, debugger, cdp]
---

# Node.js Debugger (--inspect)

Debug Node.js applications using the `--inspect` flag and CDP.

## Quick Start

```bash
node --inspect app.js
# Debugger listening on ws://127.0.0.1:9229/...

# Connect via CLI
node inspect app.js
```

## Breakpoints

```bash
node inspect app.js
> n        # next
> s        # step into
> o        # step out
> c        # continue
> repl     # enter REPL mode
> .exit    # exit debugger
```

## Remote Debugging

```bash
node --inspect=0.0.0.0:9229 app.js
# Connect via DevTools frontend at chrome://inspect
```
