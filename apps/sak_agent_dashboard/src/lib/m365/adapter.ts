import { M365CopilotData, M365CopilotPrimitive } from "../types";
import { AuthStrategy, DEFAULT_AUTH_STRATEGY } from "./authStrategy";

/**
 * M365 Copilot Adapter.
 *
 * The dashboard used to couple the M365 tab directly to a single hardcoded
 * data module (`m365Copilot.ts`). `M365CopilotAdapter` is the seam: the panel
 * and route depend on this interface, not on any concrete implementation, so a
 * future live integration can be swapped in without touching the UI.
 *
 * Two adapters are provided:
 * - `StaticDocsAdapter` — the current behaviour: documented SDK surface, no
 *   live retrieval call. This is the default.
 * - `PythonSdkAdapter` — a documented future adapter that would shell out to
 *   the vendored `microsoft_agents_m365copilot` Python SDK (v1.8.0) through a
 *   bridge route. It is intentionally not wired up: the repo's own research
 *   records that the Copilot Retrieval API is blocked for personal Microsoft
 *   accounts, so a live call would be a dead end here.
 */

export interface M365CopilotAdapter {
  readonly id: string;
  readonly name: string;
  getOverview(): M365CopilotData["overview"];
  getInstall(): string;
  getQuickstart(): string;
  getPrimitives(): M365CopilotPrimitive[];
  getAuthStrategy(): AuthStrategy;
  getContrastWithTeamsMcp(): M365CopilotData["contrastWithTeamsMcp"];
  /** Assemble the full data shape the panel and route consume. */
  getData(): M365CopilotData;
}

const PRIMITIVES: M365CopilotPrimitive[] = [
  {
    id: "client",
    name: "AgentsM365CopilotServiceClient",
    summary:
      "Root client for the M365 Copilot APIs. Wired with a credential provider (typically DeviceCodeCredential for delegated auth) at construction time; all sub-resources hang off it.",
    snippet: `from azure.identity import DeviceCodeCredential
from microsoft_agents_m365copilot import AgentsM365CopilotServiceClient

credential = DeviceCodeCredential(
    tenant_id="<tenant-id>",
    client_id="<client-id>",
)

client = AgentsM365CopilotServiceClient(credential)`,
  },
  {
    id: "retrieval-request",
    name: "RetrievalPostRequestBody",
    summary:
      "Typed body for the Copilot Retrieval API — pick a data source and (optionally) a filter, run the query, get back grounding hits.",
    snippet: `from microsoft_agents_m365copilot.copilot_retrieval import (
    RetrievalPostRequestBody,
    RetrievalDataSource,
)

body = RetrievalPostRequestBody(
    query_string="Q1 launch plan",
    data_source=RetrievalDataSource.SharePoint,
    maximum_number_of_results=10,
)

result = await client.copilot.retrieval.post(body=body)
for hit in result.retrieval_hits:
    print(hit.web_url, hit.extracts[0].text[:200])`,
  },
  {
    id: "data-source",
    name: "RetrievalDataSource",
    summary:
      "Enum naming the connected store to query — SharePoint, OneDriveBusiness, ExternalItem. One data source per call; interleaving isn't supported.",
    snippet: `from microsoft_agents_m365copilot.copilot_retrieval import RetrievalDataSource

# Choose one per call:
RetrievalDataSource.SharePoint
RetrievalDataSource.OneDriveBusiness
RetrievalDataSource.ExternalItem   # requires a Copilot connector connection id`,
  },
  {
    id: "hit-shape",
    name: "Retrieval hits",
    summary:
      "The response payload: each hit carries a web_url back to the source item and one or more extracts with the grounding text.",
    snippet: `for hit in result.retrieval_hits:
    print(f"[source] {hit.web_url}")
    for extract in hit.extracts:
        print(extract.text)`,
  },
];

const CONTRAST: M365CopilotData["contrastWithTeamsMcp"] = [
  {
    dimension: "Auth model",
    m365Sdk: "Delegated (signed-in-user) OAuth via azure-identity.",
    teamsCopilotMcp:
      "App-only (client-credentials) via MSAL — tenant-wide, no per-user scoping.",
  },
  {
    dimension: "Transport",
    m365Sdk:
      "Direct HTTPS to Graph via microsoft-agents-m365copilot; no MCP layer.",
    teamsCopilotMcp:
      "stdio MCP server that an agent host launches as a subprocess.",
  },
  {
    dimension: "Copilot Retrieval",
    m365Sdk:
      "Supported on a work/school tenant — delegated auth is what the endpoint requires. NOT usable on a personal Microsoft account under any auth mode (see the account-type blocker below).",
    teamsCopilotMcp:
      "Not usable — the endpoint doesn't accept application permissions, so the tool raises NotImplementedError.",
  },
  {
    dimension: "First-use ceremony",
    m365Sdk:
      "One interactive device-code sign-in per user, then cached.",
    teamsCopilotMcp:
      "No interactive sign-in — three env vars (`MSGRAPH_TENANT_ID`, `_CLIENT_ID`, `_CLIENT_SECRET`) and it runs.",
  },
  {
    dimension: "Sits well with",
    m365Sdk:
      "User-facing Copilot integrations, personal assistants, per-user knowledge grounding.",
    teamsCopilotMcp:
      "Background/batch agents that operate tenant-wide (channel post automation, calendar reads for many users).",
  },
];

/**
 * The default adapter: serves the documented SDK surface with no live
 * retrieval call. This is the current, shipped behaviour.
 */
export class StaticDocsAdapter implements M365CopilotAdapter {
  readonly id = "static-docs";
  readonly name = "Static SDK documentation";

  constructor(private readonly authStrategy: AuthStrategy = DEFAULT_AUTH_STRATEGY) {}

  getOverview(): M365CopilotData["overview"] {
    return {
      title: "Microsoft Agents — M365 Copilot (Python)",
      description:
        "Delegated-auth Python client for the M365 Copilot APIs — most notably the Copilot Retrieval API for grounding an agent's answers in SharePoint / OneDrive / external connectors. Complements the app-only teams-copilot-mcp already registered in the MCP Servers tab.",
      repoUrl:
        "https://github.com/microsoft/Agents-M365Copilot/tree/main/python/packages/microsoft_agents_m365copilot",
      pypiUrl: "https://pypi.org/project/microsoft-agents-m365copilot/",
      packageName: "microsoft-agents-m365copilot",
      authModel: this.authStrategy.authModel,
    };
  }

  getInstall(): string {
    return "pip install microsoft-agents-m365copilot azure-identity";
  }

  getQuickstart(): string {
    return `import asyncio
from azure.identity import DeviceCodeCredential
from microsoft_agents_m365copilot import AgentsM365CopilotServiceClient
from microsoft_agents_m365copilot.copilot_retrieval import (
    RetrievalPostRequestBody,
    RetrievalDataSource,
)

credential = DeviceCodeCredential(
    tenant_id="<tenant-id>",
    client_id="<client-id>",
)
client = AgentsM365CopilotServiceClient(credential)

async def main() -> None:
    body = RetrievalPostRequestBody(
        query_string="Q1 launch plan",
        data_source=RetrievalDataSource.SharePoint,
        maximum_number_of_results=5,
    )
    result = await client.copilot.retrieval.post(body=body)
    for hit in result.retrieval_hits:
        print(hit.web_url)

if __name__ == "__main__":
    asyncio.run(main())`;
  }

  getPrimitives(): M365CopilotPrimitive[] {
    return PRIMITIVES;
  }

  getAuthStrategy(): AuthStrategy {
    return this.authStrategy;
  }

  getContrastWithTeamsMcp(): M365CopilotData["contrastWithTeamsMcp"] {
    return CONTRAST;
  }

  getData(): M365CopilotData {
    return {
      overview: this.getOverview(),
      install: this.getInstall(),
      quickstart: this.getQuickstart(),
      primitives: this.getPrimitives(),
      authSteps: this.authStrategy.steps,
      contrastWithTeamsMcp: this.getContrastWithTeamsMcp(),
    };
  }
}

/**
 * A future live adapter that would shell out to the vendored
 * `microsoft_agents_m365copilot` Python SDK (v1.8.0) through a bridge route.
 *
 * Documented, not wired up: the Copilot Retrieval API is blocked for personal
 * Microsoft accounts (see `AccountTypeGate`), so a live call would be a dead
 * end in this environment. When a work/school tenant is available, implement
 * `getData()` to invoke the bridge and return the same `M365CopilotData` shape.
 */
export class PythonSdkAdapter implements M365CopilotAdapter {
  readonly id = "python-sdk";
  readonly name = "Live Python SDK (future)";

  constructor(private readonly authStrategy: AuthStrategy = DEFAULT_AUTH_STRATEGY) {}

  getOverview(): M365CopilotData["overview"] {
    return {
      title: "Microsoft Agents — M365 Copilot (Python, live)",
      description:
        "Live integration that shells out to the vendored microsoft_agents_m365copilot SDK. Not yet wired up — see the account-type gate.",
      repoUrl:
        "https://github.com/microsoft/Agents-M365Copilot/tree/main/python/packages/microsoft_agents_m365copilot",
      pypiUrl: "https://pypi.org/project/microsoft-agents-m365copilot/",
      packageName: "microsoft-agents-m365copilot",
      authModel: this.authStrategy.authModel,
    };
  }

  getInstall(): string {
    return "pip install microsoft-agents-m365copilot azure-identity";
  }

  getQuickstart(): string {
    return "# Live retrieval is not wired up in this environment.";
  }

  getPrimitives(): M365CopilotPrimitive[] {
    return PRIMITIVES;
  }

  getAuthStrategy(): AuthStrategy {
    return this.authStrategy;
  }

  getContrastWithTeamsMcp(): M365CopilotData["contrastWithTeamsMcp"] {
    return CONTRAST;
  }

  getData(): M365CopilotData {
    return {
      overview: this.getOverview(),
      install: this.getInstall(),
      quickstart: this.getQuickstart(),
      primitives: this.getPrimitives(),
      authSteps: this.authStrategy.steps,
      contrastWithTeamsMcp: this.getContrastWithTeamsMcp(),
    };
  }
}

/** The adapter the M365 tab and route use by default. */
export const DEFAULT_M365_ADAPTER: M365CopilotAdapter = new StaticDocsAdapter();
