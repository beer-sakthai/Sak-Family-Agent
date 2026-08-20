/**
 * M365 Copilot authentication Strategy.
 *
 * The M365 Copilot SDK can be reached through two mutually exclusive auth
 * modes. Each is modelled as an `AuthStrategy` carrying its own config, its
 * first-use ceremony (the ordered `steps`), and an `AccountTypeGate` that
 * records which Microsoft account types the mode can actually serve. The gate
 * is what makes the repo's own research finding — that the Copilot Retrieval
 * API is blocked for personal Microsoft accounts under *both* modes — a
 * first-class property of the strategy rather than a stray comment.
 */

/** The Microsoft account types a strategy can serve. */
export type M365AccountType = "work_school" | "personal";

/**
 * A gate that runs before any auth mode matters: the account type itself can
 * make a strategy a structural dead end regardless of how it authenticates.
 */
export interface AccountTypeGate {
  /** Account types this strategy can actually serve. */
  allowedAccountTypes: M365AccountType[];
  headline: string;
  body: string;
  specPath: string;
  ruledOutAlternatives: string[];
  viablePath: string;
}

/** One way to authenticate against the M365 Copilot SDK. */
export interface AuthStrategy {
  readonly id: string;
  readonly name: string;
  /** Short label shown next to the tab title, e.g. "Delegated OAuth (azure-identity)". */
  readonly authModel: string;
  readonly description: string;
  /** Ordered first-use ceremony steps, rendered as a numbered walkthrough. */
  readonly steps: string[];
  readonly accountTypeGate: AccountTypeGate;
}

/**
 * The account-type blocker shared by both strategies. The Copilot Retrieval API
 * does not support personal Microsoft accounts under delegated *or* application
 * auth — a work/school Entra ID tenant with Copilot licensing is required
 * regardless of how you authenticate.
 */
const RETRIEVAL_ACCOUNT_GATE: AccountTypeGate = {
  allowedAccountTypes: ["work_school"],
  headline: "Account type gates this before auth mode does",
  body:
    "The Graph Copilot Retrieval API does not support personal Microsoft accounts under any auth mode — delegated or application. A work/school Entra ID tenant with Copilot licensing is required regardless of how you authenticate. Switching from app-only to delegated auth does not unlock it on a personal M365 subscription; the account type is the binding constraint.",
  specPath: "docs/superpowers/specs/2026-08-03-cowork-plugin-design.md",
  ruledOutAlternatives: [
    "Browser automation of the Copilot web UI (Playwright / computer-use) — Microsoft's Copilot Terms of Use explicitly prohibit bots and scrapers, reinforced by the Services Agreement's anti-scraping clauses, with Cloudflare bot protection and prior enforcement precedent (EdgeGPT) as evidence this is not merely theoretical.",
    "Office Agent Frontier (Word/Excel/PowerPoint Agents) — real and free on M365 Premium, but chat/UI-only with no programmatic API.",
  ],
  viablePath:
    "Copilot Cowork is the one surface with a documented developer extensibility path: plugins packaged as Agent Skills + remote MCP connectors, distributed as a standard M365 app package and installable for personal use via `atk install --scope Personal` — no Partner Center submission. This inverts the direction: instead of pulling data out of Copilot, Cowork calls into MCP servers you host.",
};

/**
 * Delegated (signed-in-user) OAuth via `azure-identity`. Every retrieval call
 * is issued *as the signed-in user*, so results respect that user's SharePoint /
 * OneDrive ACLs automatically.
 */
export const DELEGATED_DEVICE_CODE_STRATEGY: AuthStrategy = {
  id: "delegated-device-code",
  name: "Delegated-auth flow",
  authModel: "Delegated OAuth (azure-identity)",
  description:
    "Per-user OAuth via azure-identity. First run prints a device code; the signed-in user completes it in a browser once, and subsequent calls reuse the cached token.",
  steps: [
    "Register an Azure AD app with delegated Microsoft Graph permissions for Copilot Retrieval (e.g. `Files.Read.All`, `Sites.Read.All`).",
    "Provision `DeviceCodeCredential(tenant_id=..., client_id=...)` (or any azure-identity delegated credential).",
    "First run prints a device code + verification URL — the signed-in user completes it in a browser, once.",
    "Subsequent calls reuse the cached token; the credential provider refreshes it silently.",
    "Every retrieval call is issued *as the signed-in user*, so results respect that user's SharePoint / OneDrive ACLs automatically.",
  ],
  accountTypeGate: RETRIEVAL_ACCOUNT_GATE,
};

/**
 * App-only (client-credentials) auth via MSAL. Tenant-wide, no per-user
 * scoping — the shape `teams-copilot-mcp` already uses. Documented here for
 * contrast: it does *not* unlock Copilot Retrieval, which requires delegated
 * auth and a work/school tenant.
 */
export const APP_ONLY_CLIENT_CREDENTIALS_STRATEGY: AuthStrategy = {
  id: "app-only-client-credentials",
  name: "App-only client-credentials flow",
  authModel: "App-only (client-credentials) via MSAL",
  description:
    "Tenant-wide application auth via MSAL client credentials. No interactive sign-in — three env vars and it runs — but the Copilot Retrieval endpoint does not accept application permissions.",
  steps: [
    "Register an Azure AD app with application (not delegated) permissions.",
    "Provision `MSGRAPH_TENANT_ID`, `MSGRAPH_CLIENT_ID`, and `MSGRAPH_CLIENT_SECRET`.",
    "Acquire a token with MSAL's confidential-client application flow.",
    "Call Graph as the application identity — tenant-wide, with no per-user scoping.",
  ],
  accountTypeGate: RETRIEVAL_ACCOUNT_GATE,
};

/** The strategy the M365 tab surfaces by default. */
export const DEFAULT_AUTH_STRATEGY: AuthStrategy = DELEGATED_DEVICE_CODE_STRATEGY;
