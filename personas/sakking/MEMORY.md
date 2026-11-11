# MEMORY.md — SakKing 👑
> *TDD execution, CLI runner, utility refactoring, subagents — Memory Store*

---

## 🧠 Where My Memory Lives

- **My shard**: `~/.sakthai/sakking/memory.db`. Locally that is `--persona sakking`; on the VM, `infra/vm-agents/sakthai-agent-run.sh` sets `SAKTHAI_HOME=$HOME/.sakthai/sakking`, which resolves to the same file.
- **The family**: `sakthai memory family` reads all six shards plus the legacy `~/.sakthai/memory.db`.
- **This file is not the store.** Facts live in the shard; this file keeps the bindings and verified events worth keeping in the repository.
- The shard is created on its first write.

---

## 📖 Read

```bash
sakthai recall --persona sakking "<query>"
sakthai memory --persona sakking show
sakthai memory --persona sakking stats
```

Pre-task checklist (SOUL.md):

```bash
sakthai memory family "CHARGE: sakking" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: sakking" --tag cycle-interrupted --tag sakking --tag resumable --limit 1
```

---

## ✍️ Write

```bash
sakthai learn --persona sakking "<fact>" --tag sakking --tag <topic>
```

The `sakthai learn` commands in SOUL.md omit `--persona`: on the VM, `SAKTHAI_HOME` already scopes them. In a local shell, add `--persona sakking`, or the fact lands in the unscoped `~/.sakthai/memory.db`.

---

## 🛡️ Keep It Healthy

```bash
sakthai memory --persona sakking healthcheck
sakthai memory --persona sakking backup
```

---

## 📋 Verified Execution Log

_Nothing recorded yet._ Add an entry only for something that ran and can be checked: the date, the command, and its result.

---

*SakKing Memory Node · House of Sak*
