'use client';

import React, { useState } from 'react';
import { TelegramWebhookStatus } from '../../lib/types';

interface TelegramWebhookTesterProps {
  status: TelegramWebhookStatus;
  onSimulateVoice: (text: string) => Promise<{ transcription: string; targetPersona: string }>;
  onExecuteSlashCommand: (cmd: string) => Promise<{ response: string }>;
}

export const TelegramWebhookTester: React.FC<TelegramWebhookTesterProps> = ({
  status,
  onSimulateVoice,
  onExecuteSlashCommand,
}) => {
  const [voiceText, setVoiceText] = useState('ช่วยตรวจสอบความปลอดภัยของ AST Sandbox ให้หน่อยครับ');
  const [slashCmd, setSlashCmd] = useState('/status');
  const [voiceResult, setVoiceResult] = useState<{ transcription: string; targetPersona: string } | null>(null);
  const [cmdResult, setCmdResult] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const handleTestVoice = async () => {
    setIsSimulating(true);
    try {
      const res = await onSimulateVoice(voiceText);
      setVoiceResult(res);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleTestCmd = async () => {
    const res = await onExecuteSlashCommand(slashCmd);
    setCmdResult(res.response);
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>⚡</span> Telegram Bot Webhook &amp; Voice Simulator
          </h3>
          <p className="text-xs text-slate-400">
            Simulates inbound Telegram voice notes and slash command dispatching.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-950 px-2.5 py-1 text-[11px] font-semibold text-emerald-400 border border-emerald-800/50">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            {status.botUsername} Connected
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Voice Note Simulation */}
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
          <h4 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
            <span>🎙️</span> Inbound Voice Memo Test
          </h4>
          <p className="mt-1 text-[11px] text-slate-400">
            Simulates an incoming .oga voice note and tests STT intent routing.
          </p>

          <textarea
            rows={2}
            value={voiceText}
            onChange={(e) => setVoiceText(e.target.value)}
            className="mt-3 w-full rounded-md border border-slate-800 bg-slate-900 p-2 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
          />

          <button
            type="button"
            onClick={handleTestVoice}
            disabled={isSimulating}
            className="mt-3 w-full rounded bg-blue-600 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {isSimulating ? 'Processing Audio Memo...' : 'Simulate Inbound Voice Memo'}
          </button>

          {voiceResult && (
            <div className="mt-3 rounded border border-blue-900/60 bg-blue-950/40 p-2.5 text-xs text-slate-300">
              <div><strong className="text-blue-300">STT Transcribed:</strong> {voiceResult.transcription}</div>
              <div className="mt-1">
                <strong className="text-emerald-300">Routed Persona:</strong>{' '}
                <span className="rounded bg-emerald-950 px-2 py-0.5 font-mono text-[10px] text-emerald-300">
                  {voiceResult.targetPersona}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Slash Command Test */}
        <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
          <h4 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
            <span>🤖</span> Bot Slash Command Runner
          </h4>
          <p className="mt-1 text-[11px] text-slate-400">
            Execute inline bot commands (e.g. <code>/status</code>, <code>/eval</code>, <code>/lora_jobs</code>).
          </p>

          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={slashCmd}
              onChange={(e) => setSlashCmd(e.target.value)}
              className="w-full rounded-md border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-mono text-slate-200 focus:border-blue-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={handleTestCmd}
              className="rounded bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700"
            >
              Send
            </button>
          </div>

          {cmdResult && (
            <div className="mt-3 rounded border border-slate-800 bg-slate-900 p-2.5 font-mono text-xs text-slate-200">
              <span className="text-[10px] text-slate-500">Telegram Bot Output:</span>
              <div className="mt-1 text-emerald-300">{cmdResult}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
