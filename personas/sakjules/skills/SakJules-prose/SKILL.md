---
name: SakJules-prose
version: 1.1.0
description: OpenProse virtual machine dispatch protocol for multi-agent workflows and prose program orchestration.
category: devops
tags:
- automation
- prose
---

# OpenProse Dispatch Protocol

Operational protocol for executing, compiling, and managing OpenProse multi-agent programs within the agent runtime.

## 1. Activation & Intent Routing
Activate on any `prose` command, `.prose` files, or multi-agent pipeline mentions:
| Command | Primary Action | Target Document |
|---|---|---|
| `prose help` | Display syntax and guide | [Help Guide](help.md) |
| `prose run <file>` | Simulate and run Prose VM | [Prose Spec](prose.md) |
| `prose compile <file>` | Validate syntax & static types | [Compiler Spec](compiler.md) |
| `prose examples` | Review sample workflows | [Examples](examples/) |

## 2. OpenClaw Runtime Mapping
- Task Tool $\to$ `sessions_spawn` / `invoke_subagent`
- File I/O $\to$ Standard file read / write tools
- Remote Fetch $\to$ `web_fetch` or `curl`

## 3. Execution Lifecycle
1. **Validate**: Run compiler preflight on target script.
2. **Initialize VM**: Load state primitives from `primitives/` and `state/`.
3. **Execute**: Step through program nodes sequentially or in designated parallel blocks.
4. **State Persistence**: Store session checkpoint to disk or memory store upon completion.

## 4. References & Documentation
- Core VM Specification: [OpenProse Spec](prose.md)
- Compiler & AST Validator: [Compiler](compiler.md)
- Command Line Guide: [Help Reference](help.md)
- Agent Personas & Alternatives: [Borges Alternate](alt-borges.md) | [Alts Directory](alts/)
- Implementation Libraries: [Guidance](guidance/) | [Primitives](primitives/) | [Libraries](lib/)
