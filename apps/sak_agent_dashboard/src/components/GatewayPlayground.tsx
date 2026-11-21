"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Radio,
  RefreshCw,
  Send,
  Shield,
  ShieldAlert,
} from "lucide-react";
import PersonaAvatar from "./PersonaAvatar";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  persona?: string;
  model?: string;
  streaming?: boolean;
  timestamp: string;
}

interface GatewayHealth {
  ok: boolean;
  status: string;
  gateway_url: string;
  version?: string;
  uptime?: string;
  active_personas?: string[];
  models_count?: number;
  tools_count?: number;
  message?: string;
}

const PERSONA_CONFIGS = [
  {
    id: "sakthai",
    name: "SakThai",
    role: "Main Lead · HF Master",
    handle: "@sakthai_agent_bot",
    defaultModel: "deepseek-ai/DeepSeek-V4.1-Flash",
    badgeColor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
  },
  {
    id: "sakking",
    name: "SakKing",
    role: "Runner · Deputy 1 · Coder",
    handle: "@sakking_agent_bot",
    defaultModel: "Qwen/Qwen3-Coder-30B-A3B-Instruct",
    badgeColor: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  },
  {
    id: "saksee",
    name: "SakSee",
    role: "Web / Browser · Deputy 3",
    handle: "@saksee_agent_bot",
    defaultModel: "deepseek-ai/DeepSeek-V4.1-Flash",
    badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  },
  {
    id: "sakjules",
    name: "SakJules",
    role: "Automation & CI/CD Master",
    handle: "@sakjules_agent_bot",
    defaultModel: "deepseek-ai/DeepSeek-V4.1-Flash",
    badgeColor: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  },
  {
    id: "saksit",
    name: "SakSit",
    role: "Social / Content Specialist",
    handle: "@saksit_agent_bot",
    defaultModel: "deepseek-ai/DeepSeek-V4-Flash",
    badgeColor: "bg-pink-500/10 text-pink-400 border-pink-500/30",
  },
  {
    id: "saktan",
    name: "SakTan",
    role: "Daily Ops · Deputy 2",
    handle: "@saktan_agent_bot",
    defaultModel: "sakthai on local Ollama",
    badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  },
];

const MODEL_TIERS = [
  { id: "persona-default", label: "Persona Default", model: "" },
  { id: "fast", label: "Fast (Gemini 2.5)", model: "gemini-2.5-flash" },
  { id: "reasoning", label: "Reasoning (Gemini 3.7)", model: "gemini-3.7-flash" },
  { id: "local", label: "Local (Gemma 2 9B)", model: "gemma-2-9b-it" },
];

async function readStreamDeltas(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onUpdate: (accumulated: string) => void
): Promise<string> {
  const decoder = new TextDecoder();
  let text = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split("\n");

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data:")) continue;
      const dataStr = trimmed.replace(/^data:\s*/, "");
      if (dataStr === "[DONE]") {
        break;
      }
      try {
        const parsed = JSON.parse(dataStr);
        const delta = parsed.choices?.[0]?.delta?.content || "";
        text += delta;
        onUpdate(text);
      } catch {
        // Ignore non-json chunks
      }
    }
  }
  return text;
}

export function GatewayPlayground() {
  const [health, setHealth] = useState<GatewayHealth | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState<string>("sakjules");
  const [selectedTier, setSelectedTier] = useState<string>("persona-default");
  const [inputPrompt, setInputPrompt] = useState("");
  const [streamMode, setStreamMode] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [guardrailAlert, setGuardrailAlert] = useState<Record<string, unknown> | null>(null);
  const [guardrailTesting, setGuardrailTesting] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "initial",
      role: "assistant",
      persona: "sakjules",
      model: "sakjules",
      content:
        "**SakJules · Master of Automation & CI/CD.**\n\nRuntime Gateway online! Select any persona and stream chat completions or test concentric guardrails below.",
      timestamp: "Just now",
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageCounterRef = useRef(0);

  const fetchHealth = useCallback(async () => {
    setCheckingHealth(true);
    try {
      const res = await fetch("/api/gateway/health");
      const data = await res.json();
      setHealth(data);
    } catch {
      setHealth({
        ok: false,
        status: "offline",
        gateway_url: "http://127.0.0.1:8080",
        message: "Network error reaching gateway probe.",
      });
    } finally {
      setCheckingHealth(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const res = await fetch("/api/gateway/health");
        const data = await res.json();
        if (active) setHealth(data);
      } catch {
        if (active) {
          setHealth({
            ok: false,
            status: "offline",
            gateway_url: "http://127.0.0.1:8080",
            message: "Network error reaching gateway probe.",
          });
        }
      }
    };

    void poll();
    const interval = setInterval(poll, 15000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages]);

  const effectiveModel =
    selectedTier === "persona-default"
      ? selectedPersona
      : MODEL_TIERS.find((t) => t.id === selectedTier)?.model || selectedPersona;

  const handleSendMessage = useCallback(
    async (promptToSend?: string) => {
      const prompt = (promptToSend || inputPrompt).trim();
      if (!prompt || isSending) return;

      messageCounterRef.current += 1;
      const userMessageId = `user-${messageCounterRef.current}`;
      const assistantId = `assistant-${messageCounterRef.current}`;

      const userMessage: Message = {
        id: userMessageId,
        role: "user",
        content: prompt,
        timestamp: "Now",
      };

      const initialAssistant: Message = {
        id: assistantId,
        role: "assistant",
        persona: selectedPersona,
        model: effectiveModel,
        content: "",
        streaming: streamMode,
        timestamp: "Now",
      };

      setMessages((prev) => [...prev, userMessage, initialAssistant]);
      if (!promptToSend) setInputPrompt("");
      setIsSending(true);

      try {
        const payload = {
          model: effectiveModel,
          stream: streamMode,
          messages: [
            { role: "system", content: `You are ${selectedPersona}. Respond accurately.` },
            { role: "user", content: prompt },
          ],
        };

        const res = await fetch("/api/gateway/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const errJson = await res.json().catch(() => ({}));
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: `❌ Error: ${errJson.error || "Gateway connection error"} (${errJson.detail || res.statusText})`,
                    streaming: false,
                  }
                : m
            )
          );
          return;
        }

        if (streamMode && res.body) {
          const reader = res.body.getReader();
          const finalContent = await readStreamDeltas(reader, (currentText) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: currentText, streaming: true }
                  : m
              )
            );
          });

          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: finalContent || "[Completed]", streaming: false }
                : m
            )
          );
        } else {
          const json = await res.json();
          const content =
            json.choices?.[0]?.message?.content || JSON.stringify(json, null, 2);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content, streaming: false } : m
            )
          );
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: `❌ Network error: ${msg}`, streaming: false }
              : m
          )
        );
      } finally {
        setIsSending(false);
      }
    },
    [effectiveModel, inputPrompt, isSending, selectedPersona, streamMode]
  );

  const handleTestGuardrail = async (cmd: string) => {
    setGuardrailTesting(true);
    setGuardrailAlert(null);
    try {
      const res = await fetch("/api/gateway/tools", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool: "run_command",
          arguments: { command: cmd },
        }),
      });
      const data = await res.json();
      setGuardrailAlert({ command: cmd, ...data });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setGuardrailAlert({ command: cmd, status: "error", error: msg });
    } finally {
      setGuardrailTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Gateway Pulse */}
      <div className="flex flex-col gap-4 rounded-2xl border border-line-subtle bg-surface-raised p-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
            <Radio className="h-6 w-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-content-primary">Runtime Gateway</h2>
              {health?.ok ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
                  Live :8080
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400">
                  <AlertTriangle className="h-3 w-3" />
                  Offline
                </span>
              )}
            </div>
            <p className="text-xs text-content-secondary">
              OpenAI-compatible & REST API server serving all 6 family personas with DataLossGuardrail security.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {health?.ok && (
            <div className="flex items-center gap-4 text-xs text-content-secondary">
              <div>
                <span className="text-content-muted">Uptime: </span>
                <span className="font-mono text-content-primary">{health.uptime || "active"}</span>
              </div>
              <div>
                <span className="text-content-muted">Models: </span>
                <span className="font-mono text-content-primary">{health.models_count || 10}</span>
              </div>
              <div>
                <span className="text-content-muted">Tools: </span>
                <span className="font-mono text-content-primary">{health.tools_count || 19}</span>
              </div>
            </div>
          )}
          <button
            type="button"
            onClick={fetchHealth}
            disabled={checkingHealth}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line-subtle bg-surface-base px-3 py-1.5 text-xs font-medium text-content-primary hover:bg-surface-raised"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${checkingHealth ? "animate-spin" : ""}`} />
            Probe
          </button>
        </div>
      </div>

      {!health?.ok && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-300">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <div className="space-y-1">
            <p className="font-medium">Gateway server is offline or unreachable on {health?.gateway_url || "http://127.0.0.1:8080"}.</p>
            <p className="text-amber-300/80">
              Start the gateway locally with: <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono text-amber-200">uv run sakthai gateway serve --port 8080</code>
            </p>
          </div>
        </div>
      )}

      {/* Main Grid: Persona Selection & Chat */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Persona Matrix & Tiers */}
        <div className="space-y-4 lg:col-span-4">
          <div className="rounded-2xl border border-line-subtle bg-surface-raised p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-content-muted">
              Select Family Persona
            </h3>
            <div className="space-y-2">
              {PERSONA_CONFIGS.map((persona) => {
                const isSelected = selectedPersona === persona.id;
                return (
                  <button
                    key={persona.id}
                    type="button"
                    onClick={() => setSelectedPersona(persona.id)}
                    className={`flex w-full items-center gap-3 rounded-xl border p-2.5 text-left transition-all ${
                      isSelected
                        ? "border-purple-500/40 bg-purple-500/10 shadow-sm"
                        : "border-transparent bg-surface-base/50 hover:border-line-subtle hover:bg-surface-base"
                    }`}
                  >
                    <PersonaAvatar name={persona.id} size={36} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-content-primary">{persona.name}</span>
                        <span className={`rounded-full border px-1.5 py-0.2 text-[10px] font-mono ${persona.badgeColor}`}>
                          {persona.id}
                        </span>
                      </div>
                      <p className="truncate text-[11px] text-content-secondary">{persona.role}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Model Tier Selector */}
          <div className="rounded-2xl border border-line-subtle bg-surface-raised p-4">
            <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-content-muted">
              Model Tier Override
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {MODEL_TIERS.map((tier) => (
                <button
                  key={tier.id}
                  type="button"
                  onClick={() => setSelectedTier(tier.id)}
                  className={`rounded-lg border px-2.5 py-2 text-left text-xs font-medium transition-colors ${
                    selectedTier === tier.id
                      ? "border-purple-500/50 bg-purple-500/15 text-purple-300"
                      : "border-line-subtle bg-surface-base text-content-secondary hover:text-content-primary"
                  }`}
                >
                  {tier.label}
                </button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-content-muted">
              Target model ID: <span className="font-mono text-content-secondary">{effectiveModel}</span>
            </p>
          </div>

          {/* Concentric Guardrails Test Deck */}
          <div className="rounded-2xl border border-line-subtle bg-surface-raised p-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-content-muted">
                <Shield className="h-3.5 w-3.5 text-purple-400" />
                DataLossGuardrail Probe
              </h3>
            </div>
            <p className="mb-3 text-[11px] text-content-secondary">
              Test how the gateway intercepts destructive commands sent to <code className="font-mono">/v1/tools/execute</code>.
            </p>
            <div className="space-y-2">
              <button
                type="button"
                disabled={guardrailTesting}
                onClick={() => handleTestGuardrail("rm -rf /")}
                className="flex w-full items-center justify-between rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs font-medium text-rose-300 hover:bg-rose-500/20"
              >
                <span>Destructive: rm -rf /</span>
                <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
              </button>
              <button
                type="button"
                disabled={guardrailTesting}
                onClick={() => handleTestGuardrail("echo 'House of Sak safe test'")}
                className="flex w-full items-center justify-between rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-medium text-emerald-300 hover:bg-emerald-500/20"
              >
                <span>Safe: echo &#39;test&#39;</span>
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              </button>
            </div>

            {guardrailAlert && (
              <div
                className={`mt-3 rounded-xl border p-3 text-xs ${
                  guardrailAlert.status === "blocked"
                    ? "border-amber-500/40 bg-amber-500/10 text-amber-200"
                    : guardrailAlert.status === "success"
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-200"
                    : "border-line-subtle bg-surface-base text-content-primary"
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[11px]">
                  <span>Status: {String(guardrailAlert.status)}</span>
                  {guardrailAlert.status === "blocked" && (
                    <span className="rounded bg-amber-500/20 px-1 text-amber-300">BLOCKED</span>
                  )}
                </div>
                {Boolean(guardrailAlert.reason) && (
                  <p className="mt-1 text-[11px] text-content-secondary">
                    Reason: {String(guardrailAlert.reason)}
                  </p>
                )}
                {Boolean(guardrailAlert.approval_token_required) && (
                  <p className="mt-1 truncate font-mono text-[10px] text-amber-300">
                    Token req: {String(guardrailAlert.approval_token_required)}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Interactive Chat & SSE Stream Window */}
        <div className="flex flex-col rounded-2xl border border-line-subtle bg-surface-raised lg:col-span-8">
          {/* Chat Header */}
          <div className="flex items-center justify-between border-b border-line-subtle px-5 py-3.5">
            <div className="flex items-center gap-3">
              <PersonaAvatar name={selectedPersona} size={32} />
              <div>
                <h4 className="text-xs font-semibold text-content-primary">
                  Chatting with {PERSONA_CONFIGS.find((p) => p.id === selectedPersona)?.name}
                </h4>
                <p className="text-[11px] text-content-muted">
                  Model: <span className="font-mono text-purple-400">{effectiveModel}</span> · Streaming:{" "}
                  {streamMode ? "SSE Enabled" : "JSON"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <label className="flex cursor-pointer items-center gap-1.5 text-xs text-content-secondary">
                <input
                  type="checkbox"
                  checked={streamMode}
                  onChange={(e) => setStreamMode(e.target.checked)}
                  className="rounded border-line-strong bg-surface-base text-purple-500 focus:ring-0"
                />
                SSE Stream
              </label>
            </div>
          </div>

          {/* Messages Feed */}
          <div className="flex-1 space-y-4 overflow-y-auto p-5" style={{ minHeight: "360px", maxHeight: "500px" }}>
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.role !== "user" && <PersonaAvatar name={m.persona || selectedPersona} size={28} />}
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                    m.role === "user"
                      ? "bg-purple-600 text-white"
                      : "border border-line-subtle bg-surface-base text-content-primary"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{m.content}</div>
                  {m.streaming && (
                    <span className="inline-block h-3 w-1.5 animate-pulse bg-purple-400 ml-1" />
                  )}
                  <div className={`mt-1 text-[10px] ${m.role === "user" ? "text-purple-200" : "text-content-muted"}`}>
                    {m.timestamp}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompt Chips */}
          <div className="flex flex-wrap items-center gap-2 border-t border-line-subtle/50 px-5 pt-3">
            <span className="text-[11px] text-content-muted">Quick:</span>
            {[
              "What is your identity and specialty?",
              "Check status of family runtime",
              "Explain concentric guardrails",
            ].map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => handleSendMessage(chip)}
                disabled={isSending}
                className="rounded-full border border-line-subtle bg-surface-base px-2.5 py-1 text-[11px] text-content-secondary hover:border-purple-500/30 hover:text-content-primary"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Chat Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2 p-5"
          >
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder={`Message ${PERSONA_CONFIGS.find((p) => p.id === selectedPersona)?.name}...`}
              disabled={isSending}
              className="flex-1 rounded-xl border border-line-subtle bg-surface-base px-3.5 py-2.5 text-xs text-content-primary placeholder:text-content-muted focus:border-purple-500/50 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isSending || !inputPrompt.trim()}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-purple-600 text-white transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default GatewayPlayground;
