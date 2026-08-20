/**
 * types/m365.ts — Microsoft 365 Copilot types.
 *
 * Moved from the monolithic types.ts. Imported via the `@/lib/types` barrel
 * (`types/index.ts`), which re-exports everything here.
 */

export interface M365CopilotPrimitive {
  id: string;
  name: string;
  summary: string;
  snippet: string;
}

export interface M365CopilotData {
  overview: {
    title: string;
    description: string;
    repoUrl: string;
    pypiUrl: string;
    packageName: string;
    authModel: string;
  };
  install: string;
  quickstart: string;
  primitives: M365CopilotPrimitive[];
  authSteps: string[];
  contrastWithTeamsMcp: Array<{
    dimension: string;
    m365Sdk: string;
    teamsCopilotMcp: string;
  }>;
}

export interface M365CopilotApiResponse {
  success: boolean;
  m365: M365CopilotData;
  error?: string;
}
