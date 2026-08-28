import type { Config } from "tailwindcss";

/**
 * Every colour here resolves to a CSS variable defined in `globals.css`, one
 * set per theme. That indirection is what makes `bg-panel` correct in both
 * themes without a single `dark:` variant in a component.
 *
 * The `<alpha-value>` placeholder is Tailwind's: it lets `bg-panel/70` keep
 * working, which the glass surfaces depend on.
 */
const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  // `class`, and the class is set on <html> by the inline script in layout.tsx.
  // Nothing uses a `dark:` variant any more — the tokens carry the theme — but
  // leaving the strategy explicit keeps a stray one from following the OS
  // instead of the user's choice.
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Surfaces.
        canvas: token("canvas"),
        sunken: token("sunken"),
        panel: token("panel"),
        raised: token("raised"),
        "raised-2": token("raised-2"),

        // Hairlines. `border-line` rather than overriding Tailwind's `border`
        // colour, so `border` alone stays the width utility it has always been.
        line: token("line"),
        "line-strong": token("line-strong"),
        "line-soft": token("line-soft"),

        // Text.
        fg: token("fg"),
        "fg-2": token("fg-2"),
        "fg-3": token("fg-3"),
        "fg-4": token("fg-4"),
        "fg-5": token("fg-5"),

        // Brand accent.
        accent: token("accent"),
        "accent-strong": token("accent-strong"),
        "accent-contrast": token("accent-contrast"),

        // Status and category hues, three roles each: see globals.css.
        // Nested under `hue` so Tailwind's own colour names stay intact:
        // the two brand gradients (the logo tile and the success bar) still
        // name real shades, because a fixed gradient reads on either canvas.
        hue: {
          cyan: token("h-cyan"),
          "cyan-tint": token("h-cyan-tint"),
          "cyan-line": token("h-cyan-line"),
          emerald: token("h-emerald"),
          "emerald-tint": token("h-emerald-tint"),
          "emerald-line": token("h-emerald-line"),
          rose: token("h-rose"),
          "rose-tint": token("h-rose-tint"),
          "rose-line": token("h-rose-line"),
          amber: token("h-amber"),
          "amber-tint": token("h-amber-tint"),
          "amber-line": token("h-amber-line"),
          violet: token("h-violet"),
          "violet-tint": token("h-violet-tint"),
          "violet-line": token("h-violet-line"),
          purple: token("h-purple"),
          "purple-tint": token("h-purple-tint"),
          "purple-line": token("h-purple-line"),
          sky: token("h-sky"),
          "sky-tint": token("h-sky-tint"),
          "sky-line": token("h-sky-line"),
          teal: token("h-teal"),
          "teal-tint": token("h-teal-tint"),
          "teal-line": token("h-teal-line"),
          fuchsia: token("h-fuchsia"),
          "fuchsia-tint": token("h-fuchsia-tint"),
          "fuchsia-line": token("h-fuchsia-line"),
          blue: token("h-blue"),
          "blue-tint": token("h-blue-tint"),
          "blue-line": token("h-blue-line"),
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        display: ["var(--font-outfit)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glass: "var(--shadow-panel)",
      },
      spacing: {
        // The density-toggle rhythm, so a panel can lay out on `gap-gap` and
        // `p-pad` and tighten with the setting rather than with a class swap.
        gap: "var(--gap)",
        pad: "var(--pad)",
      },
    },
  },
  plugins: [],
};

export default config;
