import "@testing-library/jest-dom";

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

// Polyfill EventSource for JSDOM streaming tests
class MockEventSource {
  url: string;
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  private listeners: Record<string, ((ev: unknown) => void)[]> = {};
  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor(url: string) {
    this.url = url;
    this.timer = setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 10);
  }

  addEventListener(type: string, listener: (ev: unknown) => void) {
    if (!this.listeners[type]) this.listeners[type] = [];
    this.listeners[type].push(listener);
  }

  removeEventListener(type: string, listener: (ev: unknown) => void) {
    if (!this.listeners[type]) return;
    this.listeners[type] = this.listeners[type].filter((l) => l !== listener);
  }

  close() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.onopen = null;
    this.onerror = null;
    this.onmessage = null;
  }
}

if (typeof global !== "undefined") {
  (global as unknown as { EventSource: typeof MockEventSource }).EventSource = MockEventSource;
}
if (typeof window !== "undefined") {
  (window as unknown as { EventSource: typeof MockEventSource }).EventSource = MockEventSource;
}

// Mock getBoundingClientRect for JSDOM Recharts rendering
if (typeof HTMLElement !== "undefined") {
  HTMLElement.prototype.getBoundingClientRect = function () {
    return {
      width: 500,
      height: 300,
      top: 0,
      left: 0,
      bottom: 300,
      right: 500,
      x: 0,
      y: 0,
      toJSON: () => {},
    };
  };
}
