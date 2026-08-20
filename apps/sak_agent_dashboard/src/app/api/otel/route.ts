import { createApiHandler } from "@/lib/api/handler";
import { getOtelData } from "@/lib/otel";

export const GET = createApiHandler("/api/otel", async () => {
  const otel = getOtelData();
  return { otel };
});
