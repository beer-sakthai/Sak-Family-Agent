import { NextResponse } from "next/server";
import { createMutationHandler } from "@/lib/api/handler";
import {
  getTelegramWebhookStatus,
  processTelegramWebhookUpdate,
  transcribeVoiceAudio,
} from "@/lib/telegram/voice_bridge";

export const dynamic = "force-dynamic";

export async function GET() {
  const status = getTelegramWebhookStatus();
  return NextResponse.json(status);
}

export const POST = createMutationHandler("/api/telegram/webhook", async (body) => {
  if (body.type === "voice_simulation") {
    const transcriptionRes = transcribeVoiceAudio(String(body.text ?? ""));
    return { type: "voice_simulation", ...transcriptionRes };
  }

  const result = processTelegramWebhookUpdate(body);
  return { result };
});
