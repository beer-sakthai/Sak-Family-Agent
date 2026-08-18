import {
  DatasetCardSpec,
  LoraJobStatus,
  LoraTargetModel,
  LoraTrainingConfig,
  TrainingLossPoint,
} from '../types';
import { readStagedEntries } from './dataset_staging';

// In-memory registry of active/completed training jobs
const activeJobs: Map<string, LoraJobStatus> = new Map();

/**
 * Converts staged dataset entries into ChatML format strings.
 */
export function formatToChatML(instruction: string, response: string, persona = 'sakthai'): string {
  return `<|im_start|>system\nYou are ${persona}, an advanced AI specialist in the Sak-Family ecosystem.<|im_end|>\n<|im_start|>user\n${instruction.trim()}<|im_end|>\n<|im_start|>assistant\n${response.trim()}<|im_end|>`;
}

/**
 * Converts staged dataset entries into Alpaca format.
 */
export function formatToAlpaca(instruction: string, response: string): { instruction: string; input: string; output: string } {
  return {
    instruction: instruction.trim(),
    input: '',
    output: response.trim(),
  };
}

/**
 * Generates Hugging Face dataset card specification from staged session entries.
 */
export function generateDatasetCardSpec(): DatasetCardSpec {
  const staged = readStagedEntries(100);
  const personasSet = new Set<string>();
  let totalLength = 0;

  const samples = staged.map((entry) => {
    entry.personasInvolved.forEach((p) => personasSet.add(p));
    totalLength += entry.instruction.length + entry.finalOutput.length;
    return {
      instruction: entry.instruction,
      response: entry.finalOutput,
      persona: entry.personasInvolved[0] || 'sakthai',
    };
  });

  const totalSamples = samples.length;
  const avgTokenLength = totalSamples > 0 ? Math.round(totalLength / totalSamples / 4) : 256;

  return {
    id: 'sakthai_combined_v7',
    name: 'SakThai Combined Instruction Dataset v7',
    format: 'chatml',
    totalSamples,
    avgTokenLength,
    personasCovered: Array.from(personasSet).length > 0 ? Array.from(personasSet) : ['sakthai', 'sakking', 'sakjules'],
    hfRepoId: 'Sak-Family/sakthai-combined-v7',
    samples: samples.slice(0, 10),
  };
}

/**
 * Validates LoRA training hyperparameters against boundary invariants.
 */
export function validateLoraHyperparameters(config: Partial<LoraTrainingConfig>): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!config.modelName || !['sakthai-1.5b', 'sakthai-7b', 'qwen-2.5-coder-7b'].includes(config.modelName)) {
    errors.push('Invalid target modelName. Must be sakthai-1.5b, sakthai-7b, or qwen-2.5-coder-7b.');
  }

  if (typeof config.r !== 'number' || config.r < 4 || config.r > 64) {
    errors.push('LoRA rank (r) must be an integer between 4 and 64.');
  }

  if (typeof config.loraAlpha !== 'number' || config.loraAlpha < 8 || config.loraAlpha > 128) {
    errors.push('LoRA alpha must be an integer between 8 and 128.');
  }

  if (typeof config.learningRate !== 'number' || config.learningRate < 1e-6 || config.learningRate > 1e-2) {
    errors.push('Learning rate must be between 1e-6 and 1e-2.');
  }

  if (typeof config.numEpochs !== 'number' || config.numEpochs < 1 || config.numEpochs > 20) {
    errors.push('Number of epochs must be between 1 and 20.');
  }

  if (typeof config.batchSize !== 'number' || config.batchSize < 1 || config.batchSize > 32) {
    errors.push('Batch size must be between 1 and 32.');
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Spawns and tracks a new LoRA training run with simulated loss descent curve.
 */
export function spawnLoraTrainingJob(config: LoraTrainingConfig): LoraJobStatus {
  const validation = validateLoraHyperparameters(config);
  if (!validation.isValid) {
    throw new Error(`Hyperparameter validation failed: ${validation.errors.join(', ')}`);
  }

  const jobId = config.jobId || `job_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
  const totalSteps = config.numEpochs * 50;

  // Generate initial descending loss history
  const lossHistory: TrainingLossPoint[] = [];
  let currentLoss = 2.45;

  for (let step = 1; step <= 10; step++) {
    currentLoss = Math.max(0.35, currentLoss * 0.88 + (Math.random() * 0.05 - 0.025));
    lossHistory.push({
      epoch: Math.min(config.numEpochs, Math.ceil((step / totalSteps) * config.numEpochs)),
      step,
      loss: parseFloat(currentLoss.toFixed(4)),
      evalLoss: parseFloat((currentLoss * 1.05).toFixed(4)),
    });
  }

  const job: LoraJobStatus = {
    jobId,
    modelName: config.modelName,
    status: 'running',
    currentEpoch: 1,
    totalEpochs: config.numEpochs,
    currentStep: 10,
    totalSteps,
    lossHistory,
    currentLoss: parseFloat(currentLoss.toFixed(4)),
    checkpointPath: `checkpoints/${config.modelName}_lora_${jobId}/final_adapter`,
    startedAt: Date.now(),
  };

  activeJobs.set(jobId, job);
  return job;
}

export function getLoraJob(jobId: string): LoraJobStatus | undefined {
  return activeJobs.get(jobId);
}

export function listLoraJobs(): LoraJobStatus[] {
  // If empty, supply mock baseline job for demonstration
  if (activeJobs.size === 0) {
    const defaultJob: LoraJobStatus = {
      jobId: 'job_baseline_sakthai_7b',
      modelName: 'sakthai-7b',
      status: 'completed',
      currentEpoch: 3,
      totalEpochs: 3,
      currentStep: 150,
      totalSteps: 150,
      lossHistory: [
        { epoch: 1, step: 50, loss: 1.84, evalLoss: 1.92 },
        { epoch: 2, step: 100, loss: 0.95, evalLoss: 1.04 },
        { epoch: 3, step: 150, loss: 0.42, evalLoss: 0.49 },
      ],
      currentLoss: 0.42,
      checkpointPath: 'checkpoints/sakthai-7b_lora_run1/final_adapter',
      startedAt: Date.now() - 3600000,
      completedAt: Date.now() - 600000,
    };
    activeJobs.set(defaultJob.jobId, defaultJob);
  }

  return Array.from(activeJobs.values()).reverse();
}
