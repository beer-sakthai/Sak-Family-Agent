import '@testing-library/jest-dom/vitest'

// recharts' ResponsiveContainer needs a ResizeObserver, which jsdom doesn't implement.
if (!globalThis.ResizeObserver) {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub
}
