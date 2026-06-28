# Workspace Agent Rules — sakthai-hermes-agents

## oh-my-product CLI

The `oh-my-product` and `omp` CLI binaries are NOT installed in this workspace.
When any `/oh-my-product:*` skill is invoked, ALWAYS implement the skill natively
using Python or shell inline scripts. Never attempt to call `oh-my-product ...`,
`omp ...`, or `npm run omp -- ...` — they will all return `command not found`.

---

## Git Push — Deploy Key Limitation

The SSH key available to the agent in this workspace is a **read-only GitHub deploy key**.
`git push` will always fail with a permission error:
```
ERROR: Permission to beer-sakthai/sakthai-hermes-agents.git denied to deploy key
```

- NEVER attempt `git push` autonomously and expect it to succeed.
- After committing, ALWAYS instruct the user to run `git push` from their host terminal.
- `git fetch`, `git log`, `git status`, `git rebase` are all fine (read operations work).

---

## systemd User Services — Sandbox Limitation

`systemctl --user` commands ALWAYS fail inside the agent sandbox because there is
no `/run/user` directory or D-Bus session socket available.

- NEVER attempt `systemctl --user start/stop/restart/daemon-reload` autonomously.
- After deploying changed configs or service files, ALWAYS provide the user with the
  exact commands to run in their host terminal, e.g.:
  ```bash
  systemctl --user daemon-reload
  systemctl --user restart hermes-gateway.service hermes-gateway-saksee.service \
    hermes-gateway-sakthai.service hermes-gateway-saksit.service
  ```
