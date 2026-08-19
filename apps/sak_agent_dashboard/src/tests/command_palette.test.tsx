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

    expect(screen.getByRole('dialog', { name: /Command Palette/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Close command palette/i })).toBeDefined();
    expect(screen.getByPlaceholderText(/Type a command or jump to studio panel/i)).toBeDefined();
    expect(screen.getByText(/Agent War Room & Mesh Visualizer/i)).toBeDefined();
    expect(screen.getByText(/Autonomous Red Team Fuzzer/i)).toBeDefined();
    expect(screen.getByText(/Mutation Testing & Auto-Healer Studio/i)).toBeDefined();
  });

  it('triggers navigation callback on item selection click', () => {
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

  it('supports keyboard navigation via ArrowDown, ArrowUp, and Enter', () => {
    const handleNavigate = vi.fn();
    const handleClose = vi.fn();

    render(
      <CommandPaletteModal
        isOpen={true}
        onClose={handleClose}
        onNavigate={handleNavigate}
      />
    );

    const options = screen.getAllByRole('option');
    expect(options[0].getAttribute('aria-selected')).toBe('true');

    // Press ArrowDown to select second option (red_team)
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    expect(options[1].getAttribute('aria-selected')).toBe('true');

    // Press Enter to navigate to red_team
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(handleNavigate).toHaveBeenCalledWith('red_team');
    expect(handleClose).toHaveBeenCalled();
  });

  it('closes when clicking backdrop', () => {
    const handleNavigate = vi.fn();
    const handleClose = vi.fn();

    render(
      <CommandPaletteModal
        isOpen={true}
        onClose={handleClose}
        onNavigate={handleNavigate}
      />
    );

    const dialog = screen.getByRole('dialog', { name: /Command Palette/i });
    fireEvent.click(dialog);

    expect(handleClose).toHaveBeenCalled();
  });
});
