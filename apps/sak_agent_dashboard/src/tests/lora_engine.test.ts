import { describe, it, expect } from 'vitest';
import {
  formatToChatML,
  formatToAlpaca,
  generateDatasetCardSpec,
  validateLoraHyperparameters,
  spawnLoraTrainingJob,
  listLoraJobs,
} from '../lib/learning/lora_engine';

describe('LoRA Engine & Dataset Formatter', () => {
  it('formats prompt-response pairs into ChatML standard syntax', () => {
    const chatml = formatToChatML('Analyze AST security', 'AST scan clean.', 'sakking');
    expect(chatml).toContain('<|im_start|>system');
    expect(chatml).toContain('sakking');
    expect(chatml).toContain('<|im_start|>user\nAnalyze AST security<|im_end|>');
    expect(chatml).toContain('<|im_start|>assistant\nAST scan clean.<|im_end|>');
  });

  it('formats into Alpaca JSON schema', () => {
    const alpaca = formatToAlpaca('Run CI test', 'Passed 100%');
    expect(alpaca.instruction).toBe('Run CI test');
    expect(alpaca.input).toBe('');
    expect(alpaca.output).toBe('Passed 100%');
  });

  it('generates a Hugging Face dataset card specification', () => {
    const card = generateDatasetCardSpec();
    expect(card.id).toBe('sakthai_combined_v7');
    expect(card.hfRepoId).toBe('Sak-Family/sakthai-combined-v7');
    expect(card.format).toBe('chatml');
    expect(card.personasCovered.length).toBeGreaterThan(0);
  });

  it('validates hyperparameter bounds correctly', () => {
    const validRes = validateLoraHyperparameters({
      modelName: 'sakthai-7b',
      r: 16,
      loraAlpha: 32,
      learningRate: 2e-4,
      numEpochs: 3,
      batchSize: 4,
    });
    expect(validRes.isValid).toBe(true);
    expect(validRes.errors).toHaveLength(0);

    const invalidRes = validateLoraHyperparameters({
      modelName: 'sakthai-7b',
      r: 1, // too small
      loraAlpha: 200, // too big
      learningRate: 5.0, // way too big
      numEpochs: 0, // invalid
      batchSize: 64, // too big
    });
    expect(invalidRes.isValid).toBe(false);
    expect(invalidRes.errors.length).toBeGreaterThanOrEqual(4);
  });

  it('spawns training job with valid initial loss history curve', () => {
    const job = spawnLoraTrainingJob({
      jobId: 'job_test_123',
      modelName: 'sakthai-1.5b',
      datasetPath: 'staged.jsonl',
      r: 8,
      loraAlpha: 16,
      loraDropout: 0.05,
      learningRate: 1e-4,
      numEpochs: 2,
      batchSize: 2,
      targetModules: ['q_proj', 'v_proj'],
      outputDir: 'checkpoints/test',
    });

    expect(job.jobId).toBe('job_test_123');
    expect(job.status).toBe('running');
    expect(job.lossHistory.length).toBeGreaterThan(0);
    expect(job.currentLoss).toBeLessThan(3.0);

    const jobs = listLoraJobs();
    expect(jobs.some((j) => j.jobId === 'job_test_123')).toBe(true);
  });
});
