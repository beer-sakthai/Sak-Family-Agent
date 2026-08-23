import {
  GatewayControl,
  GatewayData,
  GatewayMcpService,
  GatewayMode,
  GatewayStep,
} from "./types";

const CONTROLS: GatewayControl[] = [
  {
    id: "iap-request-authz",
    name: "IAP REQUEST_AUTHZ",
    kind: "authz",
    summary:
      "Per-tool IAM enforced at the gateway. Each MCP server gets its own runtime service account, and the agent is granted egress to only the specific servers it needs — so a compromised prompt cannot reach a tool the agent was never authorized for.",
    enforcedAt: "Gateway, before the request reaches Cloud Run",
  },
  {
    id: "agent-identity",
    name: "Agent Identity",
    kind: "identity",
    summary:
      "The deployed agent carries a first-class identity rather than borrowing the service's credentials. That identity is what per-tool IAM bindings are written against, which is what makes per-tool authorization meaningful in the first place.",
    enforcedAt: "Agent Runtime, at deploy time (--enable-agent-identity)",
  },
  {
    id: "model-armor",
    name: "Model Armor CONTENT_AUTHZ",
    kind: "content",
    summary:
      "A service extension that screens both prompts and responses — prompt injection, jailbreak attempts, and sensitive-data egress — with DLP integration. Runs as a gateway extension, so it applies uniformly regardless of which tool the agent is calling.",
    enforcedAt: "Gateway, on both request and response paths",
  },
  {
    id: "agent-registry",
    name: "Agent Registry",
    kind: "discovery",
    summary:
      "Tool URLs are discovered at runtime instead of being baked into the agent image. Moving a service, or switching from public to private networking, becomes a registry change rather than a rebuild-and-redeploy.",
    enforcedAt: "Runtime, on every tool resolution",
  },
  {
    id: "cloud-trace",
    name: "Cloud Trace",
    kind: "observability",
    summary:
      "End-to-end execution is observable across the agent, the gateway, and every MCP hop — the distributed-tracing counterpart to what the Observability tab describes for the local sakthai loop.",
    enforcedAt: "Ambient, across all hops",
  },
];

const MODES: GatewayMode[] = [
  {
    mode: "Default (public)",
    cloudRunIngress: "all",
    registryUrls: "*.run.app",
    extraRequirements: "None",
    secure: false,
  },
  {
    mode: "Secure (private)",
    cloudRunIngress: "internal-and-cloud-load-balancing",
    registryUrls: "<svc>.<your-domain> via internal ALB",
    extraRequirements: "A public DNS zone you own + a Google-managed cert",
    secure: true,
  },
];

const MCP_SERVICES: GatewayMcpService[] = [
  {
    name: "legacy-dms",
    purpose: "MCP legacy document-management service.",
  },
  {
    name: "corporate-email",
    purpose: "MCP corporate email service.",
  },
  {
    name: "income-verification-api",
    purpose: "MCP income verification API.",
  },
];

const STEPS: GatewayStep[] = [
  {
    order: 1,
    title: "Bootstrap APIs",
    command: `gcloud services enable \\
  compute.googleapis.com serviceusage.googleapis.com \\
  cloudresourcemanager.googleapis.com iam.googleapis.com \\
  storage.googleapis.com dns.googleapis.com`,
  },
  {
    order: 2,
    title: "Create Terraform state bucket",
    command: `gcloud storage buckets create gs://\${PROJECT_ID}-tfstate \\
  --location=\${REGION} --uniform-bucket-level-access
cp terraform/example.backend.conf terraform/backend.conf`,
  },
  {
    order: 3,
    title: "Deploy infrastructure",
    command: `cd terraform
terraform init -backend-config=backend.conf
terraform plan
terraform apply`,
  },
  {
    order: 4,
    title: "Render manifests from Terraform state",
    command: `# MCP_INGRESS mirrors enable_cloud_run_private_networking, so the
# rendered Cloud Run YAML stays in sync with Terraform state.
export MCP_INGRESS=$(cd terraform && terraform output -raw mcp_cloud_run_ingress_annotation)
envsubst '\${PROJECT_ID} \${REGION} \${MCP_INGRESS}' < skaffold.yaml.tmpl > skaffold.yaml`,
  },
  {
    order: 5,
    title: "Build images and deploy MCP services",
    command: "skaffold run",
  },
  {
    order: 6,
    title: "Deploy the agent to Agent Runtime",
    command: `uv run python deploy_agent.py \\
  --project=\${PROJECT_ID} --region=\${REGION} \\
  --enable-agent-identity --agent-name=mortgage-agent \\
  --agent-gateway=projects/\${PROJECT_ID}/locations/\${REGION}/agentGateways/agent-gateway \\
  --model-endpoint-location=global`,
  },
  {
    order: 7,
    title: "Grant per-MCP egress IAM",
    command: `./scripts/grant_agent_mcp_egress.sh \\
  --mcp \\
  --agent-id \${AGENT_ID} \\
  --mcp-filter "legacy-dms income-verification"`,
  },
];

export function getGatewayData(): GatewayData {
  return {
    overview: {
      title: "Agent Gateway — Governing Agentic Workloads",
      description:
        "Google's reference architecture for putting an agent's MCP tool calls behind a policy-enforcing gateway. A multi-tool ADK agent runs on Vertex AI Agent Runtime and reaches internal MCP servers on Cloud Run through the Agent Gateway, where per-tool IAM and content screening are enforced before any request lands. This is the production-governance counterpart to the MCP Servers tab, which covers the servers themselves.",
      repoUrl: "https://codelabs.developers.google.com/cloudnet-agent-gateway",
      codelabUrl: "https://codelabs.developers.google.com/cloudnet-agent-gateway",
      license: "Apache 2.0",
    },
    controls: CONTROLS,
    modes: MODES,
    mcpServices: MCP_SERVICES,
    prerequisites: [
      "A Google Cloud project with billing enabled",
      "gcloud (Cloud SDK)",
      "terraform >= 1.5",
      "skaffold for image builds",
      "Python 3.12+ with uv",
      "envsubst (gettext) and jq — Cloud Shell already has these",
      "(Secure path only) a public DNS zone you own, used for the LB cert",
    ],
    steps: STEPS,
    sakthaiRelevance:
      "The pattern maps directly onto this repo's own posture. sakthai's GuardrailPolicy is an in-process pre/post check around every tool call; Model Armor is the same idea enforced out-of-process, so a bypass in the agent cannot skip it. Per-tool IAM via Agent Identity is the network-level version of SAKTHAI_SHELL_ALLOW and the read_file path allowlist — deny by default, grant one capability at a time. And the Agent Registry solves the same problem as ~/.sakthai/mcp.json, except resolution happens at runtime rather than at process start.",
  };
}
