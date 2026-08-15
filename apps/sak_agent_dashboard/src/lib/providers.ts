import { ProviderSpec, ProviderType } from "./types";

export const PROVIDERS: ProviderSpec[] = [
  {
    id: "claude",
    name: "Anthropic Claude",
    description: "State-of-the-art reasoning, architecture design, and complex safety-aligned reasoning.",
    vendor: "Anthropic",
    badge: "Reasoning",
    health: "healthy",
    latencyMs: 340,
    isLocal: false,
    defaultModel: "claude-3-5-sonnet-20241022",
    assignedPersonas: ["SakThai", "SakSit"],
    supportedModels: [
      {
        id: "claude-3-5-sonnet-20241022",
        name: "Claude 3.5 Sonnet",
        contextWindow: 200000,
        inputCostPer1M: 3.0,
        outputCostPer1M: 15.0,
        isLocal: false,
        capabilities: ["text", "vision", "code", "tool_calling", "reasoning"],
      },
      {
        id: "claude-3-opus-20240229",
        name: "Claude 3 Opus",
        contextWindow: 200000,
        inputCostPer1M: 15.0,
        outputCostPer1M: 75.0,
        isLocal: false,
        capabilities: ["text", "vision", "code", "reasoning"],
      },
    ],
  },
  {
    id: "codex",
    name: "OpenAI / Codex",
    description: "Advanced code synthesis, JSON transformation, and fast reasoning engines.",
    vendor: "OpenAI",
    badge: "Code & Logic",
    health: "healthy",
    latencyMs: 290,
    isLocal: false,
    defaultModel: "gpt-4o",
    assignedPersonas: ["SakKing", "SakJules"],
    supportedModels: [
      {
        id: "gpt-4o",
        name: "GPT-4o Omnimodel",
        contextWindow: 128000,
        inputCostPer1M: 2.5,
        outputCostPer1M: 10.0,
        isLocal: false,
        capabilities: ["text", "vision", "code", "tool_calling"],
      },
      {
        id: "o3-mini",
        name: "o3-mini Fast Reasoning",
        contextWindow: 128000,
        inputCostPer1M: 1.1,
        outputCostPer1M: 4.4,
        isLocal: false,
        capabilities: ["text", "code", "reasoning"],
      },
    ],
  },
  {
    id: "opencode",
    name: "OpenCode Models",
    description: "Open-weights coding LLMs with high efficiency (DeepSeek-Coder, Qwen-2.5-Coder).",
    vendor: "Open-Source Foundation",
    badge: "Open Weights",
    health: "healthy",
    latencyMs: 210,
    isLocal: false,
    defaultModel: "Qwen/Qwen2.5-Coder-32B-Instruct",
    assignedPersonas: ["SakKing", "SakSit"],
    supportedModels: [
      {
        id: "Qwen/Qwen2.5-Coder-32B-Instruct",
        name: "Qwen 2.5 Coder 32B",
        contextWindow: 65536,
        inputCostPer1M: 0.8,
        outputCostPer1M: 1.6,
        isLocal: false,
        capabilities: ["text", "code", "tool_calling"],
      },
      {
        id: "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
        name: "DeepSeek Coder V2 Lite",
        contextWindow: 65536,
        inputCostPer1M: 0.2,
        outputCostPer1M: 0.5,
        isLocal: false,
        capabilities: ["text", "code", "tool_calling"],
      },
    ],
  },
  {
    id: "ollama",
    name: "Ollama (Local Offline)",
    description: "Zero-cost, private local inference via GGUF/llama.cpp runtime with zero internet dependency.",
    vendor: "Local Machine",
    badge: "Local $0.00",
    health: "healthy",
    latencyMs: 145,
    isLocal: true,
    defaultModel: "sakthai",
    assignedPersonas: ["SakTan"],
    supportedModels: [
      {
        id: "sakthai",
        name: "SakThai Fine-Tuned Local",
        contextWindow: 32768,
        inputCostPer1M: 0.0,
        outputCostPer1M: 0.0,
        isLocal: true,
        capabilities: ["text", "code", "tool_calling"],
      },
      {
        id: "llama3.3:70b",
        name: "Llama 3.3 70B Local",
        contextWindow: 65536,
        inputCostPer1M: 0.0,
        outputCostPer1M: 0.0,
        isLocal: true,
        capabilities: ["text", "code", "reasoning"],
      },
    ],
  },
  {
    id: "huggingface",
    name: "Hugging Face Hub & Endpoints",
    description: "Community datasets, model evaluation endpoints, and Spaces integration for Sak assets.",
    vendor: "Hugging Face",
    badge: "Hub & Spaces",
    health: "healthy",
    latencyMs: 380,
    isLocal: false,
    defaultModel: "sakthai/sak-family-agent",
    assignedPersonas: ["SakThai", "SakSee"],
    supportedModels: [
      {
        id: "sakthai/sak-family-agent",
        name: "Sak-Family-Agent v1 Endpoint",
        contextWindow: 32768,
        inputCostPer1M: 0.5,
        outputCostPer1M: 1.0,
        isLocal: false,
        capabilities: ["text", "code", "tool_calling"],
      },
      {
        id: "stabilityai/stable-diffusion-xl-base-1.0",
        name: "SDXL Image Generation",
        contextWindow: 4096,
        inputCostPer1M: 0.0,
        outputCostPer1M: 0.0,
        isLocal: false,
        capabilities: ["vision"],
      },
    ],
  },
  {
    id: "gemini_agy",
    name: "Gemini / Antigravity (AGY)",
    description: "Google Gemini multi-modal reasoning and Antigravity Agent Development Kit (ADK) pipelines.",
    vendor: "Google DeepMind",
    badge: "Agent Platform",
    health: "healthy",
    latencyMs: 190,
    isLocal: false,
    defaultModel: "gemini-2.5-flash",
    assignedPersonas: ["SakThai", "SakJules", "SakSee"],
    supportedModels: [
      {
        id: "gemini-2.5-flash",
        name: "Gemini 2.5 Flash",
        contextWindow: 1000000,
        inputCostPer1M: 0.075,
        outputCostPer1M: 0.30,
        isLocal: false,
        capabilities: ["text", "vision", "code", "tool_calling", "reasoning"],
      },
      {
        id: "gemini-2.5-pro",
        name: "Gemini 2.5 Pro",
        contextWindow: 2000000,
        inputCostPer1M: 1.25,
        outputCostPer1M: 5.0,
        isLocal: false,
        capabilities: ["text", "vision", "code", "tool_calling", "reasoning"],
      },
    ],
  },
  {
    id: "m365_azure",
    name: "Microsoft 365 Copilot & Azure AI",
    description: "Enterprise M365 Copilot Retrieval APIs, SharePoint/OneDrive grounding, and Azure OpenAI infrastructure.",
    vendor: "Microsoft",
    badge: "Enterprise & M365",
    health: "healthy",
    latencyMs: 270,
    isLocal: false,
    defaultModel: "microsoft-agents-m365copilot",
    assignedPersonas: ["SakThai", "SakKing", "SakJules"],
    supportedModels: [
      {
        id: "microsoft-agents-m365copilot",
        name: "M365 Copilot Retrieval API",
        contextWindow: 128000,
        inputCostPer1M: 2.0,
        outputCostPer1M: 8.0,
        isLocal: false,
        capabilities: ["text", "code", "tool_calling", "reasoning"],
      },
      {
        id: "azure/gpt-4o",
        name: "Azure OpenAI GPT-4o Enterprise",
        contextWindow: 128000,
        inputCostPer1M: 2.5,
        outputCostPer1M: 10.0,
        isLocal: false,
        capabilities: ["text", "vision", "code", "tool_calling"],
      },
    ],
  },
];

export function getProvider(id: ProviderType): ProviderSpec | undefined {
  return PROVIDERS.find((p) => p.id === id);
}

export function resolveProviderForPersona(personaSlug: string): {
  primary: ProviderSpec;
  fallback: ProviderSpec;
} {
  const slug = personaSlug.toLowerCase();
  const matched = PROVIDERS.filter((p) =>
    p.assignedPersonas.some((name) => name.toLowerCase() === slug)
  );

  const primary = matched[0] || PROVIDERS[0];
  const fallback = PROVIDERS.find((p) => p.id === "ollama") || PROVIDERS[1];

  return { primary, fallback };
}
