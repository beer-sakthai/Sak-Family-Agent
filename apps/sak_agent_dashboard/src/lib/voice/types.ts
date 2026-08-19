/**
 * Domain types for Gemini 2.0 Flash Multimodal Live Voice & Duplex Audio Streaming.
 */

export interface AudioPcmFrame {
  timestampMs: number;
  sampleRate: number; // 24000Hz standard for Gemini Live Audio
  channels: number; // 1 (mono)
  amplitudeData: number[]; // Normalized -1.0 to 1.0
  isVoiceActive: boolean;
}

export interface PersonaVoiceModel {
  personaSlug: string;
  displayName: string;
  geminiVoiceName: 'Puck' | 'Charon' | 'Kore' | 'Fenrir' | 'Aoede';
  pitch: number; // 0.5 to 1.5
  speakingRate: number; // 0.5 to 2.0
  timbreDescription: string;
  sampleText: string;
}

export interface VoiceStreamSession {
  sessionId: string;
  personaSlug: string;
  status: 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';
  totalDurationMs: number;
  totalAudioFrames: number;
  latencyMs: number;
  vadSensitivity: number; // 0.0 to 1.0
  transcription: string;
  responseAudioText: string;
}

export interface DuplexAudioEvent {
  eventId: string;
  timestamp: string;
  type: 'mic_input' | 'vad_detected' | 'gemini_stream' | 'audio_playback';
  personaSlug: string;
  detail: string;
  volumeLevel: number;
}
