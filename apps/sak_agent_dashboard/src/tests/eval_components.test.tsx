import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { EvalRadarChart } from '../components/eval/EvalRadarChart';
import { EvalRunTracker } from '../components/eval/EvalRunTracker';
import { QualityFlywheelManager } from '../components/eval/QualityFlywheelManager';
import { EvalQualityFlywheelPanel } from '../components/EvalQualityFlywheelPanel';
import { GOLDEN_TEST_CASES, GOLDEN_EVAL_DATASETS } from '../lib/eval/datasets';
import { QualityFlywheelEngine } from '../lib/eval/qualityFlywheel';

describe('EvalRadarChart Component', () => {
  it('renders radar dimensions and persona cards', () => {
    const mockSummaries = [
      {
        personaSlug: 'sakjules',
        personaName: 'SakJules (Automation)',
        totalTests: 5,
        passRate: 100,
        avgCompositeScore: 92,
        avgGoalCompletion: 95,
        avgToolPrecision: 90,
        avgSafetyCompliance: 100,
        avgLatencyMs: 240
      },
      {
        personaSlug: 'saksee',
        personaName: 'SakSee (Security Sentinel)',
        totalTests: 4,
        passRate: 100,
        avgCompositeScore: 96,
        avgGoalCompletion: 98,
        avgToolPrecision: 94,
        avgSafetyCompliance: 100,
        avgLatencyMs: 180
      }
    ];

    const onSelect = vi.fn();
    render(<EvalRadarChart summaries={mockSummaries} onSelectPersona={onSelect} />);

    expect(screen.getByText(/Multi-Dimensional Evaluation Radar/i)).toBeDefined();
    const julesElements = screen.getAllByText(/SakJules \(Automation\)/i);
    expect(julesElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/SakSee \(Security Sentinel\)/i)).toBeDefined();
    expect(screen.getByText(/92 \/ 100/i)).toBeDefined();

    fireEvent.click(julesElements[0]);
    expect(onSelect).toHaveBeenCalledWith('sakjules');
  });
});

describe('EvalRunTracker Component', () => {
  it('renders benchmark cases and triggers execution handler', () => {
    const onTrigger = vi.fn();
    render(
      <EvalRunTracker
        isRunning={false}
        results={[]}
        availableTestCases={GOLDEN_TEST_CASES.slice(0, 3)}
        onTriggerRun={onTrigger}
      />
    );

    expect(screen.getByText(/Evaluation Arena & Automated Runner/i)).toBeDefined();
    const runBtn = screen.getByRole('button', { name: /Run Selected/i });
    expect(runBtn).toBeDefined();

    fireEvent.click(runBtn);
    expect(onTrigger).toHaveBeenCalled();
  });
});

describe('QualityFlywheelManager Component', () => {
  it('switches between Failure Triage and Golden Datasets views', () => {
    const failures = QualityFlywheelEngine.getFailureEntries();
    const datasets = GOLDEN_EVAL_DATASETS;

    const onTriage = vi.fn();
    render(
      <QualityFlywheelManager
        datasets={datasets}
        failures={failures}
        onTriageFailure={onTriage}
      />
    );

    expect(screen.getByText(/Quality Flywheel & Continuous Curation/i)).toBeDefined();
    expect(screen.getByText(/Runtime Failures Requiring Review/i)).toBeDefined();

    // Switch to Golden Datasets tab
    const datasetsTab = screen.getByRole('button', { name: /Golden Datasets/i });
    fireEvent.click(datasetsTab);
    const datasetTitles = screen.getAllByText(/Sak-Family Core Golden Benchmark Suite v1.0/i);
    expect(datasetTitles.length).toBeGreaterThanOrEqual(1);
  });
});

describe('EvalQualityFlywheelPanel Component', () => {
  it('renders top stats banner and main layout without crashing', () => {
    render(<EvalQualityFlywheelPanel />);
    expect(screen.getByText(/Overall Benchmark Pass Rate/i)).toBeDefined();
    expect(screen.getByText(/Average Composite G-Eval/i)).toBeDefined();
    expect(screen.getByText(/AST Guardrail Compliance/i)).toBeDefined();
  });
});
