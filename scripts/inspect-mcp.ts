#!/usr/bin/env npx tsx
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { genkit } from 'genkit';
import { createMcpClient, type McpClientOptions } from '@genkit-ai/mcp';

interface InspectTargetConfig {
  mode: 'stdio' | 'http' | 'genkit-server';
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  url?: string;
  headers?: Record<string, string>;
  roots?: Array<{ uri: string; name?: string }>;
  tokenWarnThreshold?: number;
}

function estimateTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

async function resolveTarget(rawArgs: string[]): Promise<InspectTargetConfig> {
  const cleaned = rawArgs.filter(
    (a) => !a.startsWith('--') && !['audit', 'eval', 'rag', 'a2ui', 'optimize'].includes(a)
  );
  const target = cleaned[0];

  if (!target) {
    return {
      mode: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-filesystem', process.cwd()],
      roots: [{ uri: `file://${process.cwd()}`, name: 'workspace' }],
      tokenWarnThreshold: 4000,
    };
  }

  if (target.startsWith('http://') || target.startsWith('https://')) {
    return {
      mode: 'http',
      url: target,
      roots: [{ uri: `file://${process.cwd()}`, name: 'workspace' }],
      tokenWarnThreshold: 4000,
    };
  }

  if (target.endsWith('.json')) {
    const raw = await readFile(resolve(target), 'utf8');
    return JSON.parse(raw) as InspectTargetConfig;
  }

  if (target.endsWith('.ts') || target.endsWith('.js')) {
    return {
      mode: 'genkit-server',
      command: 'npx',
      args: ['tsx', resolve(target)],
      roots: [{ uri: `file://${process.cwd()}`, name: 'workspace' }],
      tokenWarnThreshold: 4000,
    };
  }

  console.error(`[inspect-mcp] Invalid target "${target}". Provide an HTTP(S) URL, .json config, or .ts/.js server entry.`);
  process.exit(2);
}

function buildServerConfig(cfg: InspectTargetConfig): McpClientOptions['mcpServer'] {
  if (cfg.mode === 'http') {
    if (!cfg.url) {
      console.error('[inspect-mcp] HTTP mode requires "url".');
      process.exit(2);
    }
    return {
      url: cfg.url,
      roots: cfg.roots,
      requestInit: cfg.headers ? { headers: cfg.headers } : undefined,
    };
  }

  if (!cfg.command) {
    console.error('[inspect-mcp] stdio / genkit-server mode requires "command".');
    process.exit(2);
  }
  return {
    command: cfg.command,
    args: cfg.args ?? [],
    env: cfg.env,
    roots: cfg.roots,
  };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log('Usage: npx tsx inspect-mcp.ts [url | mcp-target.json | server-entry.ts]');
    process.exit(0);
  }

  const cfg = await resolveTarget(args);
  const ai = genkit({});
  const serverConfig = buildServerConfig(cfg);

  const parsedClient = createMcpClient({
    name: 'auditParsed',
    rawToolResponses: false,
    mcpServer: serverConfig,
  });

  const rawClient = createMcpClient({
    name: 'auditRaw',
    rawToolResponses: true,
    mcpServer: serverConfig,
  });

  try {
    await parsedClient.ready();
    await rawClient.ready();

    const parsedTools = await parsedClient.getActiveTools(ai);
    const rawTools = await rawClient.getActiveTools(ai);

    if (parsedTools.length !== rawTools.length) {
      console.error(
        `[inspect-mcp] HARD FAIL: Tool discovery mismatch (parsed=${parsedTools.length}, raw=${rawTools.length}).`
      );
      process.exit(1);
    }

    let totalSchemaTokens = 0;
    const seenDescriptions = new Map<string, string>();
    const failures: string[] = [];

    for (const tool of parsedTools) {
      const action = tool.__action;
      const desc = action.description ?? '';
      const schemaStr = JSON.stringify(action.inputJsonSchema ?? {});
      totalSchemaTokens += estimateTokens(action.name + desc + schemaStr);

      if (desc.trim().length < 12) {
        failures.push(`Tool "${action.name}" has an underspecified description ("${desc}").`);
      }
      const normDesc = desc.trim().toLowerCase();
      if (seenDescriptions.has(normDesc)) {
        failures.push(
          `Duplicate tool description between "${seenDescriptions.get(normDesc)}" and "${action.name}".`
        );
      } else {
        seenDescriptions.set(normDesc, action.name);
      }
    }

    const threshold = cfg.tokenWarnThreshold ?? 4000;
    if (totalSchemaTokens > threshold) {
      console.warn(
        `[inspect-mcp] WARN: Active tool metadata uses ~${totalSchemaTokens} tokens (threshold=${threshold}). Consider Tool-RAG or consolidation.`
      );
    }

    if (failures.length > 0) {
      console.error(`[inspect-mcp] HARD FAIL: ${failures.length} schema quality issue(s):`);
      for (const f of failures) console.error(`  - ${f}`);
      process.exit(1);
    }

    console.log(
      `[inspect-mcp] PASS: Connected (${cfg.mode}), discovered ${parsedTools.length} tool(s), ~${totalSchemaTokens} metadata tokens.`
    );
    process.exit(0);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    if (message.includes('UnauthorizedError') || message.includes('401')) {
      console.error(
        '[inspect-mcp] HARD FAIL: Streamable HTTP server rejected connection with UnauthorizedError. Configure OAuth authProvider or bearer headers.'
      );
      process.exit(1);
    }
    console.error(`[inspect-mcp] HARD FAIL: Connection or inspection error: ${message}`);
    process.exit(1);
  } finally {
    await parsedClient.disable().catch(() => {});
    await rawClient.disable().catch(() => {});
  }
}

main();

