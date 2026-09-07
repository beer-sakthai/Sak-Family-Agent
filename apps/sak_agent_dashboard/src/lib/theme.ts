/**
 * Theme, density and presentation: the document-level display preferences.
 *
 * Each is stored in `localStorage` and mirrored onto `<html>` as a data
 * attribute, which is what the token blocks in `globals.css` key off. Keeping
 * the attribute — not a React context — as the source of truth means the
 * inline bootstrap below can set the correct theme before first paint, with no
 * hydration disagreement to reconcile afterwards.
 */

export const THEMES = ["system", "light", "dark"] as const;
export type Theme = (typeof THEMES)[number];

export const DENSITIES = ["comfortable", "compact"] as const;
export type Density = (typeof DENSITIES)[number];

export const THEME_STORAGE_KEY = "sak-dashboard:theme";
export const DENSITY_STORAGE_KEY = "sak-dashboard:density";
export const PRESENTATION_STORAGE_KEY = "sak-dashboard:presentation";

export function isTheme(value: unknown): value is Theme {
  return typeof value === "string" && (THEMES as readonly string[]).includes(value);
}

export function isDensity(value: unknown): value is Density {
  return typeof value === "string" && (DENSITIES as readonly string[]).includes(value);
}

/**
 * Apply a theme to the document.
 *
 * "system" removes the attribute rather than resolving the preference to a
 * concrete value, so the `prefers-color-scheme` block in `globals.css` takes
 * over and the page keeps following the OS as it changes — no media-query
 * listener needed.
 */
export function applyTheme(theme: Theme, root: HTMLElement): void {
  if (theme === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", theme);
  }
}

/** Density has no "system" equivalent, so it is always an explicit attribute. */
export function applyDensity(density: Density, root: HTMLElement): void {
  root.setAttribute("data-density", density);
}

/**
 * Presentation mode: the figures without the chrome.
 *
 * For a wall-mounted tab, where the sidebar, the auto-refresh select and the
 * sample-data toggle are dead pixels — nobody is going to click them from
 * across the room. Expressed as an attribute rather than a prop because the
 * elements it hides (`[data-chrome]`) span the whole shell, and the off state
 * removes the attribute so the default costs no CSS at all.
 */
export function applyPresentation(presenting: boolean, root: HTMLElement): void {
  if (presenting) {
    root.setAttribute("data-presentation", "on");
  } else {
    root.removeAttribute("data-presentation");
  }
}

/**
 * What the browser will actually render for a given setting.
 *
 * Used for the toggle's icon and for `<meta name="theme-color">`, both of which
 * need a concrete answer where the setting itself may be "system".
 */
export function resolveTheme(theme: Theme, prefersLight: boolean): "light" | "dark" {
  if (theme === "light" || theme === "dark") return theme;
  return prefersLight ? "light" : "dark";
}

/**
 * The pre-hydration bootstrap, injected into <head>.
 *
 * Without this the server sends dark markup, the client reads `localStorage`
 * after hydration, and a reader who chose light gets a dark flash on every
 * navigation. Deliberately tiny, dependency-free and wrapped in try/catch:
 * `localStorage` throws outright in some privacy modes, and a theme preference
 * is never worth a blank page.
 */
export const THEME_BOOTSTRAP = `(function(){try{
var d=document.documentElement;
var t=localStorage.getItem(${JSON.stringify(THEME_STORAGE_KEY)});
if(t==="light"||t==="dark"){d.setAttribute("data-theme",t)}
var n=localStorage.getItem(${JSON.stringify(DENSITY_STORAGE_KEY)});
d.setAttribute("data-density",n==="compact"?"compact":"comfortable");
if(localStorage.getItem(${JSON.stringify(PRESENTATION_STORAGE_KEY)})==="on"){d.setAttribute("data-presentation","on")}
}catch(e){}})();`;
