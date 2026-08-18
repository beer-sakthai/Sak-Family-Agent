import { NextRequest, NextResponse } from 'next/server';
import {
  createIncidentAlert,
  getIncidentAlerts,
  PERSONA_VOICES,
  resolveIncidentAlert,
  synthesizePersonaAudio,
} from '../../../../lib/telegram/voice_bridge';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const incidents = getIncidentAlerts();
    return NextResponse.json({
      incidents,
      voices: Object.values(PERSONA_VOICES),
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to retrieve incidents' },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const action = body.action || 'preview_tts';

    if (action === 'preview_tts') {
      const result = synthesizePersonaAudio(
        body.personaSlug || 'sakthai',
        body.text || 'ทดสอบระบบเสียงสังเคราะห์ของ Sak-Family'
      );
      return NextResponse.json({ success: true, ...result });
    }

    if (action === 'create_incident') {
      const alert = createIncidentAlert(body.alert || {});
      return NextResponse.json({ success: true, alert }, { status: 201 });
    }

    if (action === 'resolve_incident') {
      const updated = resolveIncidentAlert(body.alertId, body.status || 'resolved');
      return NextResponse.json({ success: true, alert: updated });
    }

    return NextResponse.json({ error: `Unknown action: ${action}` }, { status: 400 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Incident API error' },
      { status: 500 }
    );
  }
}
