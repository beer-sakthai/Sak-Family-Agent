// The Vitest entry point augments Vitest's Assertion interface as well as
// registering the DOM matchers at runtime. The generic entry point only
// declares Jest's matcher types, which let tests run but makes `next build`
// reject every `toBeInTheDocument` / `toHaveAttribute` assertion.
import "@testing-library/jest-dom/vitest";

// Polyfill ResizeObserver for JSDOM / Recharts testing
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Polyfill matchMedia for responsive UI components
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => true,
  }),
});
