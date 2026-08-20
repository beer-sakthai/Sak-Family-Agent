"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Cpu,
  Swords,
  BrainCircuit,
  Send,
  Radio,
  Workflow,
  Globe,
  Wrench,
  Trophy,
  Network,
  RefreshCw,
  BarChart3,
  MessageSquare,
  Shield,
  Plug,
  Boxes,
  Layers,
  MessagesSquare,
  Bot,
  Sparkles,
  Music2,
  Telescope,
  Users,
  GraduationCap,
  Fingerprint,
  ScrollText,
  ShieldCheck,
  DollarSign,
  AlertTriangle,
} from "lucide-react";
import type { SessionTranscript } from "@/lib/types";
import type { DashboardData } from "@/lib/hooks/useDashboardData";

import AgentOverview from "@/components/AgentOverview";
import AnalyticsCharts from "@/components/AnalyticsCharts";
import SessionExplorer from "@/components/SessionExplorer";
import MemoryExplorer from "@/components/MemoryExplorer";
import AuditLogs from "@/components/AuditLogs";
import StitchStudio from "@/components/StitchStudio";
import McpServers from "@/components/McpServers";
import SpecKitPanel from "@/components/SpecKitPanel";
import McpSdkPanel from "@/components/McpSdkPanel";
import ChatKitPanel from "@/components/ChatKitPanel";
import AntigravityPanel from "@/components/AntigravityPanel";
import GenkitPanel from "@/components/GenkitPanel";
import ConductorPanel from "@/components/ConductorPanel";
import OtelPanel from "@/components/OtelPanel";
import GoogleAdkPanel from "@/components/GoogleAdkPanel";
import GcpLearningPanel from "@/components/GcpLearningPanel";
import M365CopilotPanel from "@/components/M365CopilotPanel";
import AgentGatewayPanel from "@/components/AgentGatewayPanel";
import GatewayRouterPanel from "@/components/GatewayRouterPanel";
import AutoCyclePanel from "@/components/AutoCyclePanel";
import DesignSpecsPanel from "@/components/DesignSpecsPanel";
import { ChatStudioPanel } from "@/components/ChatStudioPanel";
import { FinetuningPanel } from "@/components/FinetuningPanel";
import { GoogleAdkBridgePanel } from "@/components/GoogleAdkBridgePanel";
import { TelegramVoiceBridgePanel } from "@/components/TelegramVoiceBridgePanel";
import { LiveTelemetryFeed } from "@/components/LiveTelemetryFeed";
import { WorkflowFrameworkPanel } from "@/components/WorkflowFrameworkPanel";
import { ProviderMatrixPanel } from "@/components/ProviderMatrixPanel";
import { HubEcosystemPanel } from "@/components/HubEcosystemPanel";
import { SkillsToolsPanel } from "@/components/SkillsToolsPanel";
import { BenchmarkArena } from "@/components/BenchmarkArena";
import { MemoryRagTelegramPanel } from "@/components/MemoryRagTelegramPanel";
import { SelfEvolutionPanel } from "@/components/SelfEvolutionPanel";
import { BillingManagementPanel } from "@/components/BillingManagementPanel";
import { SelfHealingConsole } from "@/components/SelfHealingConsole";
import DataSourceBadge from "@/components/DataSourceBadge";

/**
 * Tab Registry (Registry pattern).
 *
 * `page.tsx` used to hardcode ~30 tab buttons and ~30 conditional panel renders,
 * each one a near-identical copy of the last. Every tab is now a single entry
 * here: its id, label, icon, active-state styling, optional badge, and the JSX
 * it renders. The page maps over `TABS`; adding a tab is one array entry, not a
 * button + a conditional block.
 */

export type TabId =
  | "overview"
  | "arena"
  | "finetune"
  | "adk_bridge"
  | "telegram_hub"
  | "workflows"
  | "providers"
  | "hub"
  | "skills"
  | "benchmarks"
  | "rag_telegram"
  | "evolution"
  | "analytics"
  | "sessions"
  | "memory"
  | "mcp"
  | "mcpsdk"
  | "speckit"
  | "chatkit"
  | "antigravity"
  | "genkit"
  | "conductor"
  | "otel"
  | "adk"
  | "learning"
  | "m365"
  | "autocycle"
  | "specs"
  | "gateway"
  | "stitch"
  | "billing"
  | "incidents";

/** Handlers a tab's render function may need, threaded from the page. */
export interface TabContext {
  onSessionSelect: (sessionId: string) => void;
  selectedSessionDetail: SessionTranscript | null;
}

export interface TabDefinition {
  id: TabId;
  /** Label text; a function so counts (e.g. `Agent Overview (6)`) stay live. */
  label: (data: DashboardData) => string;
  icon: LucideIcon;
  /** Per-tab icon color class (e.g. `text-cyan-400`). */
  iconClass: string;
  /** Active-state gradient classes; the inactive state is shared. */
  activeClass: string;
  /** Optional trailing badge `<span>`, or `null` for no badge. */
  badge?: (data: DashboardData) => ReactNode;
  render: (data: DashboardData, ctx: TabContext) => ReactNode;
}

/** Shared inactive-state classes for every tab button. */
export const INACTIVE_CLASS =
  "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50";

/** The neutral badge used by the data-driven tabs (counts, package tallies). */
function neutralBadge(children: ReactNode): ReactNode {
  return (
    <span className="text-[10px] font-mono ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/70">
      {children}
    </span>
  );
}

export const TABS: TabDefinition[] = [
  {
    id: "overview",
    label: (d) => `Agent Overview (${d.agents.length})`,
    icon: Cpu,
    iconClass: "text-cyan-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: (d) => (
      <div className="space-y-8">
        <div className="flex flex-wrap items-center gap-2">
          <DataSourceBadge source={d.dataSources.agents} label="eval.jsonl" />
          {d.unattributedRuns > 0 && (
            <span
              className="inline-flex items-center rounded-full border border-slate-700/60 bg-slate-900/70 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide text-slate-400"
              title="Runs whose eval entry carried no persona field. They are counted separately rather than assigned to a persona."
            >
              {d.unattributedRuns} unattributed
            </span>
          )}
        </div>
        <AgentOverview agents={d.agents} />
        <LiveTelemetryFeed />
        <AnalyticsCharts metrics={d.metrics} agents={d.agents} />
      </div>
    ),
  },
  {
    id: "arena",
    label: () => "Chat Arena",
    icon: Swords,
    iconClass: "text-blue-400",
    activeClass:
      "bg-gradient-to-r from-blue-600/30 via-indigo-600/30 to-purple-600/30 text-blue-300 border border-blue-500/50 shadow-lg shadow-blue-950/50 ring-1 ring-blue-500/30",
    badge: () => (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/50">
        Supervisor
      </span>
    ),
    render: () => <ChatStudioPanel />,
  },
  {
    id: "finetune",
    label: () => "LoRA Studio",
    icon: BrainCircuit,
    iconClass: "text-purple-400",
    activeClass:
      "bg-gradient-to-r from-purple-600/30 via-indigo-600/30 to-violet-600/30 text-purple-300 border border-purple-500/50 shadow-lg shadow-purple-950/50 ring-1 ring-purple-500/30",
    badge: () => (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800/50">
        PEFT
      </span>
    ),
    render: () => <FinetuningPanel />,
  },
  {
    id: "adk_bridge",
    label: () => "ADK Bridge",
    icon: Send,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-emerald-600/30 via-teal-600/30 to-blue-600/30 text-emerald-300 border border-emerald-500/50 shadow-lg shadow-emerald-950/50 ring-1 ring-emerald-500/30",
    badge: () => (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/50">
        Cloud Run
      </span>
    ),
    render: () => <GoogleAdkBridgePanel />,
  },
  {
    id: "telegram_hub",
    label: () => "Telegram Hub",
    icon: Radio,
    iconClass: "text-teal-400",
    activeClass:
      "bg-gradient-to-r from-teal-600/30 via-cyan-600/30 to-blue-600/30 text-teal-300 border border-teal-500/50 shadow-lg shadow-teal-950/50 ring-1 ring-teal-500/30",
    badge: () => (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800/50">
        Voice &amp; Alert
      </span>
    ),
    render: () => <TelegramVoiceBridgePanel />,
  },
  {
    id: "workflows",
    label: () => "Workflows",
    icon: Workflow,
    iconClass: "text-cyan-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: () => (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/50">
        6 Agents
      </span>
    ),
    render: () => <WorkflowFrameworkPanel />,
  },
  {
    id: "providers",
    label: () => "Providers",
    icon: Cpu,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: () => (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/50">
        7 Matrix
      </span>
    ),
    render: () => <ProviderMatrixPanel />,
  },
  {
    id: "hub",
    label: () => "Hub",
    icon: Globe,
    iconClass: "text-amber-400",
    activeClass:
      "bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-300 border border-amber-500/40 shadow-lg shadow-amber-950/50",
    badge: () => (
      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/50">
        19m·16d
      </span>
    ),
    render: () => <HubEcosystemPanel />,
  },
  {
    id: "skills",
    label: () => "Skills & AST Gates",
    icon: Wrench,
    iconClass: "text-blue-400",
    activeClass:
      "bg-gradient-to-r from-blue-500/20 to-indigo-500/20 text-blue-300 border border-blue-500/40 shadow-lg shadow-blue-950/50",
    render: () => <SkillsToolsPanel />,
  },
  {
    id: "benchmarks",
    label: () => "Benchmark Arena",
    icon: Trophy,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-950/50",
    render: () => <BenchmarkArena />,
  },
  {
    id: "rag_telegram",
    label: () => "RAG & Telegram",
    icon: Network,
    iconClass: "text-purple-400",
    activeClass:
      "bg-gradient-to-r from-purple-500/20 to-fuchsia-500/20 text-purple-300 border border-purple-500/40 shadow-lg shadow-purple-950/50",
    render: () => <MemoryRagTelegramPanel />,
  },
  {
    id: "evolution",
    label: () => "Self-Evolution",
    icon: RefreshCw,
    iconClass: "text-rose-400",
    activeClass:
      "bg-gradient-to-r from-rose-500/20 to-pink-500/20 text-rose-300 border border-rose-500/40 shadow-lg shadow-rose-950/50",
    render: () => <SelfEvolutionPanel />,
  },
  {
    id: "analytics",
    label: () => "Analytics & Charts",
    icon: BarChart3,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: (d) => (
      <div className="space-y-4">
        <DataSourceBadge source={d.dataSources.metrics} label="eval.jsonl" />
        <AnalyticsCharts metrics={d.metrics} agents={d.agents} />
      </div>
    ),
  },
  {
    id: "sessions",
    label: (d) => `Session Explorer (${d.sessions.length})`,
    icon: MessageSquare,
    iconClass: "text-purple-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: (d, ctx) => (
      <div className="space-y-4">
        <DataSourceBadge source={d.dataSources.sessions} label="sessions/" />
        <SessionExplorer
          sessions={d.sessions}
          total={d.totalSessions}
          onSessionSelect={ctx.onSessionSelect}
          selectedSessionDetail={ctx.selectedSessionDetail}
        />
      </div>
    ),
  },
  {
    id: "memory",
    label: () => "Memory & Security Logs",
    icon: Shield,
    iconClass: "text-rose-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: (d) => (
      <div className="space-y-8">
        <div className="space-y-4">
          <DataSourceBadge source={d.dataSources.memory} label="memory.db" />
          <MemoryExplorer memory={d.memory} />
        </div>
        <div className="space-y-4">
          <DataSourceBadge source={d.dataSources.audit} label="audit.log" />
          <AuditLogs logs={d.auditLogs} />
        </div>
      </div>
    ),
  },
  {
    id: "mcp",
    label: (d) => `MCP Servers (${d.mcpServers.length})`,
    icon: Plug,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: (d) => <McpServers servers={d.mcpServers} />,
  },
  {
    id: "mcpsdk",
    label: () => "MCP SDK",
    icon: Boxes,
    iconClass: "text-sky-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-sky-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) =>
      d.mcpSdk
        ? neutralBadge(`${d.mcpSdk.packages.length}p · ${d.mcpSdk.primitives.length}pr`)
        : null,
    render: (d) => <McpSdkPanel data={d.mcpSdk} />,
  },
  {
    id: "speckit",
    label: () => "SpecKit",
    icon: Layers,
    iconClass: "text-amber-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-amber-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) =>
      d.speckit?.present
        ? neutralBadge(`${d.speckit.workflows.length}w · ${d.speckit.templates.length}t`)
        : null,
    render: (d) => <SpecKitPanel data={d.speckit} />,
  },
  {
    id: "chatkit",
    label: () => "ChatKit",
    icon: MessagesSquare,
    iconClass: "text-fuchsia-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-fuchsia-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.chatkit ? neutralBadge(`${d.chatkit.samples.length} samples`) : null),
    render: (d) => <ChatKitPanel data={d.chatkit} />,
  },
  {
    id: "antigravity",
    label: () => "Antigravity",
    icon: Bot,
    iconClass: "text-cyan-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.antigravity ? neutralBadge(`${d.antigravity.primitives.length}p`) : null),
    render: (d) => <AntigravityPanel data={d.antigravity} />,
  },
  {
    id: "genkit",
    label: () => "Genkit",
    icon: Sparkles,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.genkit ? neutralBadge(`${d.genkit.providers.length}p`) : null),
    render: (d) => <GenkitPanel data={d.genkit} />,
  },
  {
    id: "conductor",
    label: () => "Conductor",
    icon: Music2,
    iconClass: "text-purple-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.conductor ? neutralBadge(`${d.conductor.commands.length}c`) : null),
    render: (d) => <ConductorPanel data={d.conductor} />,
  },
  {
    id: "otel",
    label: () => "Observability",
    icon: Telescope,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: (d) => <OtelPanel data={d.otel} />,
  },
  {
    id: "adk",
    label: () => "Google ADK",
    icon: Users,
    iconClass: "text-cyan-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.adk ? neutralBadge(`${d.adk.primitives.length}p`) : null),
    render: (d) => <GoogleAdkPanel data={d.adk} />,
  },
  {
    id: "learning",
    label: () => "Learning",
    icon: GraduationCap,
    iconClass: "text-amber-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-amber-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.learning ? neutralBadge(`${d.learning.resources.length}`) : null),
    render: (d) => <GcpLearningPanel data={d.learning} />,
  },
  {
    id: "m365",
    label: () => "M365 Copilot",
    icon: Fingerprint,
    iconClass: "text-sky-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-sky-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: (d) => <M365CopilotPanel data={d.m365} />,
  },
  {
    id: "autocycle",
    label: () => "Auto-Cycle",
    icon: RefreshCw,
    iconClass: "text-purple-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) =>
      d.autocycle ? neutralBadge(`${d.autocycle.personas.length}x${d.autocycle.roundCap}`) : null,
    render: (d) => <AutoCyclePanel data={d.autocycle} />,
  },
  {
    id: "specs",
    label: () => "Design Specs",
    icon: ScrollText,
    iconClass: "text-cyan-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.designSpecs?.present ? neutralBadge(`${d.designSpecs.specs.length}`) : null),
    render: (d) => <DesignSpecsPanel data={d.designSpecs} />,
  },
  {
    id: "gateway",
    label: () => "Agent Gateway",
    icon: ShieldCheck,
    iconClass: "text-rose-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-rose-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    badge: (d) => (d.gateway ? neutralBadge(`${d.gateway.controls.length}`) : null),
    render: (d) => (
      <div className="space-y-8">
        <GatewayRouterPanel />
        <AgentGatewayPanel data={d.gateway} />
      </div>
    ),
  },
  {
    id: "stitch",
    label: () => "Stitch Studio ⚡",
    icon: Sparkles,
    iconClass: "text-cyan-400",
    activeClass:
      "bg-gradient-to-r from-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-950/50",
    render: () => <StitchStudio />,
  },
  {
    id: "billing",
    label: () => "Billing",
    icon: DollarSign,
    iconClass: "text-emerald-400",
    activeClass:
      "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-950/50",
    render: () => <BillingManagementPanel />,
  },
  {
    id: "incidents",
    label: () => "Incidents/Self-Healing",
    icon: AlertTriangle,
    iconClass: "text-rose-400",
    activeClass:
      "bg-gradient-to-r from-rose-500/20 to-amber-500/20 text-rose-300 border border-rose-500/40 shadow-lg shadow-rose-950/50",
    render: () => <SelfHealingConsole />,
  },
];
