/**
 * The two browser-owned stores behind the shell's preferences and routing.
 *
 * Worth testing directly because both are `useSyncExternalStore` wrappers:
 * the failure mode is not a wrong pixel but a value that never updates, or a
 * server snapshot that disagrees with the client and breaks hydration.
 */

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { useHashRoute, usePersistedString } from "@/lib/browser-state";

describe("usePersistedString", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("falls back when nothing is stored", () => {
    const { result } = renderHook(() => usePersistedString("pref", "off"));
    expect(result.current[0]).toBe("off");
  });

  it("reads a value written before the hook mounted", () => {
    window.localStorage.setItem("pref", "on");
    const { result } = renderHook(() => usePersistedString("pref", "off"));
    expect(result.current[0]).toBe("on");
  });

  it("persists and re-renders on a write", () => {
    const { result } = renderHook(() => usePersistedString("pref", "off"));
    act(() => result.current[1]("on"));
    expect(result.current[0]).toBe("on");
    expect(window.localStorage.getItem("pref")).toBe("on");
  });

  it("keeps two hooks on the same key in step", () => {
    const first = renderHook(() => usePersistedString("shared", "a"));
    const second = renderHook(() => usePersistedString("shared", "a"));
    act(() => first.result.current[1]("b"));
    expect(second.result.current[0]).toBe("b");
  });

  it("keeps different keys independent", () => {
    const one = renderHook(() => usePersistedString("one", "1"));
    const two = renderHook(() => usePersistedString("two", "2"));
    act(() => one.result.current[1]("changed"));
    expect(two.result.current[0]).toBe("2");
  });

  it("degrades to the fallback when storage is unavailable", () => {
    const getItem = window.localStorage.getItem;
    window.localStorage.getItem = () => {
      throw new Error("SecurityError: site data blocked");
    };
    try {
      const { result } = renderHook(() => usePersistedString("pref", "fallback"));
      expect(result.current[0]).toBe("fallback");
    } finally {
      window.localStorage.getItem = getItem;
    }
  });
});

describe("useHashRoute", () => {
  afterEach(() => {
    window.location.hash = "";
  });

  it("falls back when the fragment is empty", () => {
    const { result } = renderHook(() => useHashRoute("overview"));
    expect(result.current[0]).toBe("overview");
  });

  it("reads the fragment already in the URL", () => {
    window.location.hash = "#memory";
    const { result } = renderHook(() => useHashRoute("overview"));
    expect(result.current[0]).toBe("memory");
  });

  it("writes the fragment and re-renders", () => {
    const { result } = renderHook(() => useHashRoute("overview"));
    act(() => result.current[1]("audit"));
    expect(window.location.hash).toBe("#audit");
    expect(result.current[0]).toBe("audit");
  });

  it("does not push a duplicate entry for the current section", () => {
    window.location.hash = "#audit";
    const { result } = renderHook(() => useHashRoute("overview"));
    const before = window.history.length;
    act(() => result.current[1]("audit"));
    expect(window.history.length).toBe(before);
  });
});
