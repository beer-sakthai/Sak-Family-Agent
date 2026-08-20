/**
 * types/integrations.ts — Integration types: MCP, OTEL, ADK, Genkit, Conductor, SpecKit,
 * ChatKit, Antigravity, Gateway, SpecKit, Providers, Workflow, etc.
 *
 * Extracted from the monolithic types.ts. Imported via `@/lib/types` barrel.
 */

export type {
  McpActionStability, McpActionCategory, McpAction, McpToolShortcut,
  McpEnvVar, McpRegistrationTarget, McpServerStatus, McpServerSpec, McpServersApiResponse,
} from "../types";

export type {
  SpecKitInitOptions, SpecKitIntegrationState, SpecKitTemplate,
  SpecKitWorkflowStepKind, SpecKitWorkflowStep, SpecKitWorkflow,
  SpecKitIntegrationManifest, SpecKitConstitution, SpecKitData, SpecKitApiResponse,
  SpecKitUpstreamCommand, SpecKitUpstream,
} from "../types";

export type {
  SdkPrimitiveKind, SdkPrimitive, SdkPackage, SdkUsageSite,
  SdkScaffoldFile, McpSdkData, McpSdkApiResponse,
} from "../types";

export type {
  ChatKitCapability, ChatKitSample, ChatKitPrerequisite, ChatKitData, ChatKitApiResponse,
} from "../types";

export type {
  AntigravityPrimitiveKind, AntigravityPrimitive, AntigravityFeature,
  AntigravityComparisonRow, AntigravityData, AntigravityApiResponse,
} from "../types";

export type {
  GenkitPrimitiveKind, GenkitPrimitive, GenkitProvider, GenkitData, GenkitApiResponse,
} from "../types";

export type {
  ConductorHost, ConductorCommand, ConductorArtifact, ConductorData, ConductorApiResponse,
} from "../types";

export type {
  OtelSignal, OtelSignalCard, OtelExporter, OtelSemConv, OtelData, OtelApiResponse,
} from "../types";

export type {
  AdkPrimitiveKind, AdkPrimitive, AdkAppField, AdkPlugin,
  AdkCrossCuttingConfig, AdkA2aService, AdkData, AdkApiResponse,
} from "../types";

export type {
  GatewayControl, GatewayMode, GatewayMcpService, GatewayStep, GatewayData, GatewayApiResponse,
} from "../types";

export type {
  ProviderType, ModelSpec, ProviderSpec, WorkflowStage, WorkflowTopology, WorkflowExecutionResult,
} from "../types";

export type {
  TelemetryEventType, TelemetryEvent, StreamEventPayload,
} from "../types";

export type { StitchScreenPreset } from "../types";
