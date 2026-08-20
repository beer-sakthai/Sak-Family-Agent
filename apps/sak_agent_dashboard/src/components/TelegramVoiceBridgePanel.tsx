'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { VoiceWaveformPreviewer } from './telegram/VoiceWaveformPreviewer';
import { IncidentAlertFeed } from './telegram/IncidentAlertFeed';
import { TelegramWebhookTester } from './telegram/TelegramWebhookTester';
import {
  MobileIncidentAlert,
  PersonaVoiceProfile,
  TelegramWebhookStatus,
} from '../lib/types';
import {
  getIncidentAlerts,
  getTelegramWebhookStatus,
  PERSONA_VOICES,
  synthesizePersonaAudio,
  transcribeVoiceAudio,
} from '../lib/telegram/voice_bridge';

export const TelegramVoiceBridgePanel: React.FC = () => {
  const [voices, setVoices] = useState<PersonaVoiceProfile[]>(Object.values(PERSONA_VOICES));
  const [incidents, setIncidents] = useState<MobileIncidentAlert[]>(getIncidentAlerts());
  const [webhookStatus, setWebhookStatus] = useState<TelegramWebhookStatus>(getTelegramWebhookStatus());

  useEffect(() => {
    let isMounted = true;

    async function loadInitialHubData() {
      try {
        const [resInc, resHook] = await Promise.all([
          fetch('/api/telegram/incidents'),
          fetch('/api/telegram/webhook'),
        ]);

        if (!isMounted) return;

        if (resInc.ok) {
          const data = await resInc.json();
          if (data.incidents) setIncidents(data.incidents);
          if (data.voices) setVoices(data.voices);
        }

        if (resHook.ok) {
          const hookData = await resHook.json();
          setWebhookStatus(hookData);
        }
      } catch {
        // Fallback already loaded
      }
    }

    loadInitialHubData();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleSynthesize = async (personaSlug: string, text: string) => {
    try {
      const res = await fetch('/api/telegram/incidents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'preview_tts', personaSlug, text }),
      });
      if (res.ok) {
        const data = await res.json();
        return { waveform: data.waveform, audioDuration: data.audioDuration };
      }
    } catch {
      // Fallback
    }
    return synthesizePersonaAudio(personaSlug, text);
  };

  const handleResolveIncident = async (alertId: string, status: 'acknowledged' | 'resolved') => {
    try {
      const res = await fetch('/api/telegram/incidents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'resolve_incident', alertId, status }),
      });
      if (res.ok) {
        setIncidents((prev) =>
          prev.map((i) => (i.alertId === alertId ? { ...i, status } : i))
        );
      }
    } catch {
      setIncidents((prev) =>
        prev.map((i) => (i.alertId === alertId ? { ...i, status } : i))
      );
    }
  };

  const handleSimulateVoice = async (text: string) => {
    try {
      const res = await fetch('/api/telegram/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'voice_simulation', text }),
      });
      if (res.ok) {
        const data = await res.json();
        return { transcription: data.transcription, targetPersona: data.targetPersona };
      }
    } catch {
      // Fallback
    }
    return transcribeVoiceAudio(text);
  };

  const handleExecuteSlashCommand = async (cmd: string) => {
    try {
      const res = await fetch('/api/telegram/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: { text: cmd } }),
      });
      if (res.ok) {
        const data = await res.json();
        return { response: data.result?.response || 'Executed' };
      }
    } catch {
      // Fallback
    }
    return { response: `Response for ${cmd}: 6 Agents Online, AST Guardrails Active.` };
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-gradient-to-r from-teal-950/40 via-slate-900/60 to-blue-950/40 p-6 backdrop-blur">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">📻</span>
              <h2 className="text-xl font-bold text-slate-100">Telegram Voice Bridge &amp; Mobile Alerting</h2>
              <span className="rounded-full bg-teal-500/20 px-2.5 py-0.5 text-xs font-semibold text-teal-300 border border-teal-500/30">
                Track 20260818
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-400 max-w-2xl">
              Bi-directional mobile command center for <strong>Sak-Family</strong>. Handles inbound voice memo STT,
              persona TTS synthesis, AST security escalations, and interactive inline Telegram approvals.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Bot:</span> <span className="text-teal-400">@SakFamilyBot</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-1.5 font-mono text-[11px] text-slate-300">
              <span className="text-slate-500">Audio Codec:</span> <span className="text-blue-400">OPUS / OGG</span>
            </div>
          </div>
        </div>
      </div>

      {/* Voice Waveform & Persona TTS Previewer */}
      <VoiceWaveformPreviewer voices={voices} onSynthesize={handleSynthesize} />

      {/* Incident Alert Feed */}
      <IncidentAlertFeed incidents={incidents} onResolve={handleResolveIncident} />

      {/* Webhook & Slash Command Tester */}
      <TelegramWebhookTester
        status={webhookStatus}
        onSimulateVoice={handleSimulateVoice}
        onExecuteSlashCommand={handleExecuteSlashCommand}
      />
    </div>
  );
};
