# Product Decision

## Decision

Build Sak Family as a **business-first AI team platform** with **customer-specific packaging**.

The shared core should serve three modes:
- business
- personal
- family

Business is the primary target because it gives the clearest ROI, simplest pricing,
and strongest path to paid deployments. Personal and family use stay supported as
lighter-weight customer modes, but they do not drive the core roadmap.

## Why This Direction

- Business customers can justify paying for time saved, leads captured, and support reduced.
- The current repository already fits a reusable agent-platform model, not a single consumer app.
- One shared core with persona-specific deployment keeps the project flexible without fragmenting it.

## Product Shape

- **Core platform:** shared Sak Family agents, memory, tools, and export scaffolding.
- **Primary product:** business-facing Telegram or chat-based agents.
- **Secondary modes:** personal assistant and family assistant variants when a customer needs them.

## Non-Goals

- Do not optimize the roadmap for a general consumer app first.
- Do not add framework dependencies unless they directly support the chosen business use case.
- Do not split the repository into separate stacks for business, personal, and family.
