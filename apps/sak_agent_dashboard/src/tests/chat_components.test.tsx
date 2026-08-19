import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { AgentThoughtBlock } from '../components/chat/AgentThoughtBlock';
import { ToolExecutionCard } from '../components/chat/ToolExecutionCard';
import { PersonaSelector } from '../components/chat/PersonaSelector';
import { SynthesisCard } from '../components/chat/SynthesisCard';
import { ChatStudioPanel } from '../components/ChatStudioPanel';

describe('AgentThoughtBlock Component', () => {
  it('renders persona name and collapsible reasoning text with proper ARIA accessibility', () => {
    render(<AgentThoughtBlock persona="sakking" thought="Analyzing AST security invariants..." />);
    expect(screen.getByText(/Sakking's Reasoning Process/i)).toBeDefined();
    expect(screen.getByText(/Analyzing AST security invariants/i)).toBeDefined();

    const button = screen.getByRole('button', { name: "Toggle Sakking's reasoning process" });
    expect(button.getAttribute('aria-expanded')).toBe('true');

    fireEvent.click(button);
    expect(button.getAttribute('aria-expanded')).toBe('false');
    expect(screen.queryByText(/Analyzing AST security invariants/i)).toBeNull();
  });
});

describe('ToolExecutionCard Component', () => {
  it('renders safe AST badge and arguments', () => {
    render(
      <ToolExecutionCard
        persona="sakking"
        tool="ast_sandbox"
        args={{ code: 'print("hello")' }}
        output="PASS"
        astSafe={true}
      />
    );

    expect(screen.getByText('ast_sandbox')).toBeDefined();
    expect(screen.getByText('✓ AST Safe')).toBeDefined();
    expect(screen.getByText('PASS')).toBeDefined();
  });

  it('renders approval intercept and calls onApprove', () => {
    const onApprove = vi.fn();
    render(
      <ToolExecutionCard
        persona="sakjules"
        tool="git_push"
        args={{ branch: 'main', force: true }}
        astSafe={false}
        requiresApproval={true}
        onApprove={onApprove}
      />
    );

    expect(screen.getByText('⚠️ AST Warning')).toBeDefined();
    expect(screen.getByText(/Guardrail Intercept:/i)).toBeDefined();

    const approveBtn = screen.getByRole('button', { name: /Approve & Run/i });
    fireEvent.click(approveBtn);
    expect(onApprove).toHaveBeenCalled();
  });
});

describe('PersonaSelector Component', () => {
  it('renders all 6 personas and allows toggling and preset selection', () => {
    const onSelectPreset = vi.fn();
    const onTogglePersona = vi.fn();

    render(
      <PersonaSelector
        selectedPreset="cloud_powerhouse"
        activePersonas={['sakthai', 'sakking', 'sakjules']}
        onSelectPreset={onSelectPreset}
        onTogglePersona={onTogglePersona}
      />
    );

    expect(screen.getByText('SakThai')).toBeDefined();
    expect(screen.getByText('SakKing')).toBeDefined();
    expect(screen.getByText('SakSee')).toBeDefined();
    expect(screen.getByText('SakJules')).toBeDefined();
    expect(screen.getByText('SakSit')).toBeDefined();
    expect(screen.getByText('SakTan')).toBeDefined();

    // Click offline preset
    const offlineBtn = screen.getByText('100% Offline / Local');
    fireEvent.click(offlineBtn);
    expect(onSelectPreset).toHaveBeenCalledWith('local_offline');

    // Toggle persona
    const seeCard = screen.getByText('SakSee');
    fireEvent.click(seeCard);
    expect(onTogglePersona).toHaveBeenCalledWith('saksee');
  });
});

describe('SynthesisCard Component', () => {
  it('renders supervisor synthesis and handles Star for LoRA training', () => {
    const onStar = vi.fn();
    render(
      <SynthesisCard
        content="Actionable consensus synthesized across 3 personas."
        sessionId="session_test_789"
        onStarForTraining={onStar}
      />
    );

    expect(screen.getByText(/Supervisor Final Consensus \(SakThai\)/i)).toBeDefined();
    expect(screen.getByText(/Actionable consensus synthesized/i)).toBeDefined();

    const starBtn = screen.getByRole('button', { name: /Star for LoRA Training/i });
    fireEvent.click(starBtn);
    expect(onStar).toHaveBeenCalled();
    expect(screen.getByText('⭐ Staged in LoRA Dataset Pool')).toBeDefined();
  });
});

describe('ChatStudioPanel Component', () => {
  it('renders the header banner and studio interface', () => {
    render(<ChatStudioPanel />);
    expect(screen.getByText('Collaborative Chat Arena & Studio')).toBeDefined();
    expect(screen.getByText('Track 20260818')).toBeDefined();
    expect(screen.getByText('Team Preset & Persona Matrix')).toBeDefined();
  });
});
