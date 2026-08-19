import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/auto-cycle/route';
import { NextRequest } from 'next/server';

describe('AutoCycle API Route', () => {
  it('GET /api/auto-cycle returns autocycle overview and live persona states', async () => {
    const res = await GET();
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.autocycle.stages.length).toBe(6);
    expect(json.cycleStates.SakThai).toBeDefined();
  });

  it('POST /api/auto-cycle step advances stage for persona', async () => {
    const req = new NextRequest('http://localhost:3000/api/auto-cycle', {
      method: 'POST',
      body: JSON.stringify({
        action: 'step',
        persona: 'SakKing',
        task: 'Multi-agent orchestration loop',
      }),
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.stepResult.persona).toBe('SakKing');
    expect(json.stepResult.artifact).toBeDefined();
  });
});
