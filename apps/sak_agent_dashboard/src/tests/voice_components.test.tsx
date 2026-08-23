import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { VoiceStudioWorkbench } from '../components/telegram/VoiceStudioWorkbench';

describe('VoiceStudioWorkbench Component', () => {
  it('renders Gemini 2.0 Live Voice banner, persona voice selectors, and push to talk button', () => {
    render(<VoiceStudioWorkbench />);

    expect(screen.getByText(/Gemini 2.0 Multimodal Live Voice/i)).toBeDefined();
    expect(screen.getByText(/SakKing/i)).toBeDefined();
    expect(screen.getByText(/SakJules/i)).toBeDefined();
    expect(screen.getByText(/Push to Talk/i)).toBeDefined();
  });
});
