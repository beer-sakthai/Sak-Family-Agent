import '@testing-library/jest-dom/vitest'

// recharts' ResponsiveContainer needs a ResizeObserver, which jsdom doesn't implement.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverStub
