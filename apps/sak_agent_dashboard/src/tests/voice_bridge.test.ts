import { describe, it, expect } from 'vitest';
import {
  PERSONA_VOICES,
  transcribeVoiceAudio,
  synthesizePersonaAudio,
  getIncidentAlerts,
  createIncidentAlert,
  resolveIncidentAlert,
  processTelegramWebhookUpdate,
} from '../lib/telegram/voice_bridge';

describe('Telegram Voice Bridge Library', () => {
  it('contains voice profiles for all 6 personas', () => {
    const keys = Object.keys(PERSONA_VOICES);
    expect(keys).toEqual(expect.arrayContaining(['sakthai', 'sakking', 'saksee', 'sakjules', 'saksit', 'saktan']));
  });

  it('transcribes simulated voice audio and routes to appropriate persona', () => {
    const resSec = transcribeVoiceAudio('ช่วยตรวจสอบความปลอดภัยของ AST หน่อยครับ');
    expect(resSec.targetPersona).toBe('sakking');

    const resCi = transcribeVoiceAudio('Run CI deployment and test checks');
    expect(resCi.targetPersona).toBe('sakjules');
  });

  it('synthesizes persona audio with custom waveform and duration', () => {
    const synth = synthesizePersonaAudio('sakthai', 'ระบบสถาปัตยกรรมทำงานปกติ');
    expect(synth.voiceProfile.name).toBe('SakThai');
    expect(synth.audioDuration).toBeGreaterThan(0);
    expect(synth.waveform.length).toBe(24);
  });

  it('manages incident lifecycle (create -> list -> resolve)', () => {
    const initialCount = getIncidentAlerts().length;
    const newAlert = createIncidentAlert({
      severity: 'P0_CRITICAL',
      title: 'Test Incident',
      details: 'Test details for verification',
    });

    expect(newAlert.alertId).toBeDefined();
    expect(newAlert.status).toBe('active');
    expect(getIncidentAlerts().length).toBe(initialCount + 1);

    const resolved = resolveIncidentAlert(newAlert.alertId, 'resolved');
    expect(resolved?.status).toBe('resolved');
  });

  it('processes webhook updates and callback queries', () => {
    const statusRes = processTelegramWebhookUpdate({ message: { text: '/status' } });
    expect(statusRes.actionTaken).toBe('status_report');
    expect(statusRes.response).toContain('Sak-Family Fleet Status');

    const approveRes = processTelegramWebhookUpdate({ callback_query: { data: 'approve_cmd_123' } });
    expect(approveRes.actionTaken).toBe('approval_granted');
  });
});
