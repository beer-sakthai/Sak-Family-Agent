import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { VoiceWaveformPreviewer } from '../components/telegram/VoiceWaveformPreviewer';
import { IncidentAlertFeed } from '../components/telegram/IncidentAlertFeed';
import { TelegramWebhookTester } from '../components/telegram/TelegramWebhookTester';
import { TelegramVoiceBridgePanel } from '../components/TelegramVoiceBridgePanel';
import {
  PERSONA_VOICES,
  getIncidentAlerts,
  getTelegramWebhookStatus,
} from '../lib/telegram/voice_bridge';

describe('VoiceWaveformPreviewer Component', () => {
  it('renders personas and triggers synthesis callback on click', async () => {
    const onSynth = vi.fn().mockResolvedValue({ waveform: [50, 60, 70], audioDuration: 2.0 });
    render(<VoiceWaveformPreviewer voices={Object.values(PERSONA_VOICES)} onSynthesize={onSynth} />);

    expect(screen.getByText(/Persona Voice Synthesizer & Waveform Monitor/i)).toBeDefined();
    expect(screen.getByText('SakThai')).toBeDefined();
    expect(screen.getByText('SakKing')).toBeDefined();

    const synthBtn = screen.getByRole('button', { name: /Synthesize & Preview Voice/i });
    fireEvent.click(synthBtn);
    expect(onSynth).toHaveBeenCalled();
  });
});

describe('IncidentAlertFeed Component', () => {
  it('renders incidents and triggers resolve callback', () => {
    const incidents = getIncidentAlerts();
    const onResolve = vi.fn().mockResolvedValue(undefined);

    render(<IncidentAlertFeed incidents={incidents} onResolve={onResolve} />);

    expect(screen.getByText(/Real-Time Mobile Incident Alert Feed/i)).toBeDefined();
    expect(screen.getByText(/Destructive Shell Execution Intercepted/i)).toBeDefined();

    const resolveBtns = screen.getAllByRole('button', { name: /Mark Resolved/i });
    if (resolveBtns.length > 0) {
      fireEvent.click(resolveBtns[0]);
      expect(onResolve).toHaveBeenCalled();
    }
  });
});

describe('TelegramWebhookTester Component', () => {
  it('runs voice simulation and slash command handlers', async () => {
    const status = getTelegramWebhookStatus();
    const onVoice = vi.fn().mockResolvedValue({ transcription: 'Test text', targetPersona: 'sakthai' });
    const onCmd = vi.fn().mockResolvedValue({ response: 'Status OK' });

    render(
      <TelegramWebhookTester
        status={status}
        onSimulateVoice={onVoice}
        onExecuteSlashCommand={onCmd}
      />
    );

    expect(screen.getByText(/Telegram Bot Webhook & Voice Simulator/i)).toBeDefined();
    expect(screen.getByText(/@SakFamilyBot Connected/i)).toBeDefined();

    const voiceBtn = screen.getByRole('button', { name: /Simulate Inbound Voice Memo/i });
    fireEvent.click(voiceBtn);
    expect(onVoice).toHaveBeenCalled();
  });
});

describe('TelegramVoiceBridgePanel Component', () => {
  it('renders the complete Telegram Voice Bridge panel', () => {
    render(<TelegramVoiceBridgePanel />);
    expect(screen.getByText(/Telegram Voice Bridge & Mobile Alerting/i)).toBeDefined();
    expect(screen.getByText(/Track 20260818/i)).toBeDefined();
    expect(screen.getAllByText(/@SakFamilyBot/i).length).toBeGreaterThanOrEqual(1);
  });
});
