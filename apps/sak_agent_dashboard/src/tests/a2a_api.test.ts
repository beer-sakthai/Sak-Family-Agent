import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/a2a/registry/route';
import { NextRequest } from 'next/server';

describe('A2A Registry API Route', () => {
  it('GET /api/a2a/registry returns fleet, health, and recent delegations', async () => {
    const req = new NextRequest('http://localhost:3000/api/a2a/registry');
    const res = await GET(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.data.fleet).toHaveLength(6);
    expect(json.data.health.fleetSize).toBe(6);
    expect(json.data.delegations.length).toBeGreaterThanOrEqual(1);
  });

  it('POST /api/a2a/registry delegate executes peer RPC', async () => {
    const req = new NextRequest('http://localhost:3000/api/a2a/registry', {
      method: 'POST',
      body: JSON.stringify({
        action: 'delegate',
        agentFrom: 'sakking',
        agentTo: 'saksee',
        capabilityId: 'cap-see-ast',
        payload: { command: 'git status', targetPath: '.' }
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.result.status).toBe('success');
    expect(json.result.agentTo).toBe('saksee');
  });

  it('POST /api/a2a/registry heartbeat records heartbeat', async () => {
    const req = new NextRequest('http://localhost:3000/api/a2a/registry', {
      method: 'POST',
      body: JSON.stringify({
        action: 'heartbeat',
        agentSlug: 'sakjules'
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
  });

  it('POST /api/a2a/registry discover returns matching capabilities', async () => {
    const req = new NextRequest('http://localhost:3000/api/a2a/registry', {
      method: 'POST',
      body: JSON.stringify({
        action: 'discover',
        category: 'coding'
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.capabilities.length).toBeGreaterThanOrEqual(2);
  });
});
