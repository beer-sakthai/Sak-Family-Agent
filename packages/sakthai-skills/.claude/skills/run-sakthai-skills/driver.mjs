#!/usr/bin/env node
// Smoke driver for sakthai-skills (root ~/ package).
// Run from the workspace root AFTER `npm run build`:
//   node .claude/skills/run-sakthai-skills/driver.mjs
//
// What it does, in order:
//   1. Direct invocation (offline): drives runAgentLoop() from dist/ with a
//      mocked GoogleGenAI client — exercises the full tool-call cycle
//      (functionCall -> skill.execute -> functionResponse -> final text).
//   2. Server smoke: spawns `node dist/src/index.js` on a scratch port and
//      curls /health, a bad /chat payload (400), and an unknown route (404).
//   3. Live /chat (optional): only if GEMINI_API_KEY is set. Without it the
//      server falls back to Vertex ADC, which 403s on this machine.
//
// Exit code 0 = all mandatory checks passed.

import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const PORT = process.env.DRIVER_PORT || '8199';
const BASE = `http://127.0.0.1:${PORT}`;

let failures = 0;
function check(label, ok, detail = '') {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures++;
}

// ---------- 1. Direct invocation: agent loop with mocked Gemini ----------
const { runAgentLoop } = require(path.join(root, 'dist/src/agent.js'));
require(path.join(root, 'dist/src/skills/sampleSkill.js')); // registers 'calculate'

// Mock client: first call emits a functionCall for the calculate skill,
// second call reads the tool response and emits the final text.
const mockAi = {
  models: {
    async generateContent({ contents }) {
      const last = contents[contents.length - 1];
      if (last.role === 'tool') {
        const result = last.parts[0].functionResponse.response.output.result;
        return { candidates: [{ content: { role: 'model', parts: [{ text: `The answer is ${result}` }] } }] };
      }
      return {
        candidates: [{
          content: {
            role: 'model',
            parts: [{ functionCall: { name: 'calculate', args: { operation: 'multiply', a: 6, b: 7 } } }]
          }
        }]
      };
    }
  }
};

const answer = await runAgentLoop(mockAi, 'mock-model', 'What is 6 times 7?');
check('agent loop tool-call cycle (mocked Gemini)', answer === 'The answer is 42', `got: "${answer}"`);

// Error path: unknown skill name must come back as a functionResponse error,
// not crash the loop.
let sawError = false;
const errAi = {
  models: {
    async generateContent({ contents }) {
      const last = contents[contents.length - 1];
      if (last.role === 'tool') {
        sawError = !!last.parts[0].functionResponse.response.error;
        return { candidates: [{ content: { role: 'model', parts: [{ text: 'done' }] } }] };
      }
      return {
        candidates: [{
          content: { role: 'model', parts: [{ functionCall: { name: 'no_such_skill', args: {} } }] }
        }]
      };
    }
  }
};
await runAgentLoop(errAi, 'mock-model', 'x');
check('unknown skill surfaces as tool error', sawError);

// ---------- 2. Server smoke ----------
const server = spawn('node', ['dist/src/index.js'], {
  cwd: root,
  env: { ...process.env, PORT },
  stdio: ['ignore', 'pipe', 'pipe']
});
let serverLog = '';
server.stdout.on('data', d => (serverLog += d));
server.stderr.on('data', d => (serverLog += d));

try {
  let up = false;
  for (let i = 0; i < 20 && !up; i++) {
    await sleep(250);
    up = serverLog.includes('listening');
  }
  check('server starts', up, serverLog.trim().split('\n')[0]);

  const health = await fetch(`${BASE}/health`).then(r => r.json());
  check('GET /health', health.status === 'ok' && health.service === 'sakthai-skills', JSON.stringify(health));

  const bad = await fetch(`${BASE}/chat`, { method: 'POST', body: '{}' });
  check('POST /chat without prompt -> 400', bad.status === 400);

  const notFound = await fetch(`${BASE}/nope`);
  check('unknown route -> 404', notFound.status === 404);

  // ---------- 3. Live /chat (optional; needs GEMINI_API_KEY) ----------
  if (process.env.GEMINI_API_KEY) {
    const live = await fetch(`${BASE}/chat`, {
      method: 'POST',
      body: JSON.stringify({ prompt: 'Use the calculate tool to multiply 6 by 7, then answer with the number.' })
    });
    const body = await live.json();
    check('live /chat (GEMINI_API_KEY)', live.status === 200 && /42/.test(body.response || ''), JSON.stringify(body).slice(0, 200));
  } else {
    console.log('SKIP  live /chat — GEMINI_API_KEY not set (Vertex ADC fallback 403s on this machine)');
  }
} finally {
  server.kill();
}

console.log(failures === 0 ? '\nAll checks passed.' : `\n${failures} check(s) FAILED.`);
process.exit(failures === 0 ? 0 : 1);
