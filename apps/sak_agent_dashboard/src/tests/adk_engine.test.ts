import { describe, it, expect } from 'vitest';
import {
  generateAdkPythonCode,
  getAllAdkSpecs,
  generateCloudDeploymentManifest,
  runQualityFlywheelEvaluation,
  getAgentRegistryStatus,
} from '../lib/adk/adk_engine';

describe('Google ADK Engine', () => {
  it('generates valid Python ADK agent code for personas', () => {
    const code = generateAdkPythonCode('sakking');
    expect(code).toContain('from google.adk import Agent, LlmAgent, Runner, tool');
    expect(code).toContain('sakking_agent = LlmAgent');
    expect(code).toContain('claude-3-5-sonnet-20241022');
    expect(code).toContain('ast_static_scan_tool');
  });

  it('returns all 6 ADK persona specifications', () => {
    const specs = getAllAdkSpecs();
    expect(specs).toHaveLength(6);
    expect(specs.map((s) => s.personaSlug)).toEqual(
      expect.arrayContaining(['sakthai', 'sakking', 'saksee', 'sakjules', 'saksit', 'saktan'])
    );
  });

  it('generates Cloud Run deployment manifest and hardened Dockerfile', () => {
    const manifest = generateCloudDeploymentManifest('cloud_run', 'sak-agent-runner', 'asia-southeast1');
    expect(manifest.target).toBe('cloud_run');
    expect(manifest.serviceName).toBe('sak-agent-runner');
    expect(manifest.region).toBe('asia-southeast1');
    expect(manifest.dockerfile).toContain('FROM python:3.11-slim as runner');
    expect(manifest.manifestYaml).toContain('apiVersion: serving.knative.dev/v1');
    expect(manifest.manifestYaml).toContain('run.googleapis.com/execution-environment: gen2');
  });

  it('generates GKE Kubernetes deployment manifest', () => {
    const manifest = generateCloudDeploymentManifest('gke', 'sak-agent-gke');
    expect(manifest.target).toBe('gke');
    expect(manifest.manifestYaml).toContain('apiVersion: apps/v1');
    expect(manifest.manifestYaml).toContain('kind: Deployment');
  });

  it('runs Quality Flywheel evaluation and returns high-accuracy metrics', () => {
    const evalRes = runQualityFlywheelEvaluation();
    expect(evalRes.overallAccuracy).toBeGreaterThan(90);
    expect(evalRes.toolCallingPrecision).toBeGreaterThan(90);
    expect(evalRes.safetyCompliance).toBe(100.0);
    expect(evalRes.metrics.length).toBeGreaterThanOrEqual(4);
  });

  it('returns Gemini Enterprise registry status', () => {
    const reg = getAgentRegistryStatus();
    expect(reg.fleetCount).toBe(6);
    expect(reg.publishedToEnterprise).toBe(true);
    expect(reg.registryEndpoint).toContain('gemini.enterprise.google');
  });
});
