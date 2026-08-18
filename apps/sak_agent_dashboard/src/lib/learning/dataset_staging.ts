import fs from 'fs';
import path from 'path';
import os from 'os';
import { DatasetStagingEntry } from '../types';

const SENSITIVE_PATTERNS = [
  /(?:sk-[a-zA-Z0-9]{20,48})/g, // OpenAI keys
  /(?:AIzaSy[a-zA-Z0-9_-]{33})/g, // Google API keys
  /(?:ghp_[a-zA-Z0-9]{36})/g, // GitHub Personal Access Tokens
  /(?:Bearer\s+[a-zA-Z0-9._-]{20,})/gi, // Bearer auth tokens
  /(?:password\s*[:=]\s*["'][^"']+["'])/gi, // Plaintext passwords
  /([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/g, // Emails (scrubbed to [EMAIL_REDACTED])
];

/**
 * Scrubs API keys, passwords, bearer tokens, and emails from text before staging into dataset pools.
 */
export function scrubSensitiveTokens(text: string): string {
  if (!text) return '';
  let sanitized = text;

  // OpenAI
  sanitized = sanitized.replace(/(?:sk-[a-zA-Z0-9]{20,48})/g, '[OPENAI_KEY_REDACTED]');
  // Google / Gemini
  sanitized = sanitized.replace(/(?:AIzaSy[a-zA-Z0-9_-]{20,45})/g, '[GEMINI_KEY_REDACTED]');
  // GitHub
  sanitized = sanitized.replace(/(?:ghp_[a-zA-Z0-9]{36})/g, '[GITHUB_TOKEN_REDACTED]');
  // Bearer
  sanitized = sanitized.replace(/(?:Bearer\s+[a-zA-Z0-9._-]{20,})/gi, 'Bearer [TOKEN_REDACTED]');
  // Password
  sanitized = sanitized.replace(/(password\s*[:=]\s*["'])[^"']+(["'])/gi, '$1[PASSWORD_REDACTED]$2');
  // Email
  sanitized = sanitized.replace(/([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)/g, '[EMAIL_REDACTED]');

  return sanitized;
}

export function computeDatasetHeuristicScore(
  instruction: string,
  finalOutput: string,
  toolOutputsCount: number,
  allToolsSafe: boolean
): number {
  let score = 50;

  if (instruction.length > 20) score += 10;
  if (finalOutput.length > 50) score += 15;
  if (finalOutput.includes('```')) score += 10; // Contains structured code or markdown
  if (toolOutputsCount > 0) score += 10;
  if (allToolsSafe) score += 5;

  return Math.min(100, Math.max(0, score));
}

export function getStagingDirectory(): string {
  const baseHome = path.resolve(os.homedir());
  const stagingDir = path.resolve(baseHome, '.sakthai', 'learning', 'dataset-staging');
  if (!stagingDir.startsWith(baseHome)) {
    throw new Error('Invalid staging directory path');
  }
  return stagingDir;
}

export function stageDatasetEntry(entry: Omit<DatasetStagingEntry, 'id' | 'timestamp' | 'scrubbedPII'>): DatasetStagingEntry {
  const stagingDir = getStagingDirectory();
  try {
    if (!fs.existsSync(stagingDir)) {
      fs.mkdirSync(stagingDir, { recursive: true });
    }
  } catch {
    // Fallback if filesystem permissions restrict
  }

  const cleanInstruction = scrubSensitiveTokens(entry.instruction);
  const cleanFinalOutput = scrubSensitiveTokens(entry.finalOutput);
  const cleanTraces = entry.reasoningTraces.map((t) => ({
    persona: t.persona,
    thought: scrubSensitiveTokens(t.thought),
    toolsUsed: t.toolsUsed,
  }));

  const fullEntry: DatasetStagingEntry = {
    id: `stage_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    timestamp: new Date().toISOString(),
    sessionId: entry.sessionId,
    instruction: cleanInstruction,
    personasInvolved: entry.personasInvolved,
    reasoningTraces: cleanTraces,
    finalOutput: cleanFinalOutput,
    stagedBy: entry.stagedBy,
    heuristicScore: entry.heuristicScore,
    scrubbedPII: true,
  };

  const stagingFile = path.resolve(stagingDir, 'staging.jsonl');
  if (!stagingFile.startsWith(stagingDir)) {
    throw new Error('Path traversal detected');
  }

  try {
    fs.appendFileSync(stagingFile, JSON.stringify(fullEntry) + '\n', 'utf-8');
  } catch {
    // Non-blocking in ephemeral test environments
  }

  return fullEntry;
}

export function readStagedEntries(limit = 50): DatasetStagingEntry[] {
  const stagingDir = getStagingDirectory();
  const stagingFile = path.resolve(stagingDir, 'staging.jsonl');
  if (!stagingFile.startsWith(stagingDir) || !fs.existsSync(stagingFile)) {
    return [];
  }

  try {
    const lines = fs.readFileSync(stagingFile, 'utf-8').trim().split('\n').filter(Boolean);
    const parsed: DatasetStagingEntry[] = [];
    for (const line of lines.slice(-limit)) {
      try {
        parsed.push(JSON.parse(line));
      } catch {
        // Skip malformed
      }
    }
    return parsed.reverse();
  } catch {
    return [];
  }
}
