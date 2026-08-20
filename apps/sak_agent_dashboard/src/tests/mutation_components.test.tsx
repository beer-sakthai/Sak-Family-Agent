import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MutationStudioPanel } from '../components/mutation/MutationStudioPanel';

describe('MutationStudioPanel Component', () => {
  it('renders mutation score metrics banner and mutant inspector', () => {
    render(<MutationStudioPanel />);

    expect(screen.getByText(/Mutation Score/i)).toBeDefined();
    expect(screen.getByText(/Killed Mutants/i)).toBeDefined();
    expect(screen.getByText(/Surviving Mutants/i)).toBeDefined();
    expect(screen.getByText(/Injected AST Mutants/i)).toBeDefined();
  });
});
