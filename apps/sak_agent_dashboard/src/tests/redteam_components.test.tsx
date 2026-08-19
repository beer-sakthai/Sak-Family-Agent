import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { RedTeamStudioPanel } from '../components/redteam/RedTeamStudioPanel';

describe('RedTeamStudioPanel Component', () => {
  it('renders Fleet Robustness Score banner and attack workbench', () => {
    render(<RedTeamStudioPanel />);

    expect(screen.getByText(/Fleet Robustness Score/i)).toBeDefined();
    expect(screen.getByText(/Threats Blocked/i)).toBeDefined();
    expect(screen.getByText(/Attack Vector Defenses/i)).toBeDefined();
    expect(screen.getByText(/Interactive Attack Workbench/i)).toBeDefined();
  });
});
