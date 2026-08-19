import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { SemanticCachePanel } from '../components/cache/SemanticCachePanel';

describe('SemanticCachePanel Component', () => {
  it('renders top stats metrics banner and query tester', () => {
    render(<SemanticCachePanel />);

    expect(screen.getByText(/Cache Hit Ratio/i)).toBeDefined();
    expect(screen.getByText(/Total USD Saved/i)).toBeDefined();
    expect(screen.getByText(/Total Tokens Saved/i)).toBeDefined();
    expect(screen.getByText(/Interactive Semantic Cache Query Tester/i)).toBeDefined();
    expect(screen.getByText(/Active Semantic Cache Entries/i)).toBeDefined();
  });

  it('provides accessible labels for input and interactive action buttons', () => {
    render(<SemanticCachePanel />);

    expect(screen.getByLabelText(/Filter prompt patterns/i)).toBeDefined();
    expect(screen.getByLabelText(/Refresh Cache/i)).toBeDefined();

    const invalidateButtons = screen.getAllByLabelText(/Invalidate cache entry for/i);
    expect(invalidateButtons.length).toBeGreaterThan(0);
  });
});
