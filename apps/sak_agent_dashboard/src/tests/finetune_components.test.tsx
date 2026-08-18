import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TrainingConfigForm } from '../components/finetune/TrainingConfigForm';
import { TrainingJobMonitor } from '../components/finetune/TrainingJobMonitor';
import { DatasetCardViewer } from '../components/finetune/DatasetCardViewer';
import { FinetuningPanel } from '../components/FinetuningPanel';
import { DatasetCardSpec, LoraJobStatus } from '../lib/types';

describe('TrainingConfigForm Component', () => {
  it('renders hyperparameter inputs and submits valid configuration', () => {
    const onStart = vi.fn().mockResolvedValue(undefined);
    const { container } = render(<TrainingConfigForm onStartTraining={onStart} />);

    expect(screen.getByText(/LoRA Hyperparameter Configuration/i)).toBeDefined();
    expect(screen.getByText(/LoRA Rank \(r\)/i)).toBeDefined();

    const form = container.querySelector('form')!;
    fireEvent.submit(form);

    expect(onStart).toHaveBeenCalledWith({
      modelName: 'sakthai-7b',
      r: 16,
      loraAlpha: 32,
      learningRate: 0.0002,
      numEpochs: 3,
      batchSize: 4,
    });
  });
});

describe('TrainingJobMonitor Component', () => {
  it('renders running job progress and loss points', () => {
    const mockJobs: LoraJobStatus[] = [
      {
        jobId: 'job_monitor_1',
        modelName: 'sakthai-7b',
        status: 'running',
        currentEpoch: 2,
        totalEpochs: 4,
        currentStep: 100,
        totalSteps: 200,
        lossHistory: [{ epoch: 1, step: 50, loss: 1.45, evalLoss: 1.5 }],
        currentLoss: 1.45,
        startedAt: Date.now() - 10000,
      },
    ];

    render(<TrainingJobMonitor jobs={mockJobs} />);
    expect(screen.getByText(/job_monitor_1/i)).toBeDefined();
    expect(screen.getByText(/● Training \(Epoch 2\/4\)/i)).toBeDefined();
    expect(screen.getByText(/Current Loss:/i)).toBeDefined();
    expect(screen.getAllByText('1.45').length).toBeGreaterThanOrEqual(1);
  });
});

describe('DatasetCardViewer Component', () => {
  it('renders dataset metadata and ChatML samples', () => {
    const mockCard: DatasetCardSpec = {
      id: 'sakthai_combined_v7',
      name: 'SakThai Combined Instruction Dataset v7',
      format: 'chatml',
      totalSamples: 42,
      avgTokenLength: 320,
      personasCovered: ['sakthai', 'sakking'],
      hfRepoId: 'Sak-Family/sakthai-combined-v7',
      samples: [
        {
          instruction: 'Check AST rules',
          response: 'All AST rules passed.',
          persona: 'sakking',
        },
      ],
    };

    render(<DatasetCardViewer card={mockCard} stagedCount={42} />);
    expect(screen.getByText(/Dataset Card: SakThai Combined Instruction Dataset v7/i)).toBeDefined();
    expect(screen.getByText(/42 Staged Samples/i)).toBeDefined();
    expect(screen.getByText('Check AST rules')).toBeDefined();
    expect(screen.getByText('All AST rules passed.')).toBeDefined();
  });
});

describe('FinetuningPanel Component', () => {
  it('renders the complete fine-tuning studio panel', () => {
    render(<FinetuningPanel />);
    expect(screen.getByText('LoRA Fine-Tuning & Dataset Curation')).toBeDefined();
    expect(screen.getByText('Track 20260818')).toBeDefined();
    expect(screen.getByText(/LoRA Hyperparameter Configuration/i)).toBeDefined();
  });
});
