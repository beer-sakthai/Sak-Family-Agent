/**
 * Persona portraits: one per persona, identical to the README's.
 *
 * The dashboard serves its own copies from `public/personas/` because Vercel
 * builds this app from its own directory and cannot reach `docs/`. Two copies
 * drift unless something checks them, so this does.
 */

import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PersonaAvatar from "@/components/PersonaAvatar";
import { PERSONA_NAMES } from "@/lib/contracts.generated";

const APP_ROOT = path.resolve(__dirname, "..", "..");
const PUBLIC_DIR = path.join(APP_ROOT, "public", "personas");
const README_DIR = path.join(APP_ROOT, "..", "..", "docs", "images", "personas");

describe("persona portraits", () => {
  it("has exactly one portrait per persona", () => {
    const files = readdirSync(PUBLIC_DIR).sort();
    expect(files).toEqual(PERSONA_NAMES.map((name) => `${name}.svg`).sort());
  });

  it.each(PERSONA_NAMES)("serves the README's portrait of %s, byte for byte", (name) => {
    const served = readFileSync(path.join(PUBLIC_DIR, `${name}.svg`), "utf8");
    const readme = readFileSync(path.join(README_DIR, `${name}.svg`), "utf8");
    expect(served).toBe(readme);
  });

  it.each(PERSONA_NAMES)("keeps the portrait of %s self-contained", (name) => {
    const svg = readFileSync(path.join(PUBLIC_DIR, `${name}.svg`), "utf8");
    // Served as a static file under a CSP of img-src 'self': an external
    // reference would be blocked, and a script has no business in a picture.
    expect(svg).not.toMatch(/<script|href=|url\((?!#)/);
    expect(svg).toContain("<title");
  });
});

describe("PersonaAvatar", () => {
  it("renders the portrait for a known persona, decorative and sized", () => {
    render(<PersonaAvatar name="saksee" size={32} />);
    const img = screen.getByTestId("persona-avatar-saksee");
    expect(img.tagName).toBe("IMG");
    expect(img).toHaveAttribute("src", "/personas/saksee.svg");
    expect(img).toHaveAttribute("alt", "");
    expect(img).toHaveAttribute("width", "32");
    expect(img).toHaveAttribute("height", "32");
  });

  it("falls back to a neutral chip, not a broken image, for an unknown name", () => {
    render(<PersonaAvatar name="unattributed" size={24} />);
    const chip = screen.getByTestId("persona-avatar-unattributed");
    expect(chip.tagName).toBe("SPAN");
    expect(chip.querySelector("img")).toBeNull();
    expect(chip).toHaveStyle({ width: "24px", height: "24px" });
  });
});
