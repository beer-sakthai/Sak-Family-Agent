import {
  OtelData,
  OtelExporter,
  OtelSemConv,
  OtelSignalCard,
} from "./types";

const SIGNALS: OtelSignalCard[] = [
  {
    id: "traces",
    title: "Traces",
    summary:
      "A causal graph of spans representing a single request's path through the system. For an agent loop, one trace typically wraps a whole `run_agent()` invocation with child spans per tool call and per LLM call.",
    keyPrimitives: ["Tracer", "Span", "SpanContext", "SpanKind", "SpanAttributes"],
    docsUrl: "https://opentelemetry.io/docs/concepts/signals/traces/",
  },
  {
    id: "metrics",
    title: "Metrics",
    summary:
      "Aggregated numeric measurements — counters, gauges, histograms. Where sakthai's per-run latency, token counts, and success-rate KPIs would live if the eval.jsonl were promoted to OTel metrics.",
    keyPrimitives: ["Meter", "Counter", "UpDownCounter", "Histogram", "ObservableGauge"],
    docsUrl: "https://opentelemetry.io/docs/concepts/signals/metrics/",
  },
  {
    id: "logs",
    title: "Logs",
    summary:
      "Structured records tied to a trace context. Correlates the plain-text session transcripts in ~/.sakthai/sessions with the trace of the run that produced them.",
    keyPrimitives: ["Logger", "LogRecord", "SeverityNumber", "TraceContext"],
    docsUrl: "https://opentelemetry.io/docs/concepts/signals/logs/",
  },
];

const EXPORTERS: OtelExporter[] = [
  {
    id: "otlp-grpc",
    name: "OTLP / gRPC",
    transport: "gRPC",
    usage: "The default cross-language transport — most vendors and open collectors accept it.",
  },
  {
    id: "otlp-http",
    name: "OTLP / HTTP",
    transport: "HTTP+protobuf",
    usage: "Same schema as gRPC over plain HTTP — friendlier through corporate proxies.",
  },
  {
    id: "console",
    name: "Console",
    transport: "stdout",
    usage: "Dev-time exporter that prints spans to the terminal. Useful for verifying instrumentation before wiring a real backend.",
  },
  {
    id: "jaeger",
    name: "Jaeger",
    transport: "OTLP or Jaeger native",
    usage: "Open-source distributed trace UI — good local option for looking at agent-loop traces.",
  },
  {
    id: "gcp",
    name: "Google Cloud Trace / Monitoring",
    transport: "gRPC",
    usage: "First-party GCP backend; pairs with the Vertex/Gemini providers already in the persona roster.",
  },
];

const LLM_SEMCONV: OtelSemConv[] = [
  {
    attribute: "gen_ai.system",
    purpose: "Vendor of the LLM (anthropic / google / openai / ollama).",
  },
  {
    attribute: "gen_ai.request.model",
    purpose: "Model id requested (matches sakthai's `--model` flag).",
  },
  {
    attribute: "gen_ai.response.model",
    purpose: "Model id the provider actually served (can differ from requested).",
  },
  {
    attribute: "gen_ai.usage.input_tokens",
    purpose: "Prompt token count — mirrors eval.jsonl input_tokens.",
  },
  {
    attribute: "gen_ai.usage.output_tokens",
    purpose: "Completion token count — mirrors eval.jsonl output_tokens.",
  },
  {
    attribute: "gen_ai.response.finish_reasons",
    purpose: "Array of finish reasons — analogous to `stop_reason` in the run.",
  },
  {
    attribute: "gen_ai.operation.name",
    purpose: "chat / text_completion / embeddings — the operation type.",
  },
];

const SAKTHAI_INTEGRATION = `# Recommended minimal wiring for sakthai/agent/loop.py
# (not yet in-tree — this is the target integration shape)

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter())
)
tracer = trace.get_tracer("sakthai.agent.loop")

async def run_agent(task: str, ...):
    with tracer.start_as_current_span("run_agent") as span:
        span.set_attribute("gen_ai.system", provider)
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("sakthai.task_preview", task[:120])

        while iterations < max_iterations:
            with tracer.start_as_current_span("model.call") as call_span:
                response = provider_call(...)
                call_span.set_attribute("gen_ai.usage.input_tokens", response.usage.in_toks)
                call_span.set_attribute("gen_ai.usage.output_tokens", response.usage.out_toks)
                call_span.set_attribute("gen_ai.response.finish_reasons", [response.stop_reason])
            for tool_call in response.tool_calls:
                with tracer.start_as_current_span(f"tool.{tool_call.name}"):
                    dispatch(tool_call)
`;

export function getOtelData(): OtelData {
  return {
    overview: {
      title: "OpenTelemetry — Observability for Agents",
      description:
        "Vendor-neutral open standard for traces, metrics, and logs. The `eval.jsonl` written by sakthai's agent loop today is a hand-rolled subset of what an OTel exporter would emit — this panel shows the mapping and the minimal wiring that would upgrade it in place.",
      repoUrl: "https://github.com/open-telemetry/opentelemetry.io",
      siteUrl: "https://opentelemetry.io",
      license: "Apache 2.0 (code) / CC-BY-4.0 (docs)",
    },
    install:
      "uv add opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp",
    signals: SIGNALS,
    exporters: EXPORTERS,
    llmSemconv: LLM_SEMCONV,
    sakthaiIntegration: SAKTHAI_INTEGRATION,
  };
}
