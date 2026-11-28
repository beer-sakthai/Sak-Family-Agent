---
name: SakSee-touchdesigner-mcp
version: 1.1.0
description: Real-time TouchDesigner visual generation and node manipulation protocol via twozero MCP server.
category: web-browser
tags:
- browser
- mcp
- touchdesigner
---

# TouchDesigner MCP Protocol

Operational guidelines for controlling TouchDesigner instances, synthesizing visual node networks, and executing Python callbacks via the twozero MCP integration.

## 1. Operating Rules & Invariants
- **Parameter Grounding**: Never guess parameter names. Query `td_get_par_info` for the target operator type first.
- **Error Handling**: On `tdAttributeError`, halt immediately and query `td_get_operator_info`.
- **Relative Addressing**: Prohibit hardcoded absolute paths in DAT callbacks; use `me.parent()` or `scriptOp.parent()`.
- **Native Tools Over Raw Python**: Prioritize `td_create_operator`, `td_set_operator_pars`, and `td_connect_operators` over arbitrary Python execution.

## 2. Setup & Connectivity
```bash
# Verify TouchDesigner hub status (port 40404)
curl -s http://localhost:40404/mcp
```
Run the automated environment setup script if disconnected: [setup.sh](scripts/setup.sh).

## 3. Workflow Steps
1. **Discover**: Call `td_get_hints` for intended network domain (TOP, CHOP, SOP, DAT).
2. **Create & Configure**: Spawn operators and set initial resolution/parameters.
3. **Wire & Connect**: Connect nodes into processing graph.
4. **Validate**: Call `td_get_errors` to ensure zero compilation or parameter faults.

## 4. References & Network Blueprints
- MCP Tool Reference: [MCP Tools](references/mcp-tools.md)
- Network Architectures: [Network Patterns](references/network-patterns.md) | [3D Scenes](references/3d-scene.md) | [Audio-Reactive](references/audio-reactive.md)
- Scripting & External APIs: [DAT Scripting](references/dat-scripting.md) | [Python API](references/python-api.md) | [GLSL](references/glsl.md)
- Troubleshooting & Pitfalls: [Pitfalls](references/pitfalls.md) | [Troubleshooting Guide](references/troubleshooting.md)
