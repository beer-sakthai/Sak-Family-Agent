/**
 * Domain types for the 6-Part Cycle Intelligence & Autonomous Operations Suite.
 * (Dream -> Hope -> Care -> Joy -> Trust -> Growth / Observe -> Orient -> Decide -> Act -> Learn)
 */

export type CycleStageName = 'dream' | 'hope' | 'care' | 'joy' | 'trust' | 'growth';

export interface StageArtifact {
  stage: CycleStageName;
  title: string;
  type: 'vision_spec' | 'decision_record' | 'quality_audit' | 'release_bundle' | 'security_doctor' | 'memory_consolidation';
  content: string;
  timestamp: string;
}

export interface PersonaCycleState {
  persona: string;
  currentStage: CycleStageName;
  currentRound: number;
  maxRounds: number;
  status: 'IDLE' | 'EXECUTING' | 'WAITING_APPROVAL' | 'ROUND_COMPLETED' | 'CYCLE_FINISHED';
  activeTask?: string;
  lastExecutionMs: number;
  history: StageArtifact[];
}

export interface CycleExecutionStepResult {
  persona: string;
  previousStage: CycleStageName;
  nextStage: CycleStageName;
  round: number;
  artifact: StageArtifact;
  logMessage: string;
  durationMs: number;
  isCycleComplete: boolean;
}
