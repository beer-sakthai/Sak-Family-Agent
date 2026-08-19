import {
  A2AMessageEnvelope,
  A2ADelegationRequest,
  A2ADelegationResult
} from './types';
import { ServiceRegistry } from './serviceRegistry';

/**
 * A2A Dispatch and Execution Engine.
 * Handles JSON-RPC 2.0 message framing, AST guardrail validation,
 * and inter-agent task delegation.
 */

export class A2AEngine {
  private static recentDelegations: A2ADelegationResult[] = [
    {
      delegationId: 'del-seed-01',
      correlationId: 'corr-seed-01',
      agentFrom: 'sakking',
      agentTo: 'sakjules',
      method: 'cap-jules-docker',
      status: 'success',
      result: { dockerfile: 'FROM node:20-alpine\nUSER node\nWORKDIR /app', layerCount: 4 },
      executionTimeMs: 195,
      astAudited: true,
      timestamp: new Date(Date.now() - 60000).toISOString()
    },
    {
      delegationId: 'del-seed-02',
      correlationId: 'corr-seed-02',
      agentFrom: 'sakking',
      agentTo: 'saksee',
      method: 'cap-see-ast',
      status: 'success',
      result: { allowed: true, violationReason: 'NONE' },
      executionTimeMs: 42,
      astAudited: true,
      timestamp: new Date(Date.now() - 30000).toISOString()
    }
  ];

  /**
   * Package payload into standard JSON-RPC 2.0 A2A Message Envelope.
   */
  public static createEnvelope<T>(
    agentFrom: string,
    agentTo: string,
    method: string,
    params: T
  ): A2AMessageEnvelope<T> {
    const timestamp = new Date().toISOString();
    const id = `rpc-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    const correlationId = `corr-${agentFrom}-${agentTo}-${Date.now()}`;

    return {
      jsonrpc: '2.0',
      id,
      agentFrom,
      agentTo,
      method,
      params,
      correlationId,
      timestamp,
      signature: `sak-sig-${Date.now().toString(16)}`
    };
  }

  /**
   * Execute an authenticated task delegation across peer agents.
   */
  public static async delegateTask(
    req: A2ADelegationRequest
  ): Promise<A2ADelegationResult> {
    const startTime = Date.now();
    const targetAgent = ServiceRegistry.getAgent(req.agentTo);

    if (!targetAgent) {
      return {
        delegationId: `del-${Date.now()}`,
        correlationId: `corr-${req.agentFrom}-${req.agentTo}`,
        agentFrom: req.agentFrom,
        agentTo: req.agentTo,
        method: req.capabilityId,
        status: 'failed',
        error: `Target agent ${req.agentTo} not found in service registry`,
        executionTimeMs: Date.now() - startTime,
        astAudited: false,
        timestamp: new Date().toISOString()
      };
    }

    const capability = targetAgent.capabilities.find((c) => c.id === req.capabilityId);
    if (!capability) {
      return {
        delegationId: `del-${Date.now()}`,
        correlationId: `corr-${req.agentFrom}-${req.agentTo}`,
        agentFrom: req.agentFrom,
        agentTo: req.agentTo,
        method: req.capabilityId,
        status: 'failed',
        error: `Capability ${req.capabilityId} not supported by ${targetAgent.agentName}`,
        executionTimeMs: Date.now() - startTime,
        astAudited: false,
        timestamp: new Date().toISOString()
      };
    }

    // AST Guardrail Check
    let astAudited = false;
    if (capability.astRequired) {
      astAudited = true;
      const payloadStr = JSON.stringify(req.payload);
      
      const isPathTraversal =
        payloadStr.includes('..') ||
        /\/etc\//i.test(payloadStr) ||
        /\/proc\//i.test(payloadStr) ||
        /\/root\//i.test(payloadStr) ||
        /\.ssh/i.test(payloadStr) ||
        /\.env/i.test(payloadStr) ||
        /id_rsa/i.test(payloadStr);

      const isCommandInjection =
        /\brm\s+(-[rfRF]+\s+|--force|--recursive)/i.test(payloadStr) ||
        /\bmkfs\b/i.test(payloadStr) ||
        /\bdd\s+if=/i.test(payloadStr) ||
        /:\(\)\{\s*:\|:&\s*\};:/i.test(payloadStr) ||
        /\b(eval|exec|Function)\s*\(/i.test(payloadStr) ||
        /(curl|wget)\s+.*\|\s*(sh|bash)/i.test(payloadStr) ||
        /[;&|`$]\s*(cat|ls|whoami|id|nc|bash|sh)\b/i.test(payloadStr);

      if (isPathTraversal || isCommandInjection) {
        return {
          delegationId: `del-${Date.now()}`,
          correlationId: `corr-${req.agentFrom}-${req.agentTo}`,
          agentFrom: req.agentFrom,
          agentTo: req.agentTo,
          method: capability.name,
          status: 'failed',
          error: 'AST Security Gate: Forbidden path traversal or destructive command detected',
          executionTimeMs: 25,
          astAudited: true,
          timestamp: new Date().toISOString()
        };
      }
    }

    // Simulate Execution
    const latency = Math.max(30, Math.floor(capability.avgLatencyMs + (Math.random() * 40 - 20)));
    await new Promise((r) => setTimeout(r, 40)); // Async yield

    ServiceRegistry.recordCallHandled(req.agentTo);

    const resultPayload = {
      executedBy: targetAgent.agentName,
      capability: capability.name,
      output: `Successfully executed ${capability.name} on behalf of ${req.agentFrom}.`,
      processedAt: new Date().toISOString()
    };

    const delegationResult: A2ADelegationResult = {
      delegationId: `del-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      correlationId: `corr-${req.agentFrom}-${req.agentTo}-${Date.now()}`,
      agentFrom: req.agentFrom,
      agentTo: req.agentTo,
      method: capability.name,
      status: 'success',
      result: resultPayload,
      executionTimeMs: latency,
      astAudited,
      timestamp: new Date().toISOString()
    };

    this.recentDelegations.unshift(delegationResult);
    if (this.recentDelegations.length > 50) {
      this.recentDelegations.pop();
    }

    return delegationResult;
  }

  /**
   * Return recent delegations.
   */
  public static getRecentDelegations(): A2ADelegationResult[] {
    return [...this.recentDelegations];
  }
}
