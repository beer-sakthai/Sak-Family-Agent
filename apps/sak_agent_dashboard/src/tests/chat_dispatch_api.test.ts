import { describe, it, expect } from 'vitest';
import { GET, POST } from '../app/api/chatkit/dispatch/route';
import { NextRequest } from 'next/server';

describe('ChatKit Dispatch API Route', () => {
  it('GET /api/chatkit/dispatch returns presets and recent staged entries', async () => {
    const res = await GET();
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.presets).toBeDefined();
    expect(data.presets.length).toBeGreaterThan(0);
    expect(Array.isArray(data.recentStaged)).toBe(true);
  });

  it('POST /api/chatkit/dispatch returns SSE stream with event chunks', async () => {
    const req = new NextRequest('http://localhost:3000/api/chatkit/dispatch', {
      method: 'POST',
      body: JSON.stringify({
        prompt: 'Verify security guardrails and CI workflows',
        personas: ['sakthai', 'sakking', 'sakjules'],
        preset: 'cloud_powerhouse',
      }),
    });

    const res = await POST(req);
    expect(res.headers.get('Content-Type')).toContain('text/event-stream');

    const reader = res.body?.getReader();
    expect(reader).toBeDefined();

    if (reader) {
      const decoder = new TextDecoder();
      let streamText = '';
      let done = false;

      while (!done) {
        const { value, done: isDone } = await reader.read();
        if (value) {
          streamText += decoder.decode(value, { stream: true });
        }
        done = isDone;
      }

      expect(streamText).toContain('session_start');
      expect(streamText).toContain('supervisor_plan');
      expect(streamText).toContain('persona_thought');
      expect(streamText).toContain('synthesis_chunk');
      expect(streamText).toContain('session_complete');
    }
  });
});
