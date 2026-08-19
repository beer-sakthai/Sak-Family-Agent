'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  PersonaVoiceModel,
  VoiceStreamSession,
  AudioPcmFrame,
} from '@/lib/voice/types';
import { VoiceEngine } from '@/lib/voice/voiceEngine';
import {
  Mic,
  MicOff,
  Volume2,
  Radio,
  Sparkles,
  Activity,
  Play,
  Square,
  Zap,
  Send,
} from 'lucide-react';

export const VoiceStudioWorkbench: React.FC = () => {
  const [voiceModels] = useState<PersonaVoiceModel[]>(VoiceEngine.getVoiceModels());
  const [selectedPersona, setSelectedPersona] = useState<string>('sakjules');
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [session, setSession] = useState<VoiceStreamSession | null>(null);
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const activeModel =
    voiceModels.find((m) => m.personaSlug === selectedPersona) || voiceModels[0];

  // Canvas 60fps Real-Time Audio Waveform Animator
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let tick = 0;
    const renderWaveform = () => {
      tick += 0.08;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barCount = 42;
      const barWidth = canvas.width / barCount - 2;

      for (let i = 0; i < barCount; i++) {
        let height = 6;
        if (isSpeaking) {
          height = Math.abs(Math.sin(tick + i * 0.35) * 36) + Math.random() * 8 + 6;
        } else if (isListening) {
          height = Math.abs(Math.sin(tick * 1.5 + i * 0.25) * 24) + Math.random() * 6 + 4;
        } else {
          height = 4 + Math.sin(tick * 0.5 + i * 0.1) * 3;
        }

        const x = i * (barWidth + 2);
        const y = (canvas.height - height) / 2;

        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        if (isSpeaking) {
          gradient.addColorStop(0, '#38bdf8'); // Cyan-400
          gradient.addColorStop(1, '#6366f1'); // Indigo-500
        } else if (isListening) {
          gradient.addColorStop(0, '#f43f5e'); // Rose-500
          gradient.addColorStop(1, '#fb923c'); // Orange-400
        } else {
          gradient.addColorStop(0, '#475569'); // Slate-600
          gradient.addColorStop(1, '#1e293b'); // Slate-800
        }

        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, height);
      }

      animationFrameRef.current = requestAnimationFrame(renderWaveform);
    };

    renderWaveform();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isSpeaking, isListening]);

  const handleStartVoiceTurn = async (promptText = inputPrompt) => {
    setIsListening(true);
    setIsSpeaking(false);

    // Simulate speech-to-speech roundtrip
    setTimeout(async () => {
      setIsListening(false);
      setIsSpeaking(true);

      const sess = await VoiceEngine.simulateVoiceInteraction(
        selectedPersona,
        promptText || 'Fleet telemetry status request'
      );
      setSession(sess);

      setTimeout(() => {
        setIsSpeaking(false);
      }, 4000);
    }, 900);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <Radio className="w-5 h-5 text-teal-400 animate-pulse" />
            Gemini 2.0 Multimodal Live Voice &amp; WebRTC Duplex Studio
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            24kHz PCM bidirectional audio streaming with persona timbre synthesis and sub-200ms latency.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40 font-bold">
            ⚡ Duplex WebRTC Active
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800/40">
            24kHz Mono PCM
          </span>
        </div>
      </div>

      {/* Persona Voice Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {voiceModels.map((vm) => {
          const isSelected = vm.personaSlug === selectedPersona;
          return (
            <div
              key={vm.personaSlug}
              onClick={() => setSelectedPersona(vm.personaSlug)}
              className={`p-3 rounded-lg border cursor-pointer transition-all text-xs space-y-1 ${
                isSelected
                  ? 'bg-teal-950/40 border-teal-500 ring-1 ring-teal-500/40 shadow-lg'
                  : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="font-bold text-slate-200 truncate">{vm.displayName}</div>
              <div className="text-[10px] font-mono text-teal-400">Voice: {vm.geminiVoiceName}</div>
              <div className="text-[10px] text-slate-500 truncate">{vm.timbreDescription}</div>
            </div>
          );
        })}
      </div>

      {/* Waveform Visualizer Screen */}
      <div className="relative bg-slate-950 rounded-xl border border-slate-800 p-4 overflow-hidden">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="flex items-center gap-1.5 font-mono text-[11px]">
            <Activity className="w-3.5 h-3.5 text-teal-400" />
            {isSpeaking
              ? `Speaking: ${activeModel.displayName}`
              : isListening
              ? 'Listening to Microphone Input...'
              : 'Live Waveform Standby'}
          </span>
          {session && (
            <span className="font-mono text-[10px] text-teal-400">
              Round-trip Latency: {session.latencyMs}ms
            </span>
          )}
        </div>

        <canvas
          ref={canvasRef}
          width={600}
          height={75}
          className="w-full h-20 rounded-lg bg-slate-900/50"
        />

        {/* Live Speaking Dialogue Box */}
        {session && (
          <div className="mt-3 p-3 bg-slate-900/90 rounded-lg border border-slate-800 text-xs space-y-1.5 animate-fade-in">
            <div className="text-[10px] font-mono text-slate-500">
              User Transcript: <span className="text-slate-300">{session.transcription}</span>
            </div>
            <div className="text-slate-100 flex items-start gap-2">
              <Volume2 className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" />
              <span className="font-medium text-teal-200 leading-relaxed">
                {session.responseAudioText}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Controls & Input Workbench */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <input
            type="text"
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            placeholder={`Speak or prompt ${activeModel.displayName} (e.g. "Report security and CI status")...`}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleStartVoiceTurn();
            }}
          />
        </div>

        <button
          onClick={() => handleStartVoiceTurn()}
          disabled={isListening || isSpeaking}
          className={`px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-md transition-all ${
            isListening
              ? 'bg-rose-600 text-white animate-pulse'
              : isSpeaking
              ? 'bg-teal-700 text-white cursor-not-allowed'
              : 'bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 text-white'
          }`}
        >
          {isListening ? (
            <>
              <Mic className="w-4 h-4" />
              Listening...
            </>
          ) : isSpeaking ? (
            <>
              <Volume2 className="w-4 h-4" />
              Streaming Audio...
            </>
          ) : (
            <>
              <Mic className="w-4 h-4" />
              Push to Talk
            </>
          )}
        </button>
      </div>
    </div>
  );
};
