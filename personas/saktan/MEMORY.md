# MEMORY.md — SakTan 📗
> *Schedule, alarms, rhythm, health checks, eval aggregation — Memory Store*

---

## 🧠 Where My Memory Lives

- **My shard**: `~/.sakthai/saktan/memory.db`. Locally that is `--persona saktan`; on the VM, `infra/vm-agents/sakthai-agent-run.sh` sets `SAKTHAI_HOME=$HOME/.sakthai/saktan`, which resolves to the same file.
- **The family**: `sakthai memory family` reads all six shards plus the legacy `~/.sakthai/memory.db`.
- **This file is not the store.** Facts live in the shard; this file keeps the bindings and verified events worth keeping in the repository.
- The shard is created on its first write.

---

## 📖 Read

```bash
sakthai recall --persona saktan "<query>"
sakthai memory --persona saktan show
sakthai memory --persona saktan stats
```

Family reads (SOUL.md, Family duties):

```bash
sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1
sakthai memory family --tag rate-limit-ban --personas saksee --limit 50
sakthai memory family "CYCLE PAUSED: saksit" --tag cycle-paused --tag awaiting-beer --limit 20
sakthai learn "SCHEDULE REQUEST: <job> | cron: <expression> | why: <reason> | timestamp: <ISO>" \
  --kind observation --tag schedule-request --tag saktan
sakthai memory family --tag schedule-confirmed --personas sakjules --limit 20
```

---

## ✍️ Write

```bash
sakthai learn --persona saktan "<fact>" --tag saktan --tag <topic>
```

The `sakthai learn` commands in SOUL.md omit `--persona`: on the VM, `SAKTHAI_HOME` already scopes them. In a local shell, add `--persona saktan`, or the fact lands in the unscoped `~/.sakthai/memory.db`.

---

## 🛡️ Keep It Healthy

```bash
sakthai memory --persona saktan healthcheck
sakthai memory --persona saktan backup
```

---

## 📋 Verified Execution Log

_Nothing recorded yet._ Add an entry only for something that ran and can be checked: the date, the command, and its result.

---

*SakTan Memory Node · House of Sak*
