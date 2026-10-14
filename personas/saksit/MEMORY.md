# MEMORY.md — SakSit 📣
> *Brand Copy, Social Posts, Hub Dataset Cards, Storytelling — Memory Store*

---

## 🧠 Where My Memory Lives

- **My shard**: `~/.sakthai/saksit/memory.db`. Locally that is `--persona saksit`; on the VM, `infra/vm-agents/sakthai-agent-run.sh` sets `SAKTHAI_HOME=$HOME/.sakthai/saksit`, which resolves to the same file.
- **The family**: `sakthai memory family` reads all six shards plus the legacy `~/.sakthai/memory.db`.
- **This file is not the store.** Facts live in the shard; this file keeps the bindings and verified events worth keeping in the repository.
- The shard is created on its first write.

---

## 📖 Read

```bash
sakthai recall --persona saksit "<query>"
sakthai memory --persona saksit show
sakthai memory --persona saksit stats
```

Pre-task checklist (SOUL.md):

```bash
sakthai memory family "CHARGE: saksit" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "CYCLE INTERRUPTED: saksit" --tag cycle-interrupted --tag saksit --tag resumable --limit 1
sakthai memory family "hub-draft" --tag hub-draft --tag awaiting-review --limit 5
```

---

## ✍️ Write

```bash
sakthai learn --persona saksit "<fact>" --tag saksit --tag <topic>
```

The `sakthai learn` commands in SOUL.md omit `--persona`: on the VM, `SAKTHAI_HOME` already scopes them. In a local shell, add `--persona saksit`, or the fact lands in the unscoped `~/.sakthai/memory.db`.

---

## 🛡️ Keep It Healthy

```bash
sakthai memory --persona saksit healthcheck
sakthai memory --persona saksit backup
```

---

## 📋 Verified Execution Log

_Nothing recorded yet._ Add an entry only for something that ran and can be checked: the date, the command, and its result.

---

*SakSit Memory Node · House of Sak*
