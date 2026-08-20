import { KnowledgeGraphData, TelegramBridgeData } from "./types";

export const SAMPLE_KNOWLEDGE_GRAPH: KnowledgeGraphData = {
  dbPath: "~/.sakthai/memory.db (WAL Mode)",
  totalFacts: 142,
  nodes: [
    { id: "node_sakthai", label: "SakThai", type: "persona", val: 24, color: "#22d3ee" },
    { id: "node_sakking", label: "SakKing", type: "persona", val: 20, color: "#a855f7" },
    { id: "node_saksee", label: "SakSee", type: "persona", val: 18, color: "#f59e0b" },
    { id: "node_saksit", label: "SakSit", type: "persona", val: 18, color: "#3b82f6" },
    { id: "node_sakjules", label: "SakJules", type: "persona", val: 22, color: "#f43f5e" },
    { id: "node_saktan", label: "SakTan", type: "persona", val: 16, color: "#10b981" },
    // Facts
    { id: "fact_huggingface", label: "19 Sak Models on HF Hub", type: "fact", val: 12 },
    { id: "fact_guardrails", label: "Zero-Vulnerability Sentinel Gate", type: "rule", val: 14 },
    { id: "fact_sqlite", label: "SQLite Fact WAL Engine", type: "fact", val: 10 },
    { id: "fact_turbopack", label: "Turbopack Zero-Warning Next.js Build", type: "fact", val: 12 },
    { id: "fact_telegram", label: "Bidirectional Telegram Bot Bridge", type: "task", val: 10 },
  ],
  edges: [
    { source: "node_sakthai", target: "fact_huggingface", relation: "publishes_and_maintains" },
    { source: "node_sakking", target: "fact_guardrails", relation: "enforces_security_policy" },
    { source: "node_saktan", target: "fact_sqlite", relation: "daily_sharding_and_journal" },
    { source: "node_sakjules", target: "fact_turbopack", relation: "automates_ci_and_builds" },
    { source: "node_saksee", target: "fact_telegram", relation: "scouts_and_routes" },
    { source: "node_saksit", target: "fact_huggingface", relation: "documents_datasets" },
  ],
};

export const SAMPLE_TELEGRAM_BRIDGE: TelegramBridgeData = {
  botUsername: "@SakFamilyAgentBot",
  status: "online",
  activeSessions: 6,
  registeredCommands: ["/start", "/workflows", "/workflow <name>", "/status", "/memory", "/ask"],
  voiceTranscriberEnabled: true,
  allowedUserCount: 3,
};

export function getKnowledgeGraphData(): KnowledgeGraphData {
  return SAMPLE_KNOWLEDGE_GRAPH;
}

export function getTelegramBridgeData(): TelegramBridgeData {
  return SAMPLE_TELEGRAM_BRIDGE;
}
