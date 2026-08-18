'use client';

import React, { useState } from 'react';
import { PersonaVoiceProfile } from '../../lib/types';

interface VoiceWaveformPreviewerProps {
  voices: PersonaVoiceProfile[];
  onSynthesize: (personaSlug: string, text: string) => Promise<{ waveform: number[]; audioDuration: number }>;
}

export const VoiceWaveformPreviewer: React.FC<VoiceWaveformPreviewerProps> = ({
  voices,
  onSynthesize,
}) => {
  const [selectedPersona, setSelectedPersona] = useState<string>(voices[0]?.personaSlug || 'sakthai');
  const [customText, setCustomText] = useState<string>(voices[0]?.samplePhrase || '');
  const [waveform, setWaveform] = useState<number[]>([30, 45, 60, 80, 65, 40, 50, 75, 90, 60, 40, 25, 35, 55, 70, 85, 95, 60, 40, 30, 50, 70, 60, 30]);
  const [duration, setDuration] = useState<number>(3.5);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const currentVoice = voices.find((v) => v.personaSlug === selectedPersona) || voices[0];

  const handleSelectPersona = (slug: string) => {
    setSelectedPersona(slug);
    const v = voices.find((item) => item.personaSlug === slug);
    if (v) {
      setCustomText(v.samplePhrase);
    }
  };

  const handlePlaySynthesis = async () => {
    setIsLoading(true);
    try {
      const res = await onSynthesize(selectedPersona, customText);
      if (res.waveform) setWaveform(res.waveform);
      if (res.audioDuration) setDuration(res.audioDuration);

      setIsPlaying(true);
      setTimeout(() => setIsPlaying(false), res.audioDuration * 1000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>🎙️</span> Persona Voice Synthesizer &amp; Waveform Monitor
          </h3>
          <p className="text-xs text-slate-400">
            Real-time TTS voice timbre tuner for all 6 Sak-Family personas with custom cadence and pitch profiles.
          </p>
        </div>

        <span className="rounded bg-indigo-950 px-2 py-0.5 text-[10px] font-mono text-indigo-300 border border-indigo-800/50">
          OPUS 24kHz
        </span>
      </div>

      {/* Persona Selector Tabs */}
      <div className="mt-4 flex flex-wrap gap-2">
        {voices.map((v) => (
          <button
            key={v.personaSlug}
            type="button"
            onClick={() => handleSelectPersona(v.personaSlug)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
              selectedPersona === v.personaSlug
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            {v.name}
          </button>
        ))}
      </div>

      {currentVoice && (
        <div className="mt-4 space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs">
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2.5">
              <span className="text-[10px] text-slate-500 uppercase">Voice ID</span>
              <div className="font-mono text-blue-300 font-bold">{currentVoice.voiceId}</div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2.5">
              <span className="text-[10px] text-slate-500 uppercase">Cadence / Speed</span>
              <div className="font-mono text-emerald-300 font-bold">{currentVoice.speed}x</div>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2.5">
              <span className="text-[10px] text-slate-500 uppercase">Tone Profile</span>
              <div className="truncate text-slate-300" title={currentVoice.toneDescription}>
                {currentVoice.toneDescription}
              </div>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-medium text-slate-300">Synthesis Input Text</label>
            <textarea
              rows={2}
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
            />
          </div>

          {/* Waveform Visualization Box */}
          <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
              <span className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${isPlaying ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'}`} />
                <span>{isPlaying ? 'Playing Audio...' : 'Audio Stream Ready'}</span>
              </span>
              <span className="font-mono text-[11px]">{duration}s Duration</span>
            </div>

            <div className="flex h-14 items-end justify-between gap-1 px-2">
              {waveform.map((bar, idx) => (
                <div
                  key={idx}
                  className={`w-full rounded-t transition-all duration-300 ${
                    isPlaying
                      ? 'bg-gradient-to-t from-blue-500 to-indigo-400 animate-pulse'
                      : 'bg-slate-700 hover:bg-slate-600'
                  }`}
                  style={{ height: `${bar}%` }}
                />
              ))}
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              onClick={handlePlaySynthesis}
              disabled={isLoading || isPlaying}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
            >
              <span>{isPlaying ? '🔊 Playing...' : '▶ Synthesize & Preview Voice'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
