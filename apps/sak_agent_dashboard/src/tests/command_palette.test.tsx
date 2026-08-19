import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CommandPaletteModal } from '../components/CommandPaletteModal';

describe('CommandPaletteModal Component', () => {
  it('renders fuzzy search and studio navigation shortcuts when open with ARIA attributes', () => {
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
    expect(screen.getByLabelText(/Close command palette/i)).toBeDefined();
    expect(screen.getByRole('listbox', { name: /Command suggestions/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Close command palette/i })).toBeDefined();
    expect(screen.getByPlaceholderText(/Type a command or jump to studio panel/i)).toBeDefined();
    expect(screen.getByText(/Agent War Room & Mesh Visualizer/i)).toBeDefined();
    expect(screen.getByText(/Autonomous Red Team Fuzzer/i)).toBeDefined();
    expect(screen.getByText(/Mutation Testing & Auto-Healer Studio/i)).toBeDefined();
  });

  it('triggers navigation callback on item selection click', () => {
  it('triggers navigation callback on item click selection', () => {
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

  it('supports keyboard navigation with ArrowDown, ArrowUp, and Enter', () => {
  it('supports ArrowDown, ArrowUp and Enter keyboard navigation', () => {
    const handleNavigate = vi.fn();
    const handleClose = vi.fn();

    render(
      <CommandPaletteModal
        isOpen={true}
        onClose={handleClose}
        onNavigate={handleNavigate}
      />
    );

    // Initial selected item is the first one (war_room)
    // Press ArrowDown to select red_team (index 1)
    fireEvent.keyDown(window, { key: 'ArrowDown' });

    // Press Enter to execute selection
    fireEvent.keyDown(window, { key: 'Enter' });

    expect(handleNavigate).toHaveBeenCalledWith('red_team');
    expect(handleClose).toHaveBeenCalled();
  });

  it('closes when close button is clicked', () => {
    const handleNavigate = vi.fn();
    const handleClose = vi.fn();

    render(
      <CommandPaletteModal
        isOpen={true}
        onClose={handleClose}
        onNavigate={handleNavigate}
      />
    );

    const closeButton = screen.getByLabelText(/Close command palette/i);
    fireEvent.click(closeButton);

    expect(handleClose).toHaveBeenCalled();
  });
    const options = screen.getAllByRole('option');
    expect(options[0]).toHaveAttribute('aria-selected', 'true');

    // Press ArrowDown to select second option
    fireEvent.keyDown(window, { key: 'ArrowDown' });
    expect(options[1]).toHaveAttribute('aria-selected', 'true');

    // Press Enter to activate second option
    fireEvent.keyDown(window, { key: 'Enter' });
    expect(handleNavigate).toHaveBeenCalledWith('red_team');
    expect(handleClose).toHaveBeenCalled();
  });
});
