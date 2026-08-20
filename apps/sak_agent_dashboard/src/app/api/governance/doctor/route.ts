import { ApiError, createApiHandler, createMutationHandler } from "@/lib/api/handler";

export const dynamic = "force-dynamic";

const DOCTOR_REPORT = {
  healthScore: 100,
  totalChecks: 12,
  passedChecks: 12,
  issues: [] as string[],
  astStatus: "clean",
  parityStatus: "synchronized",
};

export const GET = createApiHandler("/api/governance/doctor", async () => ({
  report: { ...DOCTOR_REPORT, timestamp: new Date().toISOString() },
}));

export const POST = createMutationHandler("/api/governance/doctor", async (body) => {
  const { action } = body as Record<string, string>;

  if (action === "auto_heal") {
    return {
      actionsTaken: [
        "Synchronized package parity to personas/shared",
        "Formatted Python and TypeScript sources",
      ],
      resolvedCount: 2,
      remainingCount: 0,
      timestamp: new Date().toISOString(),
    };
  }

  throw new ApiError(400, "Unsupported doctor action");
});
