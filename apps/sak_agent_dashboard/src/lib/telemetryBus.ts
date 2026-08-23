import { EventEmitter } from "events";
import { TelemetryEvent, TelemetryEventType } from "./types";

class TelemetryBus extends EventEmitter {
  private ringBuffer: TelemetryEvent[] = [];
  private readonly maxBufferSize = 250;

  constructor() {
    super();
    this.setMaxListeners(100);
  }

  /**
   * Broadcast a telemetry event to all connected SSE clients and store in ring buffer.
   */
  public emitEvent(event: Omit<TelemetryEvent, "id" | "timestamp"> & { id?: string; timestamp?: string }): TelemetryEvent {
    const fullEvent: TelemetryEvent = {
      id: event.id || `evt_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      timestamp: event.timestamp || new Date().toISOString(),
      type: event.type,
      persona: event.persona,
      sessionId: event.sessionId,
      data: event.data || {},
    };

    this.ringBuffer.push(fullEvent);
    if (this.ringBuffer.length > this.maxBufferSize) {
      this.ringBuffer.shift();
    }

    this.emit("telemetry", fullEvent);
    if (fullEvent.persona) {
      this.emit(`telemetry:${fullEvent.persona.toLowerCase()}`, fullEvent);
    }
    return fullEvent;
  }

  /**
   * Get recent history from the ring buffer, optionally filtered by persona.
   */
  public getRecentEvents(persona?: string, limit = 50): TelemetryEvent[] {
    const list = persona
      ? this.ringBuffer.filter((e) => e.persona.toLowerCase() === persona.toLowerCase())
      : this.ringBuffer;
    return list.slice(-limit);
  }

  /**
   * Generate initial sample stream event for connection ACK.
   */
  public createConnectedEvent(): TelemetryEvent {
    return {
      id: `conn_${Date.now()}`,
      type: "connected",
      timestamp: new Date().toISOString(),
      persona: "SakFamily",
      data: {
        message: "Connected to Sak-Agent-Family Live Telemetry Engine",
      },
    };
  }
}

// Global singleton instance across Next.js module reloads
const globalForTelemetry = global as unknown as { telemetryBus?: TelemetryBus };
export const telemetryBus = globalForTelemetry.telemetryBus || new TelemetryBus();
if (process.env.NODE_ENV !== "production") {
  globalForTelemetry.telemetryBus = telemetryBus;
}

export default telemetryBus;
