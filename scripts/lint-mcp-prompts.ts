#!/usr/bin/env npx tsx
import { readdir, readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import YAML from 'yaml';

interface LintIssue {
  file: string;
  rule: string;
  message: string;
}

async function collectPromptFiles(targetPath: string): Promise<string[]> {
  const results: string[] = [];
  async function walk(dir: string) {
    let entries;
    try {
      entries = await readdir(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
      const fullPath = join(dir, entry.name);
      if (entry.isDirectory()) {
        await walk(fullPath);
      } else if (entry.isFile() && entry.name.endsWith('.prompt')) {
        results.push(fullPath);
      }
    }
  }

  if (targetPath.endsWith('.prompt')) {
    return [resolve(targetPath)];
  }
  await walk(resolve(targetPath));
  return results;
}

function splitFrontmatter(raw: string): { frontmatter: Record<string, unknown>; body: string } {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) {
    return { frontmatter: {}, body: raw };
  }
  const parsed = YAML.parse(match[1]) ?? {};
  return { frontmatter: parsed as Record<string, unknown>, body: match[2] };
}

function lintPrompt(file: string, raw: string): LintIssue[] {
  const issues: LintIssue[] = [];
  const { frontmatter, body } = splitFrontmatter(raw);

  // Rule 1: MCP prompts only accept string-valued top-level input parameters
  const input = frontmatter.input as { schema?: Record<string, unknown> } | undefined;
  if (input?.schema && typeof input.schema === 'object') {
    for (const [rawKey, rawType] of Object.entries(input.schema)) {
      const cleanKey = rawKey.replace(/\?$/, '');
      if (rawKey.includes('(array)') || rawKey.includes('(object)')) {
        issues.push({
          file,
          rule: 'mcp-string-only-params',
          message: `Input field "${rawKey}" uses non-string Picoschema structure; createMcpServer requires top-level string parameters.`,
        });
        continue;
      }
      if (typeof rawType === 'string') {
        const baseType = rawType.split(',')[0].trim();
        if (baseType !== 'string' && !rawKey.includes('(enum)')) {
          issues.push({
            file,
            rule: 'mcp-string-only-params',
            message: `Input field "${cleanKey}" has type "${baseType}"; MCP prompts only accept string parameters.`,
          });
        }
      } else if (typeof rawType === 'object' && rawType !== null) {
        issues.push({
          file,
          rule: 'mcp-string-only-params',
          message: `Input field "${cleanKey}" is nested; flatten or serialize to string for MCP prompt export.`,
        });
      }
    }
  }

  // Rule 2: MCP prompts only support user and model messages (no system role)
  if (/\{\{\s*role\s+["']system["']\s*\}\}/i.test(body)) {
    issues.push({
      file,
      rule: 'mcp-no-system-role',
      message: 'Found {{role "system"}}; MCP prompts only support "user" and "model" message roles.',
    });
  }

  // Rule 3: MCP prompts cannot mix text and {{media}} in the same message block
  const roleBlocks = body.split(/\{\{\s*role\s+["'](?:user|model)["']\s*\}\}/i);
  for (const block of roleBlocks) {
    const hasMedia = /\{\{\s*media\b/.test(block);
    const withoutHandlebars = block.replace(/\{\{[\s\S]*?\}\}/g, '').trim();
    if (hasMedia && withoutHandlebars.length > 0) {
      issues.push({
        file,
        rule: 'mcp-single-type-message',
        message: 'Message block mixes plain text with {{media}}; split media and text into separate role messages.',
      });
    }
  }

  // Rule 4: Verify ext metadata does not leak into input.schema
  if (frontmatter.ext && input?.schema && 'ext' in input.schema) {
    issues.push({
      file,
      rule: 'dotprompt-ext-leak',
      message: 'Found "ext" inside input.schema; move custom metadata to top-level frontmatter "ext".',
    });
  }

  return issues;
}

async function main() {
  const args = process.argv.slice(2).filter(Boolean);
  const candidateTarget = args.find((a) => !a.startsWith('--') && !['audit', 'eval', 'rag', 'a2ui', 'optimize'].includes(a)) ?? '.';

  if (args.includes('--help')) {
    console.log('Usage: npx tsx lint-mcp-prompts.ts [directory-or-file.prompt]');
    process.exit(0);
  }

  const files = await collectPromptFiles(candidateTarget);
  if (files.length === 0) {
    console.log(`[lint-mcp-prompts] No .prompt files found under ${candidateTarget}.`);
    process.exit(0);
  }

  const allIssues: LintIssue[] = [];
  for (const file of files) {
    const content = await readFile(file, 'utf8');
    allIssues.push(...lintPrompt(file, content));
  }

  if (allIssues.length > 0) {
    console.error(`[lint-mcp-prompts] HARD FAIL: ${allIssues.length} violation(s) detected:`);
    for (const issue of allIssues) {
      console.error(`  - ${issue.file} [${issue.rule}]: ${issue.message}`);
    }
    process.exit(1);
  }

  console.log(`[lint-mcp-prompts] PASS: Validated ${files.length} .prompt file(s) for MCP compatibility.`);
  process.exit(0);
}

main().catch((err) => {
  console.error('[lint-mcp-prompts] Fatal error:', err);
  process.exit(2);
});

