import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/mutation/route';
import { NextRequest } from 'next/server';

describe('Mutation API Route', () => {
  it('GET /api/mutation returns sweeps and mutants', async () => {
    const req = new NextRequest('http://localhost:3000/api/mutation');
    const res = await GET(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.data.sweeps.length).toBeGreaterThanOrEqual(1);
    expect(json.data.mutants.length).toBeGreaterThanOrEqual(1);
  });

  it('POST /api/mutation sweep triggers new mutation test sweep', async () => {
    const req = new NextRequest('http://localhost:3000/api/mutation', {
      method: 'POST',
      body: JSON.stringify({
        action: 'sweep',
        targetFiles: ['src/lib/eval/evalEngine.ts'],
        operators: ['conditional_inversion', 'boolean_flip']
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.summary.totalMutants).toBeGreaterThan(0);
    expect(json.mutants.length).toBeGreaterThan(0);
  });

  it('POST /api/mutation heal synthesizes test for a mutant', async () => {
    const req = new NextRequest('http://localhost:3000/api/mutation', {
      method: 'POST',
      body: JSON.stringify({
        action: 'heal',
        mutantId: 'mut-seed-01'
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.healResult.verifiedKilled).toBe(true);
    expect(json.healResult.synthesizedTestCode).toContain('it(');
  });
});
