# Stitch Design Specification: Agent War Room & Live Multi-Agent Mesh Visualizer

> **Design ID:** `agent_war_room_mesh_visualizer`  
> **Status:** Approved / Enhanced Specification  
> **Target Framework:** Next.js 15, Tailwind CSS, Lucide Icons, SVG Node Mesh  
> **Theme:** Deep Space Cyberpunk / Obsidian Dark (`#020617`, `#0f172a`, `#1e293b`) with Cyan/Emerald/Purple neon accents  

---

## 1. Executive Summary & Design Vision

The **Agent War Room & Multi-Agent Mesh Visualizer** is an operations command center for monitoring, orchestrating, and observing real-time interactions across all 6 Sak-Family personas. It visualizes agent-to-agent message passing, active tool executions, token burn rates, and AST security gate events as an interactive live mesh graph.

---

## 2. Information Architecture & Layout Structure

```
+---------------------------------------------------------------------------------------+
|  WAR ROOM COMMAND HEADER: Status | Concurrency: 6 | Active Handoffs: 3 | AST: 100%    |
+-----------------------------------------------------------+---------------------------+
|                                                           |                           |
|  INTERACTIVE MULTI-AGENT TOPOLOGY MESH GRAPH              |  LIVE INCIDENT & HANDOFF  |
|  - Real-time SVG Canvas with 6 Persona Nodes              |  TELEMETRY FEED           |
|  - Animated glowing bezier message curves                 |  - Chronological trace log|
|  - Particle pulses indicating data packet transfer        |  - Subagent task handoffs |
|  - Hoverable agent state cards (CPU, Memory, Current Step)|  - AST security verdicts  |
|                                                           |                           |
+-----------------------------------------------------------+---------------------------+
|  PERSONA WORKLOAD METERS & TOKEN CONSUMPTION SPEEDOMETERS |  QUICK DISPATCH DOCK      |
|  [Jules: 84%] [See: 98%] [King: 72%] [Tan: 65%] [Thai: 90%] |  - 1-Click Broadcast   |
+---------------------------------------------------------------------------------------+
```

---

## 3. Visual Styling Tokens & Color Hierarchy

- **Background:** `bg-slate-950` with subtle radial grid overlay (`bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]`).
- **Cards & Glassmorphism:** `bg-slate-900/80 border border-slate-800 backdrop-blur-xl shadow-2xl`.
- **Agent Identity Neon Badges:**
  - **SakJules (Automation):** `#3b82f6` (Blue-500)
  - **SakSee (Security Sentinel):** `#10b981` (Emerald-500)
  - **SakKing (Orchestration Leader):** `#8b5cf6` (Purple-500)
  - **SakTan (Data & Analytics):** `#f59e0b` (Amber-500)
  - **SakThai (Architecture & Memory):** `#ec4899` (Pink-500)
  - **SakNoi (Prompt & Creative):** `#06b6d4` (Cyan-500)

---

## 4. Key Interactive Components

### A. Topology Mesh Canvas (`MeshGraph`)
- Rendered using responsive SVG with node coordinates mapped along a circular or force-directed layout.
- Directed quadratic bezier curve paths (`d="M x1 y1 Q cx cy x2 y2"`) connecting agents with animated SVG `stroke-dasharray` and `stroke-dashoffset` simulating live packet flow.
- Visual ping badges on nodes actively processing tool execution turns.

### B. Live Telemetry Ticker & Incident Stream
- Streaming feed showing persona handoff dispatches, latency timestamps, token allocations, and security audit passes.
- Filterable by persona and severity (`INFO`, `HANDOFF`, `WARNING`, `SECURITY_BLOCK`).

### C. Quick War Room Command Bar
- Actions: **"Trigger Cross-Persona Sync"**, **"Simulate Load Spike"**, **"Broadcast Emergency Pause"**, **"Export Trace Graph"**.
