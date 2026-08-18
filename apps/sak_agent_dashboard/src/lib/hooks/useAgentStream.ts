"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { TelemetryEvent, TelemetryEventType } from "@/lib/types";

export type StreamStatus = "connecting" | "connected" | "disconnected" | "error";

interface UseAgentStreamOptions {
  persona?: string;
  severity?: string;
  autoConnect?: boolean;
  maxEvents?: number;
}

const SUPPORTED_SSE_EVENTS: TelemetryEventType[] = [
  "connected",
  "agent_start",
  "agent_message",
  "agent_dispatch",
  "agent_step",
  "token_delta",
  "tool_call",
  "tool_result",
  "guardrail_check",
  "memory_mutation",
  "agent_complete",
  "agent_error",
  "heartbeat",
];

export function useAgentStream(options: UseAgentStreamOptions = {}) {
  const { persona, severity, autoConnect = true, maxEvents = 100 } = options;

  const [status, setStatus] = useState<StreamStatus>(
    autoConnect ? "connecting" : "disconnected"
  );
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<TelemetryEvent | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const openStreamRef = useRef<() => void>(() => {});

  const openStream = useCallback(() => {
    if (typeof window === "undefined" || typeof EventSource === "undefined") return;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const params = new URLSearchParams();
    if (persona) params.set("persona", persona);
    if (severity) params.set("severity", severity);

    const url = `/api/telemetry/stream${params.toString() ? `?${params.toString()}` : ""}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setStatus("connected");
      reconnectAttemptsRef.current = 0;
    };

    const handleMessage = (type: string, dataStr: string) => {
      try {
        const parsed = JSON.parse(dataStr);
        if (type === "heartbeat") {
          setLastHeartbeat(new Date());
          return;
        }

        const ev = parsed as TelemetryEvent;
        setLatestEvent(ev);
        setEvents((prev) => {
          const next = [ev, ...prev];
          return next.slice(0, maxEvents);
        });
      } catch (err) {
        console.error("Error parsing SSE telemetry frame", err);
      }
    };

    // Register all typed SSE event listeners
    SUPPORTED_SSE_EVENTS.forEach((evtType) => {
      es.addEventListener(evtType, (e) => {
        handleMessage(evtType, (e as MessageEvent).data);
      });
    });

    es.onerror = () => {
      setStatus("error");
      es.close();

      // Exponential backoff with jitter (1s - 10s max)
      const attempts = reconnectAttemptsRef.current;
      const baseDelay = Math.min(1000 * Math.pow(1.5, attempts), 10000);
      const jitter = Math.random() * 500;
      const delay = baseDelay + jitter;
      reconnectAttemptsRef.current += 1;

      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = setTimeout(() => {
        setStatus("connecting");
        openStreamRef.current();
      }, delay);
    };
  }, [persona, severity, maxEvents]);

  useEffect(() => {
    openStreamRef.current = openStream;
  }, [openStream]);

  const connect = useCallback(() => {
    setStatus("connecting");
    reconnectAttemptsRef.current = 0;
    openStream();
  }, [openStream]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setStatus("disconnected");
  }, []);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLatestEvent(null);
  }, []);

  useEffect(() => {
    if (autoConnect) {
      openStream();
    }
    return () => {
      disconnect();
    };
  }, [autoConnect, openStream, disconnect]);

  return {
    status,
    events,
    latestEvent,
    lastHeartbeat,
    connect,
    disconnect,
    clearEvents,
  };
}
