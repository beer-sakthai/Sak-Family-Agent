# Component Gallery and Detailed Design Specs

## HTML / CSS / JS Standards

Use modern CSS well:

- CSS variables for tokens
- CSS grid for layout
- container queries when helpful
- `text-wrap: pretty` where supported
- real focus states
- real hover states
- `prefers-reduced-motion` handling for non-trivial motion
- responsive scaling
- semantic HTML where practical

Avoid:

- huge monolithic files when a real repo structure is expected
- fragile hard-coded viewport assumptions
- inaccessible tiny hit targets
- decorative JS that fights usability
- `scrollIntoView` unless there is no safer option

Mobile hit targets should be at least 44px.

For print documents, text should be at least 12pt.

For 1920×1080 slide decks, text should generally be 24px or larger.

## React Guidance for Standalone HTML

Use plain HTML/CSS/JS by default.

Use React only when:

- the artifact needs meaningful state
- variants/toggles are easier as components
- interaction complexity warrants it
- the target implementation is React/Next.js and fidelity matters

If using React from CDN in standalone HTML:

- pin exact versions
- avoid unpinned `react@18` style URLs
- avoid `type="module"` unless necessary
- avoid multiple global objects named `styles`
- give global style objects specific names, e.g. `commandPaletteStyles`, `deckStyles`
- if splitting Babel scripts, explicitly attach shared components to `window`

If building inside a real repo, use the repo's package manager and component architecture instead.

## Deck Rules

For slide decks, use a fixed-size canvas and scale it to fit the viewport.

Default slide size: 1920×1080, 16:9.

Requirements:

- keyboard navigation
- visible slide count
- localStorage persistence for current slide
- print-friendly layout when practical
- screen labels or stable IDs for important slides
- no speaker notes unless the user explicitly asks

Do not hand-wave a deck as markdown bullets. Create a designed artifact if asked for a deck.

Use 1–2 background colors max unless the brand system requires more.

Keep slides sparse. If a slide feels empty, solve it with layout, rhythm, scale, or imagery placeholders, not filler text.

## Prototype Rules

For interactive prototypes:

- make the primary path clickable
- include key states: default, hover/focus, loading, empty, error, success where relevant
- expose variations with in-page controls when useful
- keep controls out of the final composition unless they are intentionally part of the prototype
- persist important state in localStorage when refresh continuity matters

If the prototype is meant to model a product flow, design the flow, not just the first screen.

## Variation Rules

When exploring, default to at least three options:

1. **Conservative** — closest to existing patterns / lowest risk
2. **Strong-fit** — best interpretation of the brief
3. **Divergent** — more novel, useful for discovering taste boundaries

Variations can explore:

- layout
- hierarchy
- type scale
- density
- color posture
- surface treatment
- motion
- interaction model
- copy structure
- component shape

Do not create variations that are merely color swaps unless color is the actual question.

When the user picks a direction, consolidate. Do not leave the project as a pile of options forever.

## Tweakable Designs in CLI/API Mode

The hosted Claude Design edit-mode toolbar does not exist here.

Still preserve the idea: when useful, add in-page controls called `Tweaks`.

A good `Tweaks` panel can control:

- theme mode
- layout variant
- density
- accent color
- type scale
- motion on/off
- copy variant
- component variant

Keep it small and unobtrusive. The design should look final when tweaks are hidden.

Persist tweak values with localStorage when helpful.

## Content Discipline

Do not add filler content.

Every element must earn its place.

Avoid:

- fake metrics
- decorative stats
- generic feature grids
- unnecessary icons
- placeholder testimonials
- AI-generated fluff sections
- invented content that changes strategy or claims

If additional sections, pages, copy, or claims would improve the artifact, ask before adding them.

When copy is necessary but not final, mark it as draft or placeholder.

## Anti-Slop Rules

Avoid common AI design sludge:

- aggressive gradient backgrounds
- glassmorphism by default
- emoji unless the brand uses them
- generic SaaS cards with icons everywhere
- left-border accent callout cards
- fake dashboards filled with arbitrary numbers
- stock-photo hero sections
- oversized rounded rectangles as a substitute for hierarchy
- rainbow palettes
- vague labels like “Insights,” “Growth,” “Scale,” “Optimize” without content
- decorative SVG illustrations pretending to be product imagery

Minimal is not automatically good. Dense is not automatically cluttered. Choose intentionally.

## Slop Diagnostic: Score Before You Fix

AI design slop has a tiny, predictable failure distribution — designers asked to label AI UIs collapse the "this is AI" signal down to about ten tells. Before polishing or repairing an artifact, run this as an explicit self-audit and write a short report. **Diagnose first, treat second** — auditing and fixing in one breath fails, because the model's prior outweighs the instruction and it repeats the mistake (recolors when it needed re-layout, polishes type on a composition problem).

The ten tells (presence of each = one point of slop; lower is better):

1. **Tech gradient** — blue/violet/indigo glossy gradient on everything.
2. **Generic tech hue** — the default accent is indigo/violet (not chosen for the brand, just the model's favorite).
3. **Feature-tile grid** — icon + heading + sentence × 3, all equal weight, nothing prioritized.
4. **Accent rail** — a colored left strip on cards: decoration pretending to be organization.
5. **Unearned blur** — glassmorphism with no real depth/elevation system behind it.
6. **Monument stat** — oversized numbers filling space that should carry product story.
7. **Icon topper** — a rounded-square icon centered above every heading (Tailwind-template filler).
8. **Center stack** — everything centered because no real composition was committed to.
9. **Default type** — Inter (or system-ui) used by default rather than chosen.
10. **Wrong surface** — the composition doesn't match the surface (e.g. a hero on a Monitor surface). This is the root cause behind most of the others.

How to run it:

- Score the artifact out of 10 (10 = maximum slop). State the score and list which tells fired, in one short report.
- Treat the report as **context, not a to-do list** — it tells you *where* to spend repair effort, it does not dictate edits.
- Then repair, matched to the diagnosis:
  - tells 3, 8, 10 → **re-layout / re-compose** (revisit the surface choice — do not recolor).
  - tells 1, 2, 9 → **recolor / re-typeset** (palette and type are genuinely the problem here).
  - tells 4, 5, 6, 7 → **remove the decoration**; replace it with real hierarchy (scale, weight, spacing).
- Re-score after repairing. Do not declare done while compositional tells (3, 8, 10) are still firing — those are causes, the rest are usually symptoms.

The point of separating diagnosis from treatment: let the audit complain first, then fix only what it complained about, in the register the complaint calls for.

## Typography

Use the existing type system if one exists.

If not, choose type deliberately based on the artifact:

- editorial: serif or humanist headline with restrained sans body
- software/productivity: precise sans with strong numeric treatment
- luxury/minimal: fewer weights, more spacing discipline
- technical: mono accents only, not mono everywhere
- deck: large, clear, high contrast

Avoid overused defaults when a stronger choice is appropriate.

If using web fonts, keep the number of families and weights low.

Use type as hierarchy before adding boxes, icons, or color.

## Color

Use brand/design-system colors first.

If no palette exists:

- define a small system
- include neutrals, surface, ink, muted text, border, accent, danger/success if needed
- use one primary accent unless the assignment calls for a broader palette
- prefer oklch for harmonious invented palettes when browser support is acceptable
- check contrast for important text and controls

Do not invent lots of colors from scratch.

## Layout and Composition

Design with rhythm:

- scale
- whitespace
- density
- alignment
- repetition
- contrast
- interruption

Avoid making every section the same card grid.

For product UIs, prioritize speed of comprehension over decoration.

For marketing surfaces, make one idea land per section.

For dashboards, avoid “data slop.” Only show data that helps the user decide or act.

## Motion

Use motion as discipline, not theater.

Good motion:

- clarifies state changes
- reduces anxiety during loading
- shows continuity between surfaces
- gives controls tactility
- stays subtle

Bad motion:

- loops without purpose
- delays the user
- calls attention to itself
- hides poor hierarchy

Respect `prefers-reduced-motion` for non-trivial animation.

## Images and Icons

Use real supplied imagery when available.

If an asset is missing:

- use a clean placeholder
- use typography, layout, or abstract texture instead
- ask for real material when fidelity matters

Do not draw elaborate fake SVG illustrations unless the assignment is explicitly illustration work.

Avoid iconography unless it improves scanning or matches the design system.

## Source-Code Fidelity

When recreating or extending a UI from a repo:

1. inspect the repo tree
2. identify the actual UI source files
3. read theme/token/global style/component files
4. lift exact values where appropriate
5. match spacing, radii, shadows, copy tone, density, and interaction patterns
6. only then design or modify

Do not build from memory when source files are available.

For GitHub URLs, parse owner/repo/ref/path correctly and inspect the relevant files before designing.

## Reading Documents and Assets

Read Markdown, HTML, CSS, JS, TS, JSX, TSX, JSON, SVG, and plain text directly when available.

For DOCX/PPTX/PDF, use available local extraction tools if present. If not available, ask the user to provide exported text/images or use another available tool path.

For sketches, prioritize thumbnails or screenshots over raw drawing JSON unless the JSON is the only usable source.

## Copyright and Reference Models

Do not recreate a company's distinctive UI, proprietary command structure, branded screens, or exact visual identity unless the user clearly has rights to that source.

It is acceptable to extract general design principles:

- density without clutter
- command-first interaction
- monochrome with one accent
- editorial hierarchy
- clear empty states
- strong keyboard affordances

It is not acceptable to clone proprietary layouts, copy exact branded surfaces, or reproduce copyrighted content.

When using references, transform posture and principles into an original design.

## Verification

Before final response, verify as much as the environment allows.

Minimum:

- file exists at the stated path
- HTML is saved completely
- obvious syntax issues are checked

Better:

- open in a browser tool and check console errors
- inspect screenshots at the primary viewport
- test key interactions
- test light/dark or variants if present
- test responsive breakpoints if relevant

If verification is limited by environment, say exactly what was and was not verified.

Never say “done” if the file was not actually written.

## Final Response Format

Keep final responses short.

Include:

- artifact path
- what it contains
- verification status
- next suggested action, if useful

Example:

```text
Created: /path/to/Prototype.html
It includes 3 layout variants, a Tweaks panel for density/theme, and responsive behavior.
Verified: file exists and opened cleanly in browser, no console errors.
Next: pick the strongest direction and I’ll tighten copy + motion.
```

## Portable Opening Prompt Pattern

When adapting a Claude Design style request into CLI/API mode, use this mental translation:

```text
You are running in CLI/API mode, not hosted Claude Design. Ignore references to hosted-only tools or preview panes. Produce complete local design artifacts, usually self-contained HTML with embedded CSS/JS, and verify with available local tools before returning. Preserve the design process: gather context, define the system, produce options, avoid filler, and meet a high visual bar.
```

## Pitfalls

- Do not paste hosted tool schemas into a skill. They cause fake tool calls.
- Do not point the skill at a giant external prompt as required runtime context. That creates drift.
- Do not strip the design doctrine while removing tool plumbing.
- Do not over-ask when the user already gave enough direction.
- Do not under-ask for high-fidelity work with no brand context.
- Do not produce generic SaaS layouts and call them designed.
- Do not claim browser verification unless it actually happened.