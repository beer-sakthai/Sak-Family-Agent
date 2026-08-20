import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/eval/route';
import { NextRequest } from 'next/server';

describe('Eval & Quality Flywheel API Route', () => {
  it('GET /api/eval returns datasets, failures, test cases, and summaries', async () => {
    const req = new NextRequest('http://localhost:3000/api/eval');
    const res = await GET(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.data.datasets.length).toBeGreaterThanOrEqual(2);
    expect(json.data.testCases.length).toBeGreaterThanOrEqual(6);
    expect(json.data.failures.length).toBeGreaterThanOrEqual(1);
  });

  it('GET /api/eval?action=datasets returns datasets only', async () => {
    const req = new NextRequest('http://localhost:3000/api/eval?action=datasets');
    const res = await GET(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.datasets.length).toBeGreaterThanOrEqual(2);
  });

  it('POST /api/eval run_eval executes selected tests and returns scores', async () => {
    const req = new NextRequest('http://localhost:3000/api/eval', {
      method: 'POST',
      body: JSON.stringify({
        action: 'run_eval',
        testCaseIds: ['eval-jules-01'],
        config: {
          personaSlugs: ['sakjules'],
          judgeModel: 'gemini-1.5-pro',
          concurrency: 1,
          enableCoT: true,
          enableOrderShuffling: false,
          passThreshold: 75
        }
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.results.length).toBe(1);
    expect(json.results[0].judgeScore).toBeDefined();
    expect(json.report).toContain('SakJules');
  });

  it('POST /api/eval triage_failure promotes a failure into a golden test case', async () => {
    const req = new NextRequest('http://localhost:3000/api/eval', {
      method: 'POST',
      body: JSON.stringify({
        action: 'triage_failure',
        failureId: 'fail-seed-01',
        promoteToGolden: true
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.promotedTestCase).toBeDefined();
    expect(json.promotedTestCase.isGolden).toBe(true);
  });

  it('POST /api/eval generate_synthetic returns generated test case', async () => {
    const req = new NextRequest('http://localhost:3000/api/eval', {
      method: 'POST',
      body: JSON.stringify({
        action: 'generate_synthetic',
        personaSlug: 'saksee',
        category: 'security',
        mutationType: 'adversarial'
      })
    });

    const res = await POST(req);
    expect(res.status).toBe(200);

    const json = await res.json();
    expect(json.success).toBe(true);
    expect(json.testCase.personaSlug).toBe('saksee');
    expect(json.testCase.category).toBe('security');
  });
});
