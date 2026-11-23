# A2UI Generative UI & Trust-Boundary Contract

## Server Validation
- Attach `a2ui({ catalog: 'basic', validate: 'strict' })` (or a registered `loadCatalog()` custom catalog) so malformed A2UI v0.9 envelopes (`createSurface`, `updateComponents`, `updateDataModel`) fail immediately during evaluation rather than silently dropping in production.
- Remember that `validate: 'strict'` checks envelope structure and component references, **not** property value safety.

## Client Sanitization & Data-Model Isolation
- **Untrusted output rule:** Treat every `application/a2ui+json` payload as untrusted. Sanitize `Image.url` schemes and escape raw HTML inside `Text` Markdown renderers.
- **CSP:** Enforce strict `img-src` and `fetch` Content Security Policy directives on web clients.
- **Zero secrets in `{ path }` bindings:** Because `actionToMessage()` returns bound `{ path }` values in `action.event.context` on subsequent user turns, never place API tokens, session secrets, or private identifiers in the surface data model.

