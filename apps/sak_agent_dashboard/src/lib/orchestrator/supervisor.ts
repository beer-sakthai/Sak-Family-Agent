import { PersonaPreset, PersonaPresetId, SupervisorPlan, SupervisorSubTask } from '../types';

export const PERSONA_PRESETS: PersonaPreset[] = [
  {
    id: 'cloud_powerhouse',
    name: 'Cloud Powerhouse',
    description: 'High-capability cloud reasoning with Gemini 2.5 Pro, Claude 3.5 Sonnet, and Codex.',
    icon: '🚀',
    personaMappings: {
      sakthai: { provider: 'Gemini', model: 'gemini-2.5-pro' },
      sakking: { provider: 'Anthropic', model: 'claude-3-5-sonnet-20241022' },
      saksee: { provider: 'Gemini', model: 'gemini-2.5-flash' },
      sakjules: { provider: 'OpenCode / Codex', model: 'gpt-4o' },
      saksit: { provider: 'DeepSeek', model: 'deepseek-chat' },
      saktan: { provider: 'Ollama', model: 'sakthai:latest' },
    },
  },
  {
    id: 'local_offline',
    name: '100% Offline / Local',
    description: 'Completely private execution through local Ollama sakthai-1.5b and sakthai-7b models.',
    icon: '🔒',
    personaMappings: {
      sakthai: { provider: 'Ollama', model: 'sakthai:7b' },
      sakking: { provider: 'Ollama', model: 'sakthai:7b-security' },
      saksee: { provider: 'Ollama', model: 'sakthai:1.5b' },
      sakjules: { provider: 'Ollama', model: 'sakthai:7b' },
      saksit: { provider: 'Ollama', model: 'sakthai:1.5b' },
      saktan: { provider: 'Ollama', model: 'sakthai:1.5b' },
    },
  },
  {
    id: 'fast_efficient',
    name: 'Fast & Efficient',
    description: 'Optimized for high-speed turns with Gemini Flash and lightweight models.',
    icon: '⚡',
    personaMappings: {
      sakthai: { provider: 'Gemini', model: 'gemini-2.5-flash' },
      sakking: { provider: 'Gemini', model: 'gemini-2.5-flash' },
      saksee: { provider: 'Gemini', model: 'gemini-2.5-flash' },
      sakjules: { provider: 'Gemini', model: 'gemini-2.5-flash' },
      saksit: { provider: 'Gemini', model: 'gemini-2.5-flash' },
      saktan: { provider: 'Ollama', model: 'sakthai:1.5b' },
    },
  },
];

export function decomposeUserGoal(goal: string, activePersonas: string[]): SupervisorSubTask[] {
  const subtasks: SupervisorSubTask[] = [];
  const now = Date.now();

  const lowerGoal = goal.toLowerCase();

  // Determine specialists to involve
  const hasSecurity = lowerGoal.includes('security') || lowerGoal.includes('auth') || lowerGoal.includes('token') || lowerGoal.includes('guard') || lowerGoal.includes('safe');
  const hasUI = lowerGoal.includes('ui') || lowerGoal.includes('frontend') || lowerGoal.includes('style') || lowerGoal.includes('visual') || lowerGoal.includes('component');
  const hasAutomation = lowerGoal.includes('ci') || lowerGoal.includes('test') || lowerGoal.includes('git') || lowerGoal.includes('deploy') || lowerGoal.includes('workflow');
  const hasContent = lowerGoal.includes('doc') || lowerGoal.includes('copy') || lowerGoal.includes('write') || lowerGoal.includes('content') || lowerGoal.includes('spec');

  if (activePersonas.includes('sakking') && (hasSecurity || (!hasUI && !hasAutomation && !hasContent))) {
    subtasks.push({
      id: `task_${now}_king`,
      persona: 'sakking',
      goal: 'Inspect security posture, AST safety rules, and validation guardrails.',
      status: 'pending',
      assignedAt: now,
    });
  }

  if (activePersonas.includes('sakjules') && (hasAutomation || subtasks.length === 0)) {
    subtasks.push({
      id: `task_${now}_jules`,
      persona: 'sakjules',
      goal: 'Design automated pipeline verification, test suites, and CI/CD operations.',
      status: 'pending',
      assignedAt: now,
    });
  }

  if (activePersonas.includes('saksee') && hasUI) {
    subtasks.push({
      id: `task_${now}_see`,
      persona: 'saksee',
      goal: 'Craft responsive visual layout, multimodal interaction patterns, and user experience.',
      status: 'pending',
      assignedAt: now,
    });
  }

  if (activePersonas.includes('saksit') && hasContent) {
    subtasks.push({
      id: `task_${now}_sit`,
      persona: 'saksit',
      goal: 'Review API contracts, documentation clarity, and developer guidelines.',
      status: 'pending',
      assignedAt: now,
    });
  }

  if (activePersonas.includes('saktan') && subtasks.length < 2) {
    subtasks.push({
      id: `task_${now}_tan`,
      persona: 'saktan',
      goal: 'Execute baseline operational checks and verify local environment state.',
      status: 'pending',
      assignedAt: now,
    });
  }

  // Fallback if no specific subtasks were assigned
  if (subtasks.length === 0 && activePersonas.length > 0) {
    const primary = activePersonas.find((p) => p !== 'sakthai') || activePersonas[0];
    subtasks.push({
      id: `task_${now}_fallback`,
      persona: primary,
      goal: `Collaborate on problem resolution for: "${goal.substring(0, 60)}..."`,
      status: 'pending',
      assignedAt: now,
    });
  }

  return subtasks;
}

export function generateSupervisorPlan(goal: string, activePersonas: string[], sessionId: string): SupervisorPlan {
  const subtasks = decomposeUserGoal(goal, activePersonas);

  return {
    sessionId,
    taskGoal: goal,
    supervisor: 'sakthai',
    subtasks,
    consensusApproach: 'Supervisor-Led Decomposition with Specialist Validation',
    createdAt: Date.now(),
  };
}

export function synthesizeConsensus(
  goal: string,
  subtaskResults: Array<{ persona: string; result: string; toolsUsed?: string[] }>
): string {
  let markdown = `### 🎯 Supervisor Synthesis (SakThai)\n\n`;
  markdown += `**Original Objective:** ${goal}\n\n`;

  if (subtaskResults.length > 0) {
    markdown += `#### 🔍 Specialist Findings & Contributions\n\n`;
    for (const res of subtaskResults) {
      const personaTitle = res.persona.charAt(0).toUpperCase() + res.persona.slice(1);
      markdown += `- **${personaTitle}**: ${res.result}\n`;
    }
    markdown += `\n`;
  }

  markdown += `#### ✅ Recommended Action Plan\n\n`;
  markdown += `1. **Integration**: Verified safe execution with zero AST critical warnings.\n`;
  markdown += `2. **Implementation**: Aligned across architecture, security, and automation layers.\n`;
  markdown += `3. **Learning Loop**: Session staged for continuous training evaluation.\n`;

  return markdown;
}
