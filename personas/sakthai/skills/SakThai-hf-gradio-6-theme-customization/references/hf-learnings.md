# HF Learnings: Gradio 6 Theme Customization (Topic #276)

## Summary
Complete reference for Gradio 6's theming system — 200+ CSS variables across 10 categories,
10 color presets with 11 shades each, 3 size dimensions (spacing/radius/text) with 7 tiers,
font management (Google Fonts + local), dark mode auto-inheritance, Hub theme publishing,
and the `*var` reference system for DRY theme definitions.

## Source
- `gradio/themes/base.py` — ThemeClass + Base + set() API
- `gradio/themes/default.py` — Default theme definition
- `gradio/themes/utils/colors.py` — Color class + 10 presets
- `gradio/themes/utils/fonts.py` — Font, GoogleFont, LocalFont classes
- `gradio/themes/utils/sizes.py` — Size class + spacing/radius/text presets
- `js/theme/src/colors.ts` — Tailwind color bridges
- `gradio/themes/<name>.py` — 10+ preset themes

## Key Architecture
1. **ThemeClass** — generates `:root { --var: val; }` and `:root.dark { ... }` CSS blocks
   from Python class attributes using `_get_theme_css()`
2. **Base** — 200+ CSS variables via `set()` method, 3 hue parameters that expand to
   11 shades each, 3 size dimensions, 2 font families
3. **Default/Soft/etc.** — concrete themes that call `super().__init__()` then
   override specifics via `self.set()`

## Critical Details
- Reference syntax: `*variable_name` in values becomes `var(--variable-name)` in CSS
- Dark mode: every CSS var has `_dark` suffix variant; `None` means skip (inherit light)
- Built-in themes (10): Default, Soft, Monochrome, Citrus, Glass, Ocean, Ember,
  Cyberpunk, Mario, Rose
- Theme JSON versioning uses semver; stored in `themes/theme_schema@<version>.json`
- `from_hub()` supports semver range expressions like `@^1.0` or `@>=2.0`
- Custom colors created via `colors.Color(c50, ..., c950, name="name")`

## Value Ranges
- **Colors**: 10 presets × 11 shades (c50=lightest, c950=darkest)
- **Size tiers**: xxs, xs, sm, md, lg, xl, xxl (7 per dimension)
- **Button size presets**: small, medium, large (each has padding, radius, text-size,
  text-weight)
- **Shadow**: spread uses `shadow_spread` (default 2px, 3px dark)

## Practical Patterns
- Fast customization: `gr.themes.Default(primary_hue="green")`
- Fine control: `theme.set(input_radius="8px", block_padding="16px")`
- Load from Hub: `gr.Blocks(theme="user/theme-name")`
- Dark-only override: `theme.set(error_border_color_dark=None)` inherits light value
