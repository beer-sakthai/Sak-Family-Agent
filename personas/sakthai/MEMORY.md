# MEMORY.md — SakThai 🤗
> *Hugging Face Hub, Model Lifecycle, 6-Stage Energy Cycle, QLoRA — Memory Store*

---

## 🧠 Where My Memory Lives

- **My shard**: `~/.sakthai/sakthai/memory.db`. Locally that is `--persona sakthai`; on the VM, `infra/vm-agents/sakthai-agent-run.sh` sets `SAKTHAI_HOME=$HOME/.sakthai/sakthai`, which resolves to the same file.
- **The family**: `sakthai memory family` reads all six shards plus the legacy `~/.sakthai/memory.db`.
- **This file is not the store.** Facts live in the shard; this file keeps the bindings and verified events worth keeping in the repository.
- The shard is created on its first write.

---

## 📖 Read

```bash
sakthai recall --persona sakthai "<query>"
sakthai memory --persona sakthai show
sakthai memory --persona sakthai stats
```

Pre-task checklist (SOUL.md):

```bash
sakthai memory family "CHARGE: sakthai" --tag charge-report --limit 1
sakthai memory family "HOUSEHOLD CHARGE SUMMARY" --tag charge-summary --limit 1
sakthai memory family "CONSERVATION MODE" --tag conservation-mode --limit 1
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family "CYCLE INTERRUPTED: sakthai" --tag cycle-interrupted --tag sakthai --tag resumable --limit 1
```

---

## ✍️ Write

```bash
sakthai learn --persona sakthai "<fact>" --tag sakthai --tag <topic>
```

The `sakthai learn` commands in SOUL.md omit `--persona`: on the VM, `SAKTHAI_HOME` already scopes them. In a local shell, add `--persona sakthai`, or the fact lands in the unscoped `~/.sakthai/memory.db`.

---

## 🛡️ Keep It Healthy

```bash
sakthai memory --persona sakthai healthcheck
sakthai memory --persona sakthai backup
```

---

## 📋 Verified Execution Log

_Nothing recorded yet._ Add an entry only for something that ran and can be checked: the date, the command, and its result.

---

*SakThai Memory Node · House of Sak*
