import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { A2ARegistryExplorer } from '../components/a2a/A2ARegistryExplorer';
import { A2APanel } from '../components/A2APanel';
import { INITIAL_SAK_FLEET } from '../lib/a2a/serviceRegistry';
import { A2ADelegationResult } from '../lib/a2a/types';

describe('A2ARegistryExplorer Component', () => {
  it('renders fleet agent cards and capability manifest', () => {
    const fleet = INITIAL_SAK_FLEET;
    const delegations: A2ADelegationResult[] = [];

    render(
      <A2ARegistryExplorer
        fleet={fleet}
        delegations={delegations}
      />
    );

    const julesElements = screen.getAllByText(/SakJules/i);
    expect(julesElements.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/A2A JSON-RPC 2.0 Test Bench/i)).toBeDefined();
    expect(screen.getByText(/Inter-Agent Delegation Telemetry Log/i)).toBeDefined();
  });

  it('triggers RPC dispatch callback on button click', async () => {
    const onRpc = vi.fn().mockResolvedValue({
      delegationId: 'test-del',
      correlationId: 'test-corr',
      agentFrom: 'sakking',
      agentTo: 'saksee',
      method: 'cap-see-ast',
      status: 'success',
      result: { ok: true },
      executionTimeMs: 40,
      astAudited: true,
      timestamp: new Date().toISOString()
    });

    render(
      <A2ARegistryExplorer
        fleet={INITIAL_SAK_FLEET}
        delegations={[]}
        onDelegateRpc={onRpc}
      />
    );

    const dispatchBtn = screen.getByRole('button', {
      name: /Dispatch A2A Remote Procedure Call/i
    });
    fireEvent.click(dispatchBtn);
    expect(onRpc).toHaveBeenCalled();
  });
});

describe('A2APanel Component', () => {
  it('renders top stats banner without errors', () => {
    render(<A2APanel />);
    expect(screen.getByText(/Fleet Service Nodes/i)).toBeDefined();
    expect(screen.getByText(/Registered Capabilities/i)).toBeDefined();
    expect(screen.getByText(/Average RPC Latency/i)).toBeDefined();
  });
});
