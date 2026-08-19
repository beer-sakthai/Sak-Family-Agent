import { describe, it, expect } from 'vitest';
import { VoiceEngine } from '../lib/voice/voiceEngine';

describe('VoiceEngine', () => {
  it('loads voice configurations for all 6 Sak-Family personas', () => {
    const models = VoiceEngine.getVoiceModels();
    expect(models.length).toBe(6);

    const slugs = models.map((m) => m.personaSlug);
    expect(slugs).toContain('sakking');
    expect(slugs).toContain('saksee');
    expect(slugs).toContain('sakjules');
    expect(slugs).toContain('saktan');
    expect(slugs).toContain('sakthai');
    expect(slugs).toContain('saknoi');
  });

  it('generates synthetic 24kHz PCM audio frames', () => {
    const frame = VoiceEngine.generateSyntheticAudioFrame(1.0, 0.8, true);
    expect(frame.sampleRate).toBe(24000);
    expect(frame.channels).toBe(1);
    expect(frame.amplitudeData.length).toBe(64);
    expect(frame.isVoiceActive).toBe(true);
  });

  it('simulates duplex voice interactions with low latency', async () => {
    const session = await VoiceEngine.simulateVoiceInteraction(
      'sakjules',
      'What is the CI/CD test status?'
    );

    expect(session.personaSlug).toBe('sakjules');
    expect(session.status).toBe('SPEAKING');
    expect(session.latencyMs).toBeGreaterThan(0);
    expect(session.responseAudioText.length).toBeGreaterThan(0);
  });
});
