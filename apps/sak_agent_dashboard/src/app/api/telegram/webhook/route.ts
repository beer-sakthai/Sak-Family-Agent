import { NextRequest, NextResponse } from 'next/server';
import {
  getTelegramWebhookStatus,
  processTelegramWebhookUpdate,
  transcribeVoiceAudio,
} from '../../../../lib/telegram/voice_bridge';

export const dynamic = 'force-dynamic';

export async function GET() {
  const status = getTelegramWebhookStatus();
  return NextResponse.json(status);
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Check if simulated voice input
    if (body.type === 'voice_simulation') {
      const transcriptionRes = transcribeVoiceAudio(body.text);
      return NextResponse.json({
        success: true,
        type: 'voice_simulation',
        ...transcriptionRes,
      });
    }

    const result = processTelegramWebhookUpdate(body);
    return NextResponse.json({ success: true, result });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Webhook error' },
      { status: 500 }
    );
  }
}
