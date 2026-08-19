import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import AutoCyclePanel from '../components/AutoCyclePanel';
import { getAutoCycleData } from '../lib/autoCycle';

describe('AutoCyclePanel Component', () => {
  it('renders 6-Part Cycle Intelligence banner and persona stage selector', () => {
    const data = getAutoCycleData();
    render(<AutoCyclePanel data={data} />);

    expect(screen.getByText(/6-Part Cycle Intelligence & Operations Suite/i)).toBeDefined();
    expect(screen.getByText(/Step Next Stage/i)).toBeDefined();
    expect(screen.getByText(/Run Full Round/i)).toBeDefined();
  });
});
