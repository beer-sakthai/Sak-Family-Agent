import {
  AudioPcmFrame,
  PersonaVoiceModel,
  VoiceStreamSession,
  DuplexAudioEvent,
} from './types';

/**
 * Gemini 2.0 Flash Multimodal Live Voice & Duplex Audio Streaming Engine.
 * Manages 24kHz PCM audio frames, Voice Activity Detection (VAD),
 * and multi-persona voice profile synthesis.
 */

export class VoiceEngine {
  public static readonly PERSONA_VOICE_MODELS: Record<string, PersonaVoiceModel> = {
    sakking: {
      personaSlug: 'sakking',
      displayName: 'SakKing (Supervisor)',
      geminiVoiceName: 'Fenrir',
      pitch: 0.9,
      speakingRate: 1.0,
      timbreDescription: 'Deep, resonant, authoritative supervisor tone',
      sampleText: 'Fleet status nominal. All multi-agent subtasks verified and aligned with mission goals.',
    },
    saksee: {
      personaSlug: 'saksee',
      displayName: 'SakSee (Security Sentinel)',
      geminiVoiceName: 'Charon',
      pitch: 1.0,
      speakingRate: 1.1,
      timbreDescription: 'Crisp, analytical, sharp zero-tolerance security tone',
      sampleText: 'AST security gate active. Zero path traversal or command injection detected in execution frame.',
    },
    sakjules: {
      personaSlug: 'sakjules',
      displayName: 'SakJules (CI/CD Master)',
      geminiVoiceName: 'Puck',
      pitch: 1.1,
      speakingRate: 1.25,
      timbreDescription: 'Energetic, rapid, precision technical cadence',
      sampleText: 'Vitest mutation test suite 100% green. 12 mutants killed, automated build pipeline deployed.',
    },
    saktan: {
      personaSlug: 'saktan',
      displayName: 'SakTan (Token & Cost Analytics)',
      geminiVoiceName: 'Kore',
      pitch: 0.95,
      speakingRate: 1.05,
      timbreDescription: 'Calm, structured, metric-driven analyst tone',
      sampleText: 'Semantic cache hit ratio at 92.4%. Total token expenditure reduced by 3.84 million tokens.',
    },
    sakthai: {
      personaSlug: 'sakthai',
      displayName: 'SakThai (Core Reasoning & Thai NLP)',
      geminiVoiceName: 'Aoede',
      pitch: 1.0,
      speakingRate: 1.0,
      timbreDescription: 'Warm, natural, bilingual Thai/English executive presence',
      sampleText: 'ระบบพร้อมทำงานร่วมกับทุกโมเดล ประมวลผลลอจิกและคลังความจำระยะยาวเรียบร้อยครับ',
    },
    saknoi: {
      personaSlug: 'saknoi',
      displayName: 'SakNoi (Prompt Designer)',
      geminiVoiceName: 'Puck',
      pitch: 1.2,
      speakingRate: 1.15,
      timbreDescription: 'Creative, expressive, adaptable persona tuner',
      sampleText: 'Prompt template calibrated with structured system constraints and high dynamic range.',
    },
  };

  /**
   * Return all supported persona voice models.
   */
  public static getVoiceModels(): PersonaVoiceModel[] {
    return Object.values(this.PERSONA_VOICE_MODELS);
  }

  /**
   * Generate realistic 24kHz PCM float normalized amplitude frames for audio visualizers.
   */
  public static generateSyntheticAudioFrame(
    frequencyFactor = 1.0,
    amplitude = 0.7,
    voiceActive = true
  ): AudioPcmFrame {
    const sampleCount = 64;
    const amplitudeData: number[] = [];

    for (let i = 0; i < sampleCount; i++) {
      if (!voiceActive) {
        amplitudeData.push((Math.random() * 0.04 - 0.02));
      } else {
        const val =
          Math.sin((i / 8) * frequencyFactor * Math.PI) * amplitude * 0.8 +
          (Math.random() * 0.2 - 0.1) * amplitude;
        amplitudeData.push(Math.max(-1.0, Math.min(1.0, val)));
      }
    }

    return {
      timestampMs: Date.now(),
      sampleRate: 24000,
      channels: 1,
      amplitudeData,
      isVoiceActive: voiceActive,
    };
  }

  /**
   * Simulate a duplex Gemini 2.0 Flash live voice turn with realistic latency and response generation.
   */
  public static async simulateVoiceInteraction(
    personaSlug: string,
    userTranscript: string
  ): Promise<VoiceStreamSession> {
    const startTime = Date.now();
    const voiceModel = this.PERSONA_VOICE_MODELS[personaSlug] || this.PERSONA_VOICE_MODELS.sakjules;

    // Simulate speech-to-speech round-trip latency (~180-220ms on Gemini 2.0 Flash Live)
    await new Promise((r) => setTimeout(r, 120));

    let responseText = voiceModel.sampleText;
    if (userTranscript.toLowerCase().includes('status') || userTranscript.toLowerCase().includes('health')) {
      responseText = `[${voiceModel.displayName}] Fleet operating at 100% capacity. All guardrails and caching layers active.`;
    } else if (userTranscript.toLowerCase().includes('security') || userTranscript.toLowerCase().includes('ast')) {
      responseText = `[${voiceModel.displayName}] AST Security Sentinel confirmed zero unescaped paths or shell injection payloads.`;
    } else if (userTranscript.trim().length > 0) {
      responseText = `[${voiceModel.displayName}] Received: "${userTranscript}". Executing autonomous pipeline tasks now.`;
    }

    const durationMs = Date.now() - startTime + 85;

    return {
      sessionId: `voice-sess-${Date.now()}`,
      personaSlug,
      status: 'SPEAKING',
      totalDurationMs: durationMs,
      totalAudioFrames: 48,
      latencyMs: durationMs,
      vadSensitivity: 0.85,
      transcription: userTranscript || 'Voice prompt detected via real-time microphone stream',
      responseAudioText: responseText,
    };
  }
}
