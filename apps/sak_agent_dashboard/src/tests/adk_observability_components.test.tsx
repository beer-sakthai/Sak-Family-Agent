import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { AdkObservabilityExplorer } from '../components/adk/AdkObservabilityExplorer';

describe('AdkObservabilityExplorer Component', () => {
  it('renders Cloud Trace waterfall and BigQuery telemetry metrics', () => {
    render(<AdkObservabilityExplorer />);

    expect(screen.getByText(/Cloud Trace OpenTelemetry/i)).toBeDefined();
    expect(screen.getByText(/BigQuery Agent Analytics/i)).toBeDefined();
    expect(screen.getByText(/Prompt-Response Logging/i)).toBeDefined();
    expect(screen.getByText(/Live OpenTelemetry Span Hierarchy/i)).toBeDefined();
  });
});
