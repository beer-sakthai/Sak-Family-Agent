import {
  OtelTraceSpan,
  TraceWaterfallSummary,
  BigQueryAgentAnalyticsEvent,
  ObservabilityTierConfig
} from './observability_types';

/**
 * Google ADK Observability & OpenTelemetry Engine.
 * Handles Cloud Trace span hierarchies, BigQuery analytics event streaming,
 * and Terraform infrastructure configuration generation.
 */

export class AdkObservabilityEngine {
  public static defaultTierConfig: ObservabilityTierConfig = {
    cloudTraceEnabled: true,
    gcsPromptLoggingEnabled: true,
    bqAnalyticsEnabled: true,
    semconvLevel: 'NO_CONTENT',
    logsBucketName: 'gs://sak-agent-logs-prod',
    bqDatasetId: 'sak_agent_analytics_prod',
    telemetryProject: 'sak-family-cloud'
  };

  /**
   * Predefined multi-agent simulation scenarios.
   */
  public static simulationScenarios = [
    {
      id: 'geval_security',
      title: 'Orchestrate Multi-Agent G-Eval & AST Security Verification',
      primaryPersonas: ['SakKing', 'SakSee', 'SakJules']
    },
    {
      id: 'cache_analytics',
      title: 'Real-time Semantic Cache Optimization & Token Burn Audit',
      primaryPersonas: ['SakTan', 'SakNoi', 'SakThai']
    },
    {
      id: 'mutation_cicd',
      title: 'Autonomous Mutation Testing & Self-Healing CI Deployment',
      primaryPersonas: ['SakJules', 'SakSee', 'SakKing']
    }
  ];

  /**
   * Generate an OpenTelemetry Trace Waterfall for an agent workflow run.
   */
  public static generateSampleTraceWaterfall(
    scenarioId = 'geval_security'
  ): TraceWaterfallSummary {
    const traceId = `trace-adk-${Date.now()}`;
    const t0 = 0;

    if (scenarioId === 'cache_analytics') {
      const childSpans: OtelTraceSpan[] = [
        {
          spanId: 'span-agent-tan',
          parentSpanId: 'span-root',
          name: 'invoke_agent: SakTan (Analytics & Cost)',
          kind: 'invoke_agent',
          status: 'OK',
          startTimeMs: t0 + 10,
          durationMs: 420,
          attributes: {
            agentSlug: 'saktan',
            model: 'gemini-1.5-flash',
            promptTokens: 410,
            completionTokens: 180,
            totalTokens: 590,
            costUsd: 0.0004
          },
          children: [
            {
              spanId: 'span-tool-cache',
              parentSpanId: 'span-agent-tan',
              name: 'execute_tool: semantic_cache_lookup',
              kind: 'execute_tool',
              status: 'OK',
              startTimeMs: t0 + 20,
              durationMs: 85,
              attributes: {
                toolName: 'semantic_cache_lookup',
                similarityScore: 0.94,
                cacheHit: true
              }
            }
          ]
        },
        {
          spanId: 'span-agent-thai',
          parentSpanId: 'span-root',
          name: 'invoke_agent: SakThai (Core Reasoning)',
          kind: 'invoke_agent',
          status: 'OK',
          startTimeMs: t0 + 440,
          durationMs: 650,
          attributes: {
            agentSlug: 'sakthai',
            model: 'gemini-1.5-pro',
            promptTokens: 890,
            completionTokens: 310,
            totalTokens: 1200,
            costUsd: 0.0029
          }
        }
      ];

      return {
        traceId,
        rootWorkflow: 'Real-time Semantic Cache Optimization & Token Burn Audit',
        totalSpans: 4,
        totalDurationMs: 1100,
        totalTokens: 1790,
        totalCostUsd: 0.0033,
        spans: [
          {
            spanId: 'span-root',
            name: 'invoke_workflow: Real-time Semantic Cache Optimization',
            kind: 'invoke_workflow',
            status: 'OK',
            startTimeMs: t0,
            durationMs: 1100,
            attributes: { totalTokens: 1790, totalCostUsd: 0.0033 },
            children: childSpans
          }
        ]
      };
    }

    if (scenarioId === 'mutation_cicd') {
      const childSpans: OtelTraceSpan[] = [
        {
          spanId: 'span-agent-jules',
          parentSpanId: 'span-root',
          name: 'invoke_agent: SakJules (CI/CD Automation)',
          kind: 'invoke_agent',
          status: 'OK',
          startTimeMs: t0 + 10,
          durationMs: 920,
          attributes: {
            agentSlug: 'sakjules',
            model: 'claude-3-5-sonnet-20241022',
            promptTokens: 1100,
            completionTokens: 480,
            totalTokens: 1580,
            costUsd: 0.0105
          },
          children: [
            {
              spanId: 'span-tool-mutant',
              parentSpanId: 'span-agent-jules',
              name: 'execute_tool: inject_ast_mutations',
              kind: 'execute_tool',
              status: 'OK',
              startTimeMs: t0 + 30,
              durationMs: 310,
              attributes: {
                toolName: 'inject_ast_mutations',
                mutantsKilled: 26,
                totalMutants: 28,
                mutationScore: 92.9
              }
            },
            {
              spanId: 'span-tool-heal',
              parentSpanId: 'span-agent-jules',
              name: 'execute_tool: synthesize_auto_healer_test',
              kind: 'execute_tool',
              status: 'OK',
              startTimeMs: t0 + 350,
              durationMs: 220,
              attributes: {
                toolName: 'synthesize_auto_healer_test',
                synthesizedTestsCount: 2,
                verifiedKilled: true
              }
            }
          ]
        }
      ];

      return {
        traceId,
        rootWorkflow: 'Autonomous Mutation Testing & Self-Healing CI Deployment',
        totalSpans: 4,
        totalDurationMs: 950,
        totalTokens: 1580,
        totalCostUsd: 0.0105,
        spans: [
          {
            spanId: 'span-root',
            name: 'invoke_workflow: Autonomous Mutation Testing & Self-Healing CI',
            kind: 'invoke_workflow',
            status: 'OK',
            startTimeMs: t0,
            durationMs: 950,
            attributes: { totalTokens: 1580, totalCostUsd: 0.0105 },
            children: childSpans
          }
        ]
      };
    }

    // Default: geval_security
    const childSpans: OtelTraceSpan[] = [
      {
        spanId: 'span-agent-king',
        parentSpanId: 'span-root',
        name: 'invoke_agent: SakKing (Supervisor)',
        kind: 'invoke_agent',
        status: 'OK',
        startTimeMs: t0 + 15,
        durationMs: 850,
        attributes: {
          agentSlug: 'sakking',
          model: 'gemini-1.5-pro',
          promptTokens: 820,
          completionTokens: 340,
          totalTokens: 1160,
          costUsd: 0.0028
        },
        children: [
          {
            spanId: 'span-llm-king',
            parentSpanId: 'span-agent-king',
            name: 'call_llm: gemini-1.5-pro',
            kind: 'call_llm',
            status: 'OK',
            startTimeMs: t0 + 25,
            durationMs: 780,
            attributes: {
              model: 'gemini-1.5-pro',
              promptTokens: 820,
              completionTokens: 340
            },
            children: [
              {
                spanId: 'span-gen-king',
                parentSpanId: 'span-llm-king',
                name: 'generate_content',
                kind: 'generate_content',
                status: 'OK',
                startTimeMs: t0 + 35,
                durationMs: 760,
                attributes: { model: 'gemini-1.5-pro' }
              }
            ]
          }
        ]
      },
      {
        spanId: 'span-agent-see',
        parentSpanId: 'span-root',
        name: 'invoke_agent: SakSee (AST Security Sentinel)',
        kind: 'invoke_agent',
        status: 'OK',
        startTimeMs: t0 + 880,
        durationMs: 190,
        attributes: {
          agentSlug: 'saksee',
          model: 'gemini-1.5-pro',
          promptTokens: 450,
          completionTokens: 90,
          totalTokens: 540,
          costUsd: 0.0011
        },
        children: [
          {
            spanId: 'span-tool-ast',
            parentSpanId: 'span-agent-see',
            name: 'execute_tool: ast_guardrail_check',
            kind: 'execute_tool',
            status: 'OK',
            startTimeMs: t0 + 910,
            durationMs: 45,
            attributes: {
              toolName: 'ast_guardrail_check',
              pathTested: 'apps/sak_agent_dashboard',
              violationsFound: 0
            }
          }
        ]
      },
      {
        spanId: 'span-agent-jules',
        parentSpanId: 'span-root',
        name: 'invoke_agent: SakJules (CI/CD Quality Gate)',
        kind: 'invoke_agent',
        status: 'OK',
        startTimeMs: t0 + 1090,
        durationMs: 410,
        attributes: {
          agentSlug: 'sakjules',
          model: 'claude-3-5-sonnet-20241022',
          promptTokens: 950,
          completionTokens: 420,
          totalTokens: 1370,
          costUsd: 0.0091
        },
        children: [
          {
            spanId: 'span-tool-ci',
            parentSpanId: 'span-agent-jules',
            name: 'execute_tool: run_vitest_mutation_suite',
            kind: 'execute_tool',
            status: 'OK',
            startTimeMs: t0 + 1120,
            durationMs: 280,
            attributes: {
              toolName: 'run_vitest_mutation_suite',
              passCount: 12,
              mutationScore: 92.9
            }
          }
        ]
      }
    ];

    const rootSpan: OtelTraceSpan = {
      spanId: 'span-root',
      name: 'invoke_workflow: Orchestrate Multi-Agent G-Eval & AST Security Verification',
      kind: 'invoke_workflow',
      status: 'OK',
      startTimeMs: t0,
      durationMs: 1520,
      attributes: {
        agentCount: 3,
        totalTokens: 3070,
        totalCostUsd: 0.013
      },
      children: childSpans
    };

    return {
      traceId,
      rootWorkflow: 'Orchestrate Multi-Agent G-Eval & AST Security Verification',
      totalSpans: 7,
      totalDurationMs: 1520,
      totalTokens: 3070,
      totalCostUsd: 0.013,
      spans: [rootSpan]
    };
  }

  /**
   * Return recent BigQuery Agent Analytics telemetry events.
   */
  public static getBigQueryAnalyticsEvents(): BigQueryAgentAnalyticsEvent[] {
    return [
      {
        eventId: 'bq-evt-001',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        agentSlug: 'sakking',
        sessionToken: 'sess-orch-9821',
        eventType: 'agent_handoff',
        model: 'gemini-1.5-pro',
        latencyMs: 850,
        totalTokens: 1160,
        costUsd: 0.0028,
        bqDatasetId: 'sak_agent_analytics_prod',
        gcsLogUri: 'gs://sak-agent-logs-prod/traces/sess-orch-9821.jsonl',
        astCompliant: true
      },
      {
        eventId: 'bq-evt-002',
        timestamp: new Date(Date.now() - 90000).toISOString(),
        agentSlug: 'saksee',
        sessionToken: 'sess-sec-4412',
        eventType: 'guardrail_verdict',
        model: 'gemini-1.5-pro',
        latencyMs: 190,
        totalTokens: 540,
        costUsd: 0.0011,
        bqDatasetId: 'sak_agent_analytics_prod',
        gcsLogUri: 'gs://sak-agent-logs-prod/traces/sess-sec-4412.jsonl',
        astCompliant: true
      },
      {
        eventId: 'bq-evt-003',
        timestamp: new Date(Date.now() - 30000).toISOString(),
        agentSlug: 'sakjules',
        sessionToken: 'sess-ci-1092',
        eventType: 'tool_use',
        model: 'claude-3-5-sonnet-20241022',
        latencyMs: 410,
        totalTokens: 1370,
        costUsd: 0.0091,
        bqDatasetId: 'sak_agent_analytics_prod',
        gcsLogUri: 'gs://sak-agent-logs-prod/traces/sess-ci-1092.jsonl',
        astCompliant: true
      }
    ];
  }

  /**
   * Generate production environment variables for ADK deployment based on tier config.
   */
  public static generateObservabilityEnvVars(config: ObservabilityTierConfig): Record<string, string> {
    const envVars: Record<string, string> = {
      GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY: config.cloudTraceEnabled ? 'true' : 'false',
      OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT: config.semconvLevel
    };

    if (config.gcsPromptLoggingEnabled) {
      envVars.OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK = 'upload';
      envVars.LOGS_BUCKET_NAME = config.logsBucketName;
    }

    if (config.bqAnalyticsEnabled) {
      envVars.BQ_ANALYTICS_DATASET_ID = config.bqDatasetId;
    }

    return envVars;
  }

  /**
   * Generate Terraform HCL snippet for provisioning telemetry resources.
   */
  public static generateTerraformTelemetrySnippet(config: ObservabilityTierConfig): string {
    return `# Google ADK Observability & Telemetry Infrastructure
# Provisioned for project: ${config.telemetryProject}

resource "google_storage_bucket" "adk_logs_bucket" {
  name          = "${config.logsBucketName.replace('gs://', '')}"
  location      = "US"
  force_destroy = false
  uniform_bucket_level_access = true
}

resource "google_bigquery_dataset" "adk_analytics_dataset" {
  dataset_id                  = "${config.bqDatasetId}"
  friendly_name               = "Sak-Family ADK Agent Analytics"
  description                 = "Structured agent telemetry events, token metrics, and tool execution logs"
  location                    = "US"
  default_table_expiration_ms = 7776000000 # 90 days
}

resource "google_project_iam_member" "adk_telemetry_roles" {
  for_each = toset([
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/storage.admin",
    "roles/bigquery.dataOwner",
    "roles/bigquery.jobUser"
  ])
  project = "${config.telemetryProject}"
  role    = each.key
  member  = "serviceAccount:sak-agent-sa@\${var.project_id}.iam.gserviceaccount.com"
}
`;
  }
}
