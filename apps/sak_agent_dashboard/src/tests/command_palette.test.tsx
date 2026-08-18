import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CommandPaletteModal } from '../components/CommandPaletteModal';

describe('CommandPaletteModal Component', () => {
  it('renders fuzzy search and studio navigation shortcuts when open', () => {
    const handleNavigate = vi.fn();
    const handleClose = vi.fn();

    render(
      <CommandPaletteModal
        isOpen={true}
        onClose={handleClose}
        onNavigate={handleNavigate}
      />
    );

    expect(screen.getByPlaceholderText(/Type a command or jump to studio panel/i)).toBeDefined();
    expect(screen.getByText(/Agent War Room & Mesh Visualizer/i)).toBeDefined();
    expect(screen.getByText(/Autonomous Red Team Fuzzer/i)).toBeDefined();
    expect(screen.getByText(/Mutation Testing & Auto-Healer Studio/i)).toBeDefined();
  });

  it('triggers navigation callback on item selection', () => {
    const handleNavigate = vi.fn();
    const handleClose = vi.fn();

    render(
      <CommandPaletteModal
        isOpen={true}
        onClose={handleClose}
        onNavigate={handleNavigate}
      />
    );

    const redTeamOption = screen.getByText(/Autonomous Red Team Fuzzer/i);
    fireEvent.click(redTeamOption);

    expect(handleNavigate).toHaveBeenCalledWith('red_team');
    expect(handleClose).toHaveBeenCalled();
  });
});
