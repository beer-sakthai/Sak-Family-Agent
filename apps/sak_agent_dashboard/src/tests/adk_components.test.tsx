import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AdkCodeViewer } from '../components/adk/AdkCodeViewer';
import { CloudDeploymentBuilder } from '../components/adk/CloudDeploymentBuilder';
import { QualityFlywheelGauge } from '../components/adk/QualityFlywheelGauge';
import { GoogleAdkBridgePanel } from '../components/GoogleAdkBridgePanel';
import {
  getAllAdkSpecs,
  generateCloudDeploymentManifest,
  runQualityFlywheelEvaluation,
} from '../lib/adk/adk_engine';

describe('AdkCodeViewer Component', () => {
  it('renders persona selector and displays Python code for selected persona', () => {
    const specs = getAllAdkSpecs();
    render(<AdkCodeViewer agents={specs} />);

    expect(screen.getByText(/Google ADK Agent Code Generator/i)).toBeDefined();
    expect(screen.getByText('SakThai')).toBeDefined();
    expect(screen.getByText('SakKing')).toBeDefined();

    // Switch to SakKing
    fireEvent.click(screen.getByText('SakKing'));
    expect(screen.getByText(/sakking_agent = LlmAgent/i)).toBeDefined();
  });
});

describe('CloudDeploymentBuilder Component', () => {
  it('switches between Cloud Run and GKE targets and toggles Dockerfile tab', () => {
    const initialManifest = generateCloudDeploymentManifest('cloud_run');
    const onGenerate = vi.fn().mockImplementation((target, serviceName, region) =>
      Promise.resolve(generateCloudDeploymentManifest(target, serviceName, region))
    );

    render(<CloudDeploymentBuilder initialManifest={initialManifest} onGenerateManifest={onGenerate} />);

    expect(screen.getByText(/Cloud Run & GKE Deployment Scaffolder/i)).toBeDefined();
    expect(screen.getByText(/service.yaml \(Knative\)/i)).toBeDefined();

    // Switch tab to Dockerfile
    const dockerfileTab = screen.getByText(/Dockerfile \(Multi-Stage Hardened\)/i);
    fireEvent.click(dockerfileTab);
    expect(screen.getByText(/FROM python:3.11-slim as runner/i)).toBeDefined();
  });
});

describe('QualityFlywheelGauge Component', () => {
  it('renders accuracy metrics and triggers evaluation callback', () => {
    const evalRes = runQualityFlywheelEvaluation();
    const onRunEval = vi.fn().mockResolvedValue(undefined);

    render(<QualityFlywheelGauge evalResult={evalRes} onRunEval={onRunEval} />);

    expect(screen.getByText(/Quality Flywheel & LLM-as-Judge Evaluation/i)).toBeDefined();
    expect(screen.getByText(/Overall Accuracy/i)).toBeDefined();
    expect(screen.getByText(`${evalRes.overallAccuracy}%`)).toBeDefined();

    const evalBtn = screen.getByRole('button', { name: /Run Quality Eval/i });
    fireEvent.click(evalBtn);
    expect(onRunEval).toHaveBeenCalled();
  });
});

describe('GoogleAdkBridgePanel Component', () => {
  it('renders the complete Google ADK Bridge panel', () => {
    render(<GoogleAdkBridgePanel />);
    expect(screen.getByText(/Google ADK & Cloud Deployment Bridge/i)).toBeDefined();
    expect(screen.getByText(/Track 20260818/i)).toBeDefined();
    expect(screen.getByText(/Gemini Enterprise/i)).toBeDefined();
  });
});
