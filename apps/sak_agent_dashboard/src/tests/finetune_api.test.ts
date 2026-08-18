import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/learning/finetune/route';
import { NextRequest } from 'next/server';

describe('Fine-Tuning API Route', () => {
  it('GET /api/learning/finetune returns datasetCard and jobs list', async () => {
    const res = await GET();
    expect(res.status).toBe(200);
    const data = await res.json();

    expect(data.datasetCard).toBeDefined();
    expect(data.datasetCard.hfRepoId).toBe('Sak-Family/sakthai-combined-v7');
    expect(Array.isArray(data.jobs)).toBe(true);
  });

  it('POST /api/learning/finetune spawns new training job on valid body', async () => {
    const req = new NextRequest('http://localhost:3000/api/learning/finetune', {
      method: 'POST',
      body: JSON.stringify({
        modelName: 'sakthai-7b',
        r: 16,
        loraAlpha: 32,
        learningRate: 2e-4,
        numEpochs: 3,
        batchSize: 4,
      }),
    });

    const res = await POST(req);
    expect(res.status).toBe(201);
    const data = await res.json();

    expect(data.success).toBe(true);
    expect(data.job).toBeDefined();
    expect(data.job.modelName).toBe('sakthai-7b');
    expect(data.job.status).toBe('running');
  });

  it('POST /api/learning/finetune rejects invalid hyperparameters with 400', async () => {
    const req = new NextRequest('http://localhost:3000/api/learning/finetune', {
      method: 'POST',
      body: JSON.stringify({
        modelName: 'invalid-model',
        r: 0,
      }),
    });

    const res = await POST(req);
    expect(res.status).toBe(400);
    const data = await res.json();
    expect(data.error).toBe('Validation failed');
    expect(data.details.length).toBeGreaterThan(0);
  });
});
