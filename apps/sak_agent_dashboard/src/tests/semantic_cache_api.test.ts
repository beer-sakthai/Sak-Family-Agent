import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/cache/route';
import { NextRequest } from 'next/server';

describe('Semantic Cache API Route', () => {
  it('GET /api/cache returns analytics and active cached entries', async () => {
    const req = new NextRequest('http://localhost:3000/api/cache');
    const res = await GET(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.data.analytics.totalLookups).toBeGreaterThan(0);
    expect(json.data.entries.length).toBeGreaterThanOrEqual(1);
  });

  it('POST /api/cache lookup performs vector search and returns hit/miss', async () => {
    const req = new NextRequest('http://localhost:3000/api/cache', {
      method: 'POST',
      body: JSON.stringify({
        action: 'lookup',
        prompt: 'Generate minimal rootless multi-stage Dockerfile for Next.js 15 app',
        minSimilarity: 0.85
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.result.hit).toBe(true);
    expect(json.result.similarity).toBeGreaterThanOrEqual(0.85);
  });

  it('POST /api/cache store and invalidate manages entries', async () => {
    const storeReq = new NextRequest('http://localhost:3000/api/cache', {
      method: 'POST',
      body: JSON.stringify({
        action: 'store',
        prompt: 'Temporary Cache Test Prompt 12345',
        response: 'Temporary Cache Response 67890',
        personaSlug: 'saksee',
        model: 'gemini-1.5-flash',
        ttlSeconds: 600
      })
    });

    const storeRes = await POST(storeReq);
    expect(storeRes.status).toBe(200);
    const storeJson = await storeRes.json();
    expect(storeJson.success).toBe(true);
    expect(storeJson.entry.id).toBeDefined();

    const invalidateReq = new NextRequest('http://localhost:3000/api/cache', {
      method: 'POST',
      body: JSON.stringify({
        action: 'invalidate',
        id: storeJson.entry.id
      })
    });

    const invalidateRes = await POST(invalidateReq);
    expect(invalidateRes.status).toBe(200);
    const invalidateJson = await invalidateRes.json();
    expect(invalidateJson.success).toBe(true);
    expect(invalidateJson.deletedCount).toBe(1);
  });
});
