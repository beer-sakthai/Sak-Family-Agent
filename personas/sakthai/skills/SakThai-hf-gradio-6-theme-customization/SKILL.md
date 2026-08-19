---
name: SakThai-hf-gradio-6-theme-customization
description: ">   Complete guide to Gradio 6s theming system \u2014 the theming class hierarchy\
  \   (ThemeClass \u2192 Base \u2192 Default/Soft/Hard), 200+ CSS variables organized\
  \ by   category (body, blocks, inputs, buttons, checkboxes, shadows, text),   color\
  \ palette system (10 "
---

# HF Gradio 6 Theme Customization

## Overview

Gradio 6 ships with a sophisticated theme system built around a three-class
hierarchy that generates CSS custom properties at runtime. All ~200+ CSS
variables are defined as Python class attributes, compiled into `:root { ... }`
and `:root.dark { ... }` blocks, then injected into the page at load time.

Design goals:
- **Zero-config defaults** — `gr.themes.Default()` just works
- **Semantic overrides** — change `primary_hue` to `"green"` and every green
  shade auto-populates
- **Dark mode parity** — every CSS var has a `_dark` twin; setting one to
  `None` falls back to the light value
- **Reference chains** — vars can reference each other via `*variable_name`
  syntax, resolved at `var(--variable-name)` in CSS

## Class Hierarchy

```
ThemeClass         # Base abstract class: CSS generation, dict serialization,
                   #   Hub push/load, computed value resolution
  └── Base         # Constructor: accepts hue, size, font params; defines
                   #   200+ CSS variables via set() with defaults
        └── Default    # Gradio default look: orange primary, blue secondary,
                       #   zinc neutral, Source Sans Pro + IBM Plex Mono
        └── Soft       # Softer, pastel-inspired theme
        └── Monochrome # Grayscale-only variant
        └── Citrus     # Yellow/orange accent theme
        └── Glass      # Frosted glass aesthetic
        └── Ocean      # Blue/teal theme
```

## Core API

### Instantiation

```python
import gradio as gr

# Quick — just pick a hue
theme = gr.themes.Default(primary_hue="green", secondary_hue="teal")

# Full control — every variable
theme = gr.themes.Default(
    primary_hue="blue",
    secondary_hue="purple",
    neutral_hue="zinc",
    spacing_size="md",
    radius_size="md",
    text_size="md",
    font=("Source Sans Pro", "sans-serif"),
    font_mono=("IBM Plex Mono", "monospace"),
)
```

### Applying to app

```python
with gr.Blocks(theme=theme) as demo:
    ...
# Or inline:
with gr.Blocks(theme="freddyaboulton/MyTheme") as demo:
    ...
# Or via gr.Theme:
demo = gr.Interface(fn, inputs, outputs, theme="gradio/theme-name")
```

### The `set()` method

After constructing, call `.set()` to override specific CSS variables:

```python
theme = gr.themes.Default()
theme.set(
    body_background_fill="#f0f0f0",
    body_background_fill_dark="#1a1a1a",
    button_primary_background_fill="*primary_600",
    button_primary_text_color="white",
    input_background_fill="#ffffff",
    block_radius="8px",
)
```

Every `set()` param accepts:
- An **absolute value** like `"#ff6600"` or `"12px"`
- A **reference** like `"*primary_500"` (resolves to `var(--primary-500)`)
- `None` for `_dark` variants (inherits light mode value)

## CSS Variable Categories

### Body & Global (8 vars)
| Variable | Default | Description |
|---|---|---|
| `body-background-fill` | white / neutral-950 | Entire app background |
| `body-text-color` | neutral-900 / white | Default text color |
| `body-text-size` | text-md | Base font size |
| `body-text-color-subdued` | neutral-400 / neutral-500 | De-emphasized text |
| `body-text-weight` | 400 | Base font weight |
| `embed-radius` | 0 | Corner radius when embedded |

### Colors (5 theme vars)
| Variable | Description |
|---|---|
| `color-accent` | Accent color (defaults to primary-500) |
| `color-accent-soft` | Softer accent (primary-50) |
| `border-color-accent` | Accent border color |
| `border-color-accent-subdued` | Softer accent border |
| `border-color-primary` | Default border color |

### Blocks / Layout (~30 vars)
Blocks wrap components: `block-background-fill`, `block-border-color`, `block-padding`,
`block-radius`, `block-shadow`, `block-label-*`, `block-title-*`, `container-radius`,
`layout-gap`, `form-gap-width`, `panel-*`.

### Buttons (~60 vars across 3 button types)
3 categories: `button-primary-*`, `button-secondary-*`, `button-cancel-*`.

Each has:
- `background-fill`, `background-fill-hover`, `border-color`, `text-color`,
  `shadow`, `shadow-hover`, `shadow-active`
- Size variants: `button-large-*`, `button-medium-*`, `button-small-*`
  (padding, radius, text-size, text-weight)

### Inputs (~20 vars)
`input-background-fill`, `input-border-color`, `input-border-color-focus`,
`input-border-color-hover`, `input-border-width`, `input-padding`, `input-radius`,
`input-shadow`, `input-shadow-focus`, `input-placeholder-color`, `input-text-size`,
`input-text-weight`, plus all `_dark` twins.

### Checkbox / Radio (~50 vars)
Fine-grained: `checkbox-background-color`, `checkbox-border-color` (each with
`-focus`, `-hover`, `-selected` variants), `checkbox-check`, `radio-circle`,
`checkbox-label-*` (background, border, text, shadow, padding, gap for each
state), `checkbox-border-radius`, `checkbox-border-width`.

### Shadows (5 base vars)
`shadow-drop`, `shadow-drop-lg`, `shadow-inset`, `shadow-spread`,
`shadow-spread-dark`. Referenced by component shadow vars via `*`.

### Text / Typography (~10 vars)
`link-text-color` (+ `-active`, `-hover`, `-visited`), `prose-text-size`,
`prose-text-weight`, `prose-header-text-weight`, `code-background-fill`,
`accordion-text-color`, `table-text-color`, `chatbot-text-size`,
`section-header-text-size`, `section-header-text-weight`.

### Error / Status (~10 vars)
`error-background-fill`, `error-border-color`, `error-border-width`,
`error-text-color`, `error-icon-color`, `stat-background-fill`,
`slider-color`, `loader-color`.

## Color System

10 preset hues, each with 11 shades (c50–c950):

| Hue | Primary | Secondary |
|---|---|---|
| `red` | c600 | c100 |
| `green` | c600 | c100 |
| `blue` | c600 | c100 |
| `yellow` | c500 | c100 |
| `purple` | c600 | c100 |
| `teal` | c600 | c100 |
| `orange` | c600 | c100 |
| `cyan` | c600 | c100 |
| `lime` | c500 | c100 |
| `pink` | c600 | c100 |

Custom colors via `gr.themes.utils.colors.Color(c50, c100, ..., c950, name)`.

## Size System

Three size dimensions with 7 tiers each (xxs–xxl):

**Radius presets:** `radius_none`(0px–0px), `radius_sm`(1px–12px),
`radius_md`(1px–22px), `radius_lg`(2px–24px), `radius_xxl`(6px–32px)

**Spacing presets:** `spacing_sm`(1px–20px), `spacing_md`(1px–30px),
`spacing_lg`(2px–40px), `spacing_xl`(4px–60px)...

**Text presets:** `text_sm`(10px–20px), `text_md`(10px–24px),
`text_lg`(12px–32px)...

## Theme from Hub

```python
# Load any Space as a theme
theme = gr.themes.ThemeClass.from_hub("user/theme-space")

# Apply by string reference
gr.Blocks(theme="user/theme-space@0.1.0")

# Version locking: "user/theme@^1.0", "user/theme@>=2.0"
```

Hub themes are Gradio Spaces with versioned JSON schemas in `themes/` directory.

## Pushing a Theme to Hub

```python
theme = gr.themes.Default(
    primary_hue="green",
    secondary_hue="teal",
    font=gr.themes.GoogleFont("Inter"),
)
theme.push_to_hub(
    repo_name="my-green-theme",
    version="1.0.0",
    theme_name="Green Glow",
    description="A fresh green Gradio 6 theme",
)
```

Creates a Space with:
1. `themes/theme_schema@1.0.0.json` — serialized theme
2. `app.py` — demo app showing the theme
3. `README.md` — auto-generated with author info

## Adding Custom CSS

```python
with gr.Blocks(css=".my-class { color: red; }") as demo:
    ...

# Or globally via theme
theme.custom_css = """
  .gradio-container { border: 2px solid *primary_500; }
"""
```

## Key Insights

1. **Dark mode is automatic** — every var has a `_dark` twin; set to `None` to
   inherit light mode value
2. **Reference system** (`*var_name`) — keeps themes DRY; a single hue change
   cascades everywhere
3. **10 preset themes** ship with Gradio 6: `Default`, `Soft`, `Monochrome`,
   `Citrus`, `Glass`, `Ocean`, `Ember`, `Cyberpunk`, `Mario`, `Rose`
4. **Version-lock themes** with semver (`@^1.0`) for stability
5. **Theme JSON schema** can be inspected via `.to_dict()` — useful for debugging
6. **Google Fonts** auto-import via `gr.themes.GoogleFont("Inter")` — injects
   `<link>` tag automatically
7. **Theme builder UI** available at `/theme-builder` route when running locally
