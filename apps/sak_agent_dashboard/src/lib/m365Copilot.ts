import { M365CopilotData, M365CopilotPrimitive } from "./types";

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

const AUTH_STEPS: string[] = [
  "Register an Azure AD app with delegated Microsoft Graph permissions for Copilot Retrieval (e.g. `Files.Read.All`, `Sites.Read.All`).",
  "Provision `DeviceCodeCredential(tenant_id=..., client_id=...)` (or any azure-identity delegated credential).",
  "First run prints a device code + verification URL — the signed-in user completes it in a browser, once.",
  "Subsequent calls reuse the cached token; the credential provider refreshes it silently.",
  "Every retrieval call is issued *as the signed-in user*, so results respect that user's SharePoint / OneDrive ACLs automatically.",
];

const CONTRAST = [
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
      "Supported — this is exactly what the SDK is designed for; delegated auth is what the endpoint requires.",
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

export function getM365CopilotData(): M365CopilotData {
  return {
    overview: {
      title: "Microsoft Agents — M365 Copilot (Python)",
      description:
        "Delegated-auth Python client for the M365 Copilot APIs — most notably the Copilot Retrieval API for grounding an agent's answers in SharePoint / OneDrive / external connectors. Complements the app-only teams-copilot-mcp already registered in the MCP Servers tab.",
      repoUrl:
        "https://github.com/microsoft/Agents-M365Copilot/tree/main/python/packages/microsoft_agents_m365copilot",
      pypiUrl: "https://pypi.org/project/microsoft-agents-m365copilot/",
      packageName: "microsoft-agents-m365copilot",
      authModel: "Delegated OAuth (azure-identity)",
    },
    install: "pip install microsoft-agents-m365copilot azure-identity",
    quickstart: `import asyncio
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
    asyncio.run(main())`,
    primitives: PRIMITIVES,
    authSteps: AUTH_STEPS,
    contrastWithTeamsMcp: CONTRAST,
  };
}
