import { M365CopilotData } from "./types";
import { DEFAULT_M365_ADAPTER } from "./m365/adapter";
import { DEFAULT_AUTH_STRATEGY } from "./m365/authStrategy";

/**
 * M365 Copilot data access — now a thin facade over the Adapter + Strategy
 * design in `./m365/`. The panel and route depend on the adapter interface;
 * this module keeps the historical `getM365CopilotData()` entry point (and the
 * `M365_ACCOUNT_BLOCKER` export) so existing import sites and tests are
 * unchanged.
 */

/**
 * The account-type blocker, promoted to a first-class `AccountTypeGate` on the
 * auth strategy. Re-exported here under its historical name.
 */
export const M365_ACCOUNT_BLOCKER = DEFAULT_AUTH_STRATEGY.accountTypeGate;

/** Assemble the M365 Copilot data shape from the default adapter. */
export function getM365CopilotData(): M365CopilotData {
  return DEFAULT_M365_ADAPTER.getData();
}
