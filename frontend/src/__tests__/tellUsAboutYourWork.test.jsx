import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TellUsAboutYourWork } from '../components/worker/TellUsAboutYourWork';
import { workersApi } from '../api/workers.api';

vi.mock('../api/workers.api', () => ({
  workersApi: {
    getMyProfile: vi.fn().mockResolvedValue({
      id: 'mock-worker-1',
      full_name: 'Ramesh Kumar',
      trade: 'Electrical Installation',
      work_narrative: 'Existing saved narrative about domestic wiring and MCBs.',
      declared_skills: ['Domestic Wiring'],
    }),
    saveNarrative: vi.fn().mockResolvedValue({
      id: 'mock-worker-1',
      work_narrative: 'Updated work narrative text.',
    }),
    analyzeNarrative: vi.fn().mockResolvedValue({
      worker_id: 'mock-worker-1',
      trade: 'electrician',
      language: 'en',
      narrative: 'Updated work narrative text.',
      extracted_skills: [
        { skill_name: 'house wiring', confidence: 0.9, trade_context: 'electrician', evidence_text: 'wiring' },
      ],
      nos_mappings: [
        {
          skill: { skill_name: 'house wiring' },
          candidates: [{ nos_id: 'ELE/N5801', title: 'Install Electrical Wiring Systems', similarity: 0.85 }],
        },
      ],
      disclaimer: 'AI suggestions are strictly advisory and awaiting assessor review.',
    }),
    updateMyProfile: vi.fn().mockResolvedValue({}),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('TellUsAboutYourWork Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders section title, guidance copy, and microphone button', async () => {
    render(<TellUsAboutYourWork />, { wrapper: createWrapper() });

    expect(screen.getByText(/tell us about your work/i)).toBeDefined();
    expect(
      screen.getByText(/you have skills worth recognizing/i)
    ).toBeDefined();

    const micBtn = screen.getByRole('button', { name: /speak about your work/i });
    expect(micBtn).toBeDefined();
  });

  it('allows typing into the text area and updates character count', async () => {
    render(<TellUsAboutYourWork />, { wrapper: createWrapper() });

    const textarea = screen.getByRole('textbox', { name: /your work experience narrative/i });
    expect(textarea).toBeDefined();

    fireEvent.change(textarea, {
      target: { value: 'I have six years of experience repairing electrical transformers.' },
    });

    expect(textarea.value).toBe(
      'I have six years of experience repairing electrical transformers.'
    );
    expect(screen.getByText(/65 characters/i)).toBeDefined();
  });

  it('provides language selection for English (India) and Hindi (India)', () => {
    render(<TellUsAboutYourWork />, { wrapper: createWrapper() });

    const langSelect = screen.getByLabelText(/speech recognition language/i);
    expect(langSelect).toBeDefined();

    fireEvent.change(langSelect, { target: { value: 'hi-IN' } });
    expect(langSelect.value).toBe('hi-IN');
  });

  it('validates empty/short text when clicking Save My Experience', async () => {
    render(<TellUsAboutYourWork />, { wrapper: createWrapper() });

    const textarea = screen.getByRole('textbox', { name: /your work experience narrative/i });
    fireEvent.change(textarea, { target: { value: 'ab' } });

    const saveBtn = screen.getByRole('button', { name: /save my experience/i });
    fireEvent.click(saveBtn);

    expect(
      await screen.findByText(/please provide at least a few words describing your work experience/i)
    ).toBeDefined();
  });

  it('invokes saveNarrative API on save and displays success message', async () => {
    render(<TellUsAboutYourWork />, { wrapper: createWrapper() });

    const textarea = screen.getByRole('textbox', { name: /your work experience narrative/i });
    fireEvent.change(textarea, {
      target: { value: 'I install MCB distribution boards and domestic wiring.' },
    });

    const saveBtn = screen.getByRole('button', { name: /save my experience/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(workersApi.saveNarrative).toHaveBeenCalledWith(
        'I install MCB distribution boards and domestic wiring.'
      );
    });
  });

  it('invokes analyzeNarrative API on Analyze My Skills and renders advisory results', async () => {
    render(<TellUsAboutYourWork />, { wrapper: createWrapper() });

    const textarea = screen.getByRole('textbox', { name: /your work experience narrative/i });
    fireEvent.change(textarea, {
      target: { value: 'I install MCB distribution boards and domestic wiring.' },
    });

    const analyzeBtn = screen.getByRole('button', { name: /analyze my skills/i });
    fireEvent.click(analyzeBtn);

    await waitFor(() => {
      expect(workersApi.analyzeNarrative).toHaveBeenCalled();
    });

    expect(
      await screen.findByText(/advisory · awaiting assessor review/i)
    ).toBeDefined();
    expect(screen.getAllByText(/house wiring/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/ELE\/N5801/i)).toBeDefined();
  });

  it('displays fallback notice gracefully when Web Speech API is absent', () => {
    const originalSpeechRecognition = window.SpeechRecognition;
    const originalWebkit = window.webkitSpeechRecognition;
    delete window.SpeechRecognition;
    delete window.webkitSpeechRecognition;

    render(<TellUsAboutYourWork />, { wrapper: createWrapper() });

    expect(
      screen.getByText(/voice dictation is not supported in this browser/i)
    ).toBeDefined();

    window.SpeechRecognition = originalSpeechRecognition;
    window.webkitSpeechRecognition = originalWebkit;
  });
});
