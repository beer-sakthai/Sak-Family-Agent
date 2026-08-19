import { describe, it, expect } from 'vitest';
import { ServiceRegistry } from '../lib/a2a/serviceRegistry';
import { A2AEngine } from '../lib/a2a/a2aEngine';
import { isValidA2AEnvelope, isValidServiceRegistration } from '../lib/a2a/types';

describe('ServiceRegistry', () => {
  it('registers all 6 Sak-Family personas with active capabilities', () => {
    const fleet = ServiceRegistry.getAllAgents();
    expect(fleet).toHaveLength(6);

    const slugs = fleet.map((a) => a.agentSlug);
    expect(slugs).toEqual(
      expect.arrayContaining(['sakjules', 'saksee', 'sakking', 'saktan', 'sakthai', 'saknoi'])
    );
  });

  it('validates service registration schema with runtime guard', () => {
    const jules = ServiceRegistry.getAgent('sakjules');
    expect(jules).toBeDefined();
    expect(isValidServiceRegistration(jules)).toBe(true);
  });

  it('discovers capabilities filtered by category', () => {
    const securityCaps = ServiceRegistry.discoverCapabilities('security');
    expect(securityCaps.length).toBeGreaterThanOrEqual(2);
    expect(securityCaps[0].agentSlug).toBe('saksee');

    const allCaps = ServiceRegistry.discoverCapabilities();
    expect(allCaps.length).toBeGreaterThanOrEqual(6);
  });

  it('computes accurate fleet health telemetry', () => {
    const health = ServiceRegistry.getFleetHealth();
    expect(health.fleetSize).toBe(6);
    expect(health.healthyNodes).toBe(6);
    expect(health.uptimePercentage).toBe(100.0);
    expect(health.avgFleetLatencyMs).toBeGreaterThan(0);
  });
});

describe('A2AEngine', () => {
  it('creates standardized JSON-RPC 2.0 message envelopes', () => {
    const env = A2AEngine.createEnvelope('sakking', 'sakjules', 'cap-jules-docker', { test: true });
    expect(env.jsonrpc).toBe('2.0');
    expect(env.agentFrom).toBe('sakking');
    expect(env.agentTo).toBe('sakjules');
    expect(env.correlationId).toContain('sakking-sakjules');
    expect(isValidA2AEnvelope(env)).toBe(true);
  });

  it('successfully executes authenticated task delegation', async () => {
    const result = await A2AEngine.delegateTask({
      agentFrom: 'sakking',
      agentTo: 'sakjules',
      capabilityId: 'cap-jules-docker',
      payload: { framework: 'nextjs', nodeVersion: 20 }
    });

    expect(result.status).toBe('success');
    expect(result.astAudited).toBe(true);
    expect(result.executionTimeMs).toBeGreaterThan(0);
  });

  it('blocks delegations that violate AST security guardrails', async () => {
    const result = await A2AEngine.delegateTask({
      agentFrom: 'unknown-client',
      agentTo: 'sakjules',
      capabilityId: 'cap-jules-docker',
      payload: { targetPath: '/etc/shadow' }
    });

    expect(result.status).toBe('failed');
    expect(result.error).toContain('AST Security Gate');
  });
});
