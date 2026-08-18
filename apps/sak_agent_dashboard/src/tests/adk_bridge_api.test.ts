import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/adk/bridge/route';
import { NextRequest } from 'next/server';

describe('Google ADK Bridge API Route', () => {
  it('GET /api/adk/bridge returns specs, default manifest, eval result, and registry status', async () => {
    const res = await GET();
    expect(res.status).toBe(200);
    const data = await res.json();

    expect(data.agents).toHaveLength(6);
    expect(data.manifest).toBeDefined();
    expect(data.evalResult).toBeDefined();
    expect(data.registryStatus.publishedToEnterprise).toBe(true);
  });

  it('POST /api/adk/bridge generate_code returns Python ADK script', async () => {
    const req = new NextRequest('http://localhost:3000/api/adk/bridge', {
      method: 'POST',
      body: JSON.stringify({
        action: 'generate_code',
        personaSlug: 'saksee',
      }),
    });

    const res = await POST(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.code).toContain('saksee_agent = LlmAgent');
  });

  it('POST /api/adk/bridge generate_manifest returns tailored Cloud Run YAML', async () => {
    const req = new NextRequest('http://localhost:3000/api/adk/bridge', {
      method: 'POST',
      body: JSON.stringify({
        action: 'generate_manifest',
        target: 'cloud_run',
        serviceName: 'prod-sak-fleet',
        region: 'europe-west1',
      }),
    });

    const res = await POST(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.manifest.serviceName).toBe('prod-sak-fleet');
    expect(data.manifest.region).toBe('europe-west1');
  });
});
