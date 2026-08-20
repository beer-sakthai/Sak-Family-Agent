import { describe, it, expect } from 'vitest';
import { GET as WebhookGET, POST as WebhookPOST } from '../app/api/telegram/webhook/route';
import { GET as IncidentsGET, POST as IncidentsPOST } from '../app/api/telegram/incidents/route';
import { NextRequest } from 'next/server';

describe('Telegram Webhook & Incident API Routes', () => {
  it('GET /api/telegram/webhook returns webhook status', async () => {
    const res = await WebhookGET();
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.connected).toBe(true);
    expect(data.botUsername).toBe('@SakFamilyBot');
  });

  it('POST /api/telegram/webhook voice simulation returns transcription', async () => {
    const req = new NextRequest('http://localhost:3000/api/telegram/webhook', {
      method: 'POST',
      body: JSON.stringify({
        type: 'voice_simulation',
        text: 'ขอเช็คหน้าจอและสี ui ล่าสุดครับ',
      }),
    });

    const res = await WebhookPOST(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.targetPersona).toBe('saksee');
  });

  it('GET /api/telegram/incidents returns incidents and voice profiles', async () => {
    const res = await IncidentsGET();
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data.incidents)).toBe(true);
    expect(data.voices.length).toBe(6);
  });

  it('POST /api/telegram/incidents preview_tts returns waveform & duration', async () => {
    const req = new NextRequest('http://localhost:3000/api/telegram/incidents', {
      method: 'POST',
      body: JSON.stringify({
        action: 'preview_tts',
        personaSlug: 'sakking',
        text: 'AST Guardrail block active',
      }),
    });

    const res = await IncidentsPOST(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.success).toBe(true);
    expect(data.waveform).toBeDefined();
    expect(data.voiceProfile.name).toBe('SakKing');
  });
});
