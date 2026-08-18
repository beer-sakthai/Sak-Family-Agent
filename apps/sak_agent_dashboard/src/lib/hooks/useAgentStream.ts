"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { TelemetryEvent } from "@/lib/types";

export type StreamStatus = "connecting" | "connected" | "disconnected" | "error";

interface UseAgentStreamOptions {
  persona?: string;
  severity?: string;
  autoConnect?: boolean;
  maxEvents?: number;
}

export function useAgentStream(options: UseAgentStreamOptions = {}) {
  const { persona, severity, autoConnect = true, maxEvents = 100 } = options;

  const [status, setStatus] = useState<StreamStatus>(
    autoConnect ? "connecting" : "disconnected",
  );
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<TelemetryEvent | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  // Holds the latest `openStream` so the reconnect timer can re-enter it without
  // `openStream` closing over itself (and going stale when persona/severity change).
  const openStreamRef = useRef<() => void>(() => {});

  // Opens the stream without touching state synchronously, so the mount effect
  // below can call it directly. Status transitions are driven by the EventSource
  // callbacks (`onopen` / `onerror`) instead.
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

    // Standard SSE event listeners
    const eventTypes = [
      "connected",
      "agent_start",
      "token_delta",
      "tool_call",
      "tool_result",
      "guardrail_check",
      "memory_mutation",
      "agent_complete",
      "agent_error",
      "heartbeat",
    ];

    eventTypes.forEach((evtType) => {
      es.addEventListener(evtType, (e) => {
        handleMessage(evtType, (e as MessageEvent).data);
      });
    });

    es.onerror = () => {
      setStatus("error");
      es.close();
      // Auto reconnect after 5s
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = setTimeout(() => {
        setStatus("connecting");
        openStreamRef.current();
      }, 5000);
    };
  }, [persona, severity, maxEvents]);

  useEffect(() => {
    openStreamRef.current = openStream;
  }, [openStream]);

  const connect = useCallback(() => {
    setStatus("connecting");
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
