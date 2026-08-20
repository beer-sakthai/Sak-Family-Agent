import { describe, it, expect } from 'vitest';
import { AdkObservabilityEngine } from '../lib/adk/observability_engine';

describe('AdkObservabilityEngine', () => {
  it('generates sample OpenTelemetry trace waterfall with hierarchical spans', () => {
    const waterfall = AdkObservabilityEngine.generateSampleTraceWaterfall('Deploy Sak-Family cluster');
    expect(waterfall.traceId).toContain('trace-adk-');
    expect(waterfall.totalSpans).toBeGreaterThanOrEqual(5);
    expect(waterfall.spans).toHaveLength(1);

    const root = waterfall.spans[0];
    expect(root.kind).toBe('invoke_workflow');
    expect(root.children?.length).toBe(3);

    const kingSpan = root.children?.[0];
    expect(kingSpan?.kind).toBe('invoke_agent');
    expect(kingSpan?.children?.[0]?.kind).toBe('call_llm');
    expect(kingSpan?.children?.[0]?.children?.[0]?.kind).toBe('generate_content');
  });

  it('retrieves BigQuery agent analytics events', () => {
    const events = AdkObservabilityEngine.getBigQueryAnalyticsEvents();
    expect(events.length).toBeGreaterThanOrEqual(3);
    expect(events[0].bqDatasetId).toBe('sak_agent_analytics_prod');
    expect(events[0].astCompliant).toBe(true);
  });

  it('generates production environment variables for ADK deployment', () => {
    const envVars = AdkObservabilityEngine.generateObservabilityEnvVars(
      AdkObservabilityEngine.defaultTierConfig
    );
    expect(envVars.GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY).toBe('true');
    expect(envVars.OTEL_INSTRUMENTATION_GENAI_COMPLETION_HOOK).toBe('upload');
    expect(envVars.LOGS_BUCKET_NAME).toBe('gs://sak-agent-logs-prod');
    expect(envVars.BQ_ANALYTICS_DATASET_ID).toBe('sak_agent_analytics_prod');
    expect(envVars.OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT).toBe('NO_CONTENT');
  });

  it('generates valid Terraform telemetry snippet with IAM roles', () => {
    const tf = AdkObservabilityEngine.generateTerraformTelemetrySnippet(
      AdkObservabilityEngine.defaultTierConfig
    );
    expect(tf).toContain('google_storage_bucket');
    expect(tf).toContain('google_bigquery_dataset');
    expect(tf).toContain('roles/cloudtrace.agent');
    expect(tf).toContain('roles/bigquery.dataOwner');
  });
});
