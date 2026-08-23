import {
  MobileIncidentAlert,
  PersonaVoiceProfile,
  TelegramVoiceMessage,
  TelegramWebhookStatus,
} from '../types';

export const PERSONA_VOICES: Record<string, PersonaVoiceProfile> = {
  sakthai: {
    personaSlug: 'sakthai',
    name: 'SakThai',
    voiceId: 'th-TH-Standard-A',
    pitch: 1.0,
    speed: 1.05,
    toneDescription: 'Authoritative, calm, balanced pace. High-level leadership timbre.',
    samplePhrase: 'ระบบ Sak-Family พร้อมทำงาน ตรวจสอบสถาปัตยกรรมและกระบวนการทำงานทั้งหมดแล้ว',
  },
  sakking: {
    personaSlug: 'sakking',
    name: 'SakKing',
    voiceId: 'th-TH-Standard-B',
    pitch: 0.95,
    speed: 1.15,
    toneDescription: 'Sharp, rapid, vigilance-focused cadence for security and AST monitoring.',
    samplePhrase: 'ตรวจพบการทำงานที่ไม่ปลอดภัยในระบบ AST Guardrail กำลังทำการบล็อกคำสั่งดังกล่าว',
  },
  saksee: {
    personaSlug: 'saksee',
    name: 'SakSee',
    voiceId: 'th-TH-Standard-C',
    pitch: 1.1,
    speed: 1.0,
    toneDescription: 'Expressive, dynamic pitch for UI/UX critiques and visual design tokens.',
    samplePhrase: 'ออกแบบส่วนติดต่อผู้ใช้เสร็จเรียบร้อย ตรวจสอบความเข้ากันได้ของการแสดงผลและสีสันแล้ว',
  },
  sakjules: {
    personaSlug: 'sakjules',
    name: 'SakJules',
    voiceId: 'en-US-Journey-D',
    pitch: 1.0,
    speed: 1.1,
    toneDescription: 'Rhythmic, precise engineer cadence for CI/CD pipelines and automated testing.',
    samplePhrase: 'All test suites verified with 100% pass rate. Automated build and container ready for deployment.',
  },
  saksit: {
    personaSlug: 'saksit',
    name: 'SakSit',
    voiceId: 'th-TH-Standard-E',
    pitch: 1.0,
    speed: 0.95,
    toneDescription: 'Structured, articulate cadence for technical documentation and API specifications.',
    samplePhrase: 'เอกสารข้อกำหนดทางเทคนิคและคู่มือการใช้งานถูกจัดทำและปรับปรุงเป็นเวอร์ชันล่าสุดแล้ว',
  },
  saktan: {
    personaSlug: 'saktan',
    name: 'SakTan',
    voiceId: 'th-TH-Standard-F',
    pitch: 1.05,
    speed: 1.2,
    toneDescription: 'Energetic, fast-paced tone for daily operations and scratchpad sandboxes.',
    samplePhrase: 'เริ่มการทดสอบในแซนด์บ็อกซ์ท้องถิ่น รันงานอัตโนมัติสำเร็จเรียบร้อย',
  },
};

let inMemoryIncidents: MobileIncidentAlert[] = [
  {
    alertId: 'inc_p0_ast_block_1',
    severity: 'P0_CRITICAL',
    source: 'AST Guardrail Sandbox',
    title: 'Destructive Shell Execution Intercepted',
    details: 'Blocked attempt to run "rm -rf /" inside host root context by unverified workflow worker.',
    suggestedAction: 'Quarantine worker and inspect AST call trace.',
    status: 'active',
    requiresApproval: true,
    createdAt: new Date(Date.now() - 1200000).toISOString(),
  },
  {
    alertId: 'inc_p1_lora_loss_spike_2',
    severity: 'P1_HIGH',
    source: 'LoRA Training Engine',
    title: 'Loss Divergence Detected in sakthai-7b',
    details: 'Eval loss spiked from 0.85 to 4.20 during Epoch 2 Step 120.',
    suggestedAction: 'Reduce learning rate to 5e-5 and rollback checkpoint.',
    status: 'acknowledged',
    requiresApproval: false,
    createdAt: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    alertId: 'inc_p2_latency_probe_3',
    severity: 'P2_MEDIUM',
    source: 'Cloud Run Prober',
    title: 'Agent Dispatch Latency > 1500ms',
    details: 'Cold start latency reached 1850ms in region us-central1.',
    suggestedAction: 'Increase minInstances from 1 to 2.',
    status: 'resolved',
    requiresApproval: false,
    createdAt: new Date(Date.now() - 7200000).toISOString(),
  },
];

/**
 * Transcribes incoming voice audio memo.
 */
export function transcribeVoiceAudio(simulatedText?: string, duration = 4.5): {
  transcription: string;
  targetPersona: string;
} {
  const text = simulatedText || 'ช่วยตรวจสอบสถานะของโมเดล sakthai ล่าสุดให้หน่อยครับ';
  let target = 'sakthai';

  if (text.includes('ความปลอดภัย') || text.includes('security') || text.includes('ast')) {
    target = 'sakking';
  } else if (text.includes('ui') || text.includes('design') || text.includes('หน้าจอ')) {
    target = 'saksee';
  } else if (text.includes('test') || text.includes('ci') || text.includes('deploy') || text.includes('jules')) {
    target = 'sakjules';
  } else if (text.includes('doc') || text.includes('เอกสาร') || text.includes('api')) {
    target = 'saksit';
  } else if (text.includes('tan') || text.includes('sandbox') || text.includes('daily')) {
    target = 'saktan';
  }

  return {
    transcription: text,
    targetPersona: target,
  };
}

/**
 * Synthesizes persona response audio.
 */
export function synthesizePersonaAudio(
  personaSlug: string,
  text: string
): {
  voiceProfile: PersonaVoiceProfile;
  audioDuration: number;
  waveform: number[];
  audioDataUrl: string;
} {
  const voice = PERSONA_VOICES[personaSlug] || PERSONA_VOICES.sakthai;
  const wordCount = text.split(/\s+/).length;
  const audioDuration = Math.max(1.5, Number((wordCount * 0.4).toFixed(1)));

  // Generate synthetic waveform bars (0 to 100)
  const waveform = Array.from({ length: 24 }, (_, i) =>
    Math.round(20 + Math.abs(Math.sin(i * 0.5) * 60) + (i % 3) * 6)
  );

  return {
    voiceProfile: voice,
    audioDuration,
    waveform,
    audioDataUrl: `data:audio/ogg;base64,GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQRChYECGFOAZwH/////////FUmpZpkq17GDD0JATYCGQ2hyb21lV0GGQ2hyb21lFlSua8+56+97mgZuT3B1c2GFQoWBAhhTgGcB/////////4VSoA==`,
  };
}

/**
 * Returns all incident alerts.
 */
export function getIncidentAlerts(): MobileIncidentAlert[] {
  return [...inMemoryIncidents];
}

/**
 * Creates a new incident alert.
 */
export function createIncidentAlert(alert: Partial<MobileIncidentAlert>): MobileIncidentAlert {
  const newAlert: MobileIncidentAlert = {
    alertId: alert.alertId || `inc_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
    severity: alert.severity || 'P1_HIGH',
    source: alert.source || 'AST Sandbox Engine',
    title: alert.title || 'Security Intercept Triggered',
    details: alert.details || 'Blocked unverified command pattern.',
    suggestedAction: alert.suggestedAction || 'Review trace in dashboard.',
    status: 'active',
    requiresApproval: alert.requiresApproval ?? true,
    createdAt: new Date().toISOString(),
  };

  inMemoryIncidents = [newAlert, ...inMemoryIncidents];
  return newAlert;
}

/**
 * Resolves or acknowledges an incident alert.
 */
export function resolveIncidentAlert(
  alertId: string,
  status: 'acknowledged' | 'resolved'
): MobileIncidentAlert | null {
  const item = inMemoryIncidents.find((i) => i.alertId === alertId);
  if (!item) return null;
  item.status = status;
  return item;
}

/**
 * Returns Telegram webhook status.
 */
export function getTelegramWebhookStatus(): TelegramWebhookStatus {
  return {
    connected: true,
    botUsername: '@SakFamilyBot',
    webhookUrl: 'https://sakthai.enterprise.internal/api/telegram/webhook',
    pendingUpdates: 0,
    lastUpdateTimestamp: new Date().toISOString(),
  };
}

/**
 * Processes incoming Telegram webhook payloads.
 */
export function processTelegramWebhookUpdate(update: any): {
  actionTaken: string;
  response: string;
  voiceUrl?: string;
} {
  if (update?.callback_query) {
    const data = update.callback_query.data;
    if (data.startsWith('approve_')) {
      return { actionTaken: 'approval_granted', response: '✅ Approved action executed safely.' };
    }
    if (data.startsWith('quarantine_')) {
      return { actionTaken: 'quarantined', response: '🛑 Worker quarantined and execution terminated.' };
    }
  }

  const messageText = update?.message?.text || '';
  if (messageText.startsWith('/status')) {
    return {
      actionTaken: 'status_report',
      response: '📊 Sak-Family Fleet Status: 6 Agents Online, AST Guardrails Active, All CI/CD checks passing.',
    };
  }

  return {
    actionTaken: 'message_processed',
    response: `Processed input for Sak-Family agents: ${messageText}`,
  };
}
