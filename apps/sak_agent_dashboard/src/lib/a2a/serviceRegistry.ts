import {
  A2AServiceRegistration,
  A2ACapabilityDescriptor,
  A2AHealthStatus
} from './types';

/**
 * Decentralized In-Memory Service Registry for Sak-Family Agents.
 * Maintains capability manifests, health status, latency metrics,
 * and discovery lookup indices.
 */

export const INITIAL_SAK_FLEET: A2AServiceRegistration[] = [
  {
    agentSlug: 'sakjules',
    agentName: 'SakJules',
    role: 'Automation & CI/CD Master',
    endpoint: 'a2a://sakjules.sakthai.local/rpc',
    capabilities: [
      {
        id: 'cap-jules-docker',
        name: 'Scaffold Production Dockerfile',
        description: 'Generate multi-stage, rootless, minimal container images.',
        category: 'coding',
        inputSchema: { framework: 'string', nodeVersion: 'number' },
        outputSchema: { dockerfile: 'string', layerCount: 'number' },
        rateLimitRpm: 120,
        avgLatencyMs: 210,
        astRequired: true
      },
      {
        id: 'cap-jules-ci',
        name: 'Generate GitHub Actions Matrix',
        description: 'Create multi-job CI/CD workflows with caching and linters.',
        category: 'coding',
        inputSchema: { pythonVersions: 'array', linters: 'array' },
        outputSchema: { workflowYaml: 'string', jobCount: 'number' },
        rateLimitRpm: 90,
        avgLatencyMs: 180,
        astRequired: true
      }
    ],
    healthStatus: 'healthy',
    lastHeartbeat: new Date().toISOString(),
    version: '1.4.0',
    uptimeSeconds: 86400,
    totalCallsHandled: 1420
  },
  {
    agentSlug: 'saksee',
    agentName: 'SakSee',
    role: 'Security Sentinel & Guardrail Auditor',
    endpoint: 'a2a://saksee.sakthai.local/rpc',
    capabilities: [
      {
        id: 'cap-see-ast',
        name: 'AST Guardrail & Path Audit',
        description: 'Verify shell commands, input paths, and code AST for safety violations.',
        category: 'security',
        inputSchema: { command: 'string', targetPath: 'string' },
        outputSchema: { allowed: 'boolean', violationReason: 'string' },
        rateLimitRpm: 300,
        avgLatencyMs: 45,
        astRequired: false
      },
      {
        id: 'cap-see-jailbreak',
        name: 'Prompt Injection & Jailbreak Detector',
        description: 'Detect adversarial system override attempts in incoming prompts.',
        category: 'security',
        inputSchema: { prompt: 'string' },
        outputSchema: { isJailbreak: 'boolean', confidence: 'number' },
        rateLimitRpm: 250,
        avgLatencyMs: 65,
        astRequired: false
      }
    ],
    healthStatus: 'healthy',
    lastHeartbeat: new Date().toISOString(),
    version: '1.4.0',
    uptimeSeconds: 91200,
    totalCallsHandled: 3890
  },
  {
    agentSlug: 'sakking',
    agentName: 'SakKing',
    role: 'Strategy & Orchestration Leader',
    endpoint: 'a2a://sakking.sakthai.local/rpc',
    capabilities: [
      {
        id: 'cap-king-dispatch',
        name: 'Multi-Agent Task Orchestrator',
        description: 'Decompose high-level goals into parallel subagent execution tracks.',
        category: 'orchestration',
        inputSchema: { goal: 'string', priority: 'string' },
        outputSchema: { subtasks: 'array', executionGraph: 'object' },
        rateLimitRpm: 150,
        avgLatencyMs: 190,
        astRequired: true
      }
    ],
    healthStatus: 'healthy',
    lastHeartbeat: new Date().toISOString(),
    version: '1.4.0',
    uptimeSeconds: 98000,
    totalCallsHandled: 2150
  },
  {
    agentSlug: 'saktan',
    agentName: 'SakTan',
    role: 'Data, Analytics & Finance Engineer',
    endpoint: 'a2a://saktan.sakthai.local/rpc',
    capabilities: [
      {
        id: 'cap-tan-cost',
        name: 'Token Cost Model & Burn Rate Forecaster',
        description: 'Compute API token expenditure, model cost projections, and spend limits.',
        category: 'analytics',
        inputSchema: { usageLogs: 'array', model: 'string' },
        outputSchema: { totalSpendUsd: 'number', costPerThousand: 'number' },
        rateLimitRpm: 180,
        avgLatencyMs: 140,
        astRequired: false
      }
    ],
    healthStatus: 'healthy',
    lastHeartbeat: new Date().toISOString(),
    version: '1.4.0',
    uptimeSeconds: 84000,
    totalCallsHandled: 1680
  },
  {
    agentSlug: 'sakthai',
    agentName: 'SakThai',
    role: 'Core Architecture & Memory Custodian',
    endpoint: 'a2a://sakthai.sakthai.local/rpc',
    capabilities: [
      {
        id: 'cap-thai-memory',
        name: 'Persistent Vector Memory Search & Sync',
        description: 'Query SQLite knowledge graph embeddings with cosine similarity distance.',
        category: 'memory',
        inputSchema: { query: 'string', topK: 'number' },
        outputSchema: { matches: 'array', topSimilarity: 'number' },
        rateLimitRpm: 200,
        avgLatencyMs: 95,
        astRequired: false
      }
    ],
    healthStatus: 'healthy',
    lastHeartbeat: new Date().toISOString(),
    version: '1.4.0',
    uptimeSeconds: 104000,
    totalCallsHandled: 4210
  },
  {
    agentSlug: 'saknoi',
    agentName: 'SakNoi',
    role: 'Prompt & Persona Alignment Specialist',
    endpoint: 'a2a://saknoi.sakthai.local/rpc',
    capabilities: [
      {
        id: 'cap-noi-caveman',
        name: 'Caveman Token Compression Engine',
        description: 'Condense verbose system directives into hyper-dense token-saving prompts.',
        category: 'prompt',
        inputSchema: { prompt: 'string', targetCompressionPercent: 'number' },
        outputSchema: { compressedPrompt: 'string', tokensSaved: 'number' },
        rateLimitRpm: 220,
        avgLatencyMs: 80,
        astRequired: false
      }
    ],
    healthStatus: 'healthy',
    lastHeartbeat: new Date().toISOString(),
    version: '1.4.0',
    uptimeSeconds: 79000,
    totalCallsHandled: 980
  }
];

export class ServiceRegistry {
  private static fleet: Map<string, A2AServiceRegistration> = new Map(
    INITIAL_SAK_FLEET.map((agent) => [agent.agentSlug, agent])
  );

  /**
   * Get all registered agents in the fleet.
   */
  public static getAllAgents(): A2AServiceRegistration[] {
    return Array.from(this.fleet.values());
  }

  /**
   * Get a single agent registration by slug.
   */
  public static getAgent(slug: string): A2AServiceRegistration | undefined {
    return this.fleet.get(slug);
  }

  /**
   * Discover agents that provide a specific capability or category.
   */
  public static discoverCapabilities(
    category?: A2ACapabilityDescriptor['category']
  ): Array<{ agentSlug: string; agentName: string; capability: A2ACapabilityDescriptor }> {
    const results: Array<{
      agentSlug: string;
      agentName: string;
      capability: A2ACapabilityDescriptor;
    }> = [];

    this.fleet.forEach((agent) => {
      if (agent.healthStatus === 'offline') return;

      agent.capabilities.forEach((cap) => {
        if (!category || cap.category === category) {
          results.push({
            agentSlug: agent.agentSlug,
            agentName: agent.agentName,
            capability: cap
          });
        }
      });
    });

    return results;
  }

  /**
   * Record a heartbeat from an agent node.
   */
  public static recordHeartbeat(slug: string): boolean {
    const agent = this.fleet.get(slug);
    if (!agent) return false;
    agent.lastHeartbeat = new Date().toISOString();
    agent.healthStatus = 'healthy';
    return true;
  }

  /**
   * Increment call counter for an agent.
   */
  public static recordCallHandled(slug: string): void {
    const agent = this.fleet.get(slug);
    if (agent) {
      agent.totalCallsHandled += 1;
    }
  }

  /**
   * Calculate fleet health overview statistics.
   */
  public static getFleetHealth(): A2AHealthStatus {
    const agents = Array.from(this.fleet.values());
    const fleetSize = agents.length;
    const healthyNodes = agents.filter((a) => a.healthStatus === 'healthy').length;

    const totalCapabilities = agents.reduce((acc, a) => acc + a.capabilities.length, 0);

    const avgFleetLatencyMs = Math.round(
      agents.reduce(
        (acc, a) =>
          acc +
          a.capabilities.reduce((cAcc, c) => cAcc + c.avgLatencyMs, 0) /
            Math.max(1, a.capabilities.length),
        0
      ) / Math.max(1, fleetSize)
    );

    return {
      fleetSize,
      healthyNodes,
      totalCapabilities,
      uptimePercentage: 100.0,
      avgFleetLatencyMs,
      activeDelegations: 6
    };
  }
}
