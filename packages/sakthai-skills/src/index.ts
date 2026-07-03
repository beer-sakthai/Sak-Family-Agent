import http from 'http';
import { GoogleGenAI } from '@google/genai';
import { runAgentLoop } from './agent';
import { calculateSkill } from './skills/sampleSkill';
import { registerSkill } from './skills/registry';

// Ensure standard skills are registered
registerSkill(calculateSkill);

const apiKey = process.env.GEMINI_API_KEY;
// If GEMINI_API_KEY is not set, initialize the client in production Vertex AI mode.
// This leverages GCP IAM and the Cloud Run Service Account's Application Default Credentials (ADC).
const ai = apiKey
  ? new GoogleGenAI({ apiKey })
  : new GoogleGenAI({
      vertexai: true,
      project: process.env.GOOGLE_CLOUD_PROJECT || 'supple-cosine-470306-d4',
      location: process.env.GOOGLE_CLOUD_REGION || 'us-east1'
    });

const PORT = process.env.PORT || '8080';

const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');

  if (req.method === 'GET' && (req.url === '/' || req.url === '/health')) {
    res.writeHead(200);
    res.end(JSON.stringify({ status: 'ok', service: 'sakthai-skills' }));
    return;
  }

  if (req.method === 'POST' && req.url === '/chat') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', async () => {
      try {
        const payload = JSON.parse(body);
        if (!payload.prompt || typeof payload.prompt !== 'string') {
          res.writeHead(400);
          res.end(JSON.stringify({ error: 'Missing or invalid "prompt" in request body' }));
          return;
        }

        const model = payload.model || 'gemini-2.5-flash';
        const responseText = await runAgentLoop(ai, model, payload.prompt);

        res.writeHead(200);
        res.end(JSON.stringify({ response: responseText }));
      } catch (err: any) {
        res.writeHead(500);
        res.end(JSON.stringify({ error: err.message || 'Internal server error' }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ error: 'Not Found' }));
});

if (require.main === module) {
  server.listen(Number(PORT), '0.0.0.0', () => {
    console.log(`Server is listening on port ${PORT}`);
  });
}

export { server };
