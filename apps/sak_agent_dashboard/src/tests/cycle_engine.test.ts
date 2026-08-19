import { describe, it, expect } from 'vitest';
import { CycleEngine } from '../lib/cycle/cycleEngine';

describe('CycleEngine', () => {
  it('initializes and manages state for all 6 Sak personas', () => {
    const states = CycleEngine.getAllPersonaStates();
    expect(Object.keys(states).length).toBe(6);
    expect(states['SakThai']).toBeDefined();
    expect(states['SakKing']).toBeDefined();
    expect(states['SakJules']).toBeDefined();
  });

  it('steps through cycle stages from dream to growth with artifacts', async () => {
    CycleEngine.resetCycle('SakJules');
    const state0 = CycleEngine.getPersonaState('SakJules');
    expect(state0.currentStage).toBe('dream');
    expect(state0.currentRound).toBe(1);

    const step1 = await CycleEngine.stepStage('SakJules', 'Refine CI mutation testing');
    expect(step1.previousStage).toBe('dream');
    expect(step1.nextStage).toBe('hope');
    expect(step1.artifact.stage).toBe('dream');
    expect(step1.artifact.type).toBe('vision_spec');

    const step2 = await CycleEngine.stepStage('SakJules');
    expect(step2.nextStage).toBe('care');
    expect(step2.artifact.type).toBe('decision_record');
  });

  it('executes a full 6-stage round sequentially', async () => {
    CycleEngine.resetCycle('SakSee');
    const steps = await CycleEngine.runFullCycle('SakSee', 'Automate AST security gate');
    expect(steps.length).toBe(6);

    const finalState = CycleEngine.getPersonaState('SakSee');
    expect(finalState.currentRound).toBe(2); // advanced to Round 2
    expect(finalState.currentStage).toBe('dream');
  });
});
