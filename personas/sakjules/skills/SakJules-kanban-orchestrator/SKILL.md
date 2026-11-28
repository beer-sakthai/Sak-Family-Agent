---
name: SakJules-kanban-orchestrator
version: 1.1.0
description: Multi-agent Kanban task decomposition and DAG orchestration protocol for distributed workflows.
category: devops
tags:
- automation
- kanban
- orchestrator
---

# Kanban Orchestrator Protocol

Standard operating procedure for task decomposition, dependency graphing, and asynchronous multi-agent coordination.

## 1. Orchestrator Invariants
- **Route, Don't Execute**: Decompose goals into distinct tasks for specialist workers rather than performing monolithic execution.
- **Roster Grounding**: Discover available profiles (`hermes profile list`) prior to task creation. Never assign tasks to unverified profile names.
- **Explicit DAG Dependencies**: Wire sequential tasks using `parents=[task_id]` upon creation. Leave parallel workstreams unlinked.

## 2. Decomposition Process
1. **Scope Intake**: Identify distinct workstreams (e.g. Research, Scaffolding, Implementation, Review).
2. **Assignee Mapping**: Map each workstream to a verified specialist agent.
3. **Graph Construction**:
   - Dispatch independent lanes as parallel tasks.
   - Attach integration/review tasks with explicit parent IDs.
4. **Monitoring & Synthesis**: Track card transitions (`ready` $\to$ `in_progress` $\to$ `done`) and report aggregated status back to user.

## 3. References & Schemas
- Python API recipes, state machine transitions, and fan-out examples: [Kanban State Machine](references/kanban-state-machine.md)
