import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPalette } from '../components/auth/LoginPalette';
import * as AuthContextModule from '../context/AuthContext';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPalette Component', () => {
  const mockLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      user: null,
      logout: vi.fn(),
    });
  });

  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <MemoryRouter>
        <LoginPalette isOpen={false} onClose={vi.fn()} />
      </MemoryRouter>
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders login palette with demo buttons and inputs when isOpen is true', () => {
    render(
      <MemoryRouter>
        <LoginPalette isOpen={true} onClose={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByText(/Sign In to KaushalTwin/i)).toBeDefined();
    expect(screen.getByText(/1-Click Demo Access/i)).toBeDefined();
    expect(screen.getAllByText('Assessor').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Worker').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Admin').length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText('assessor@kaushaltwin.gov.in')).toBeDefined();
  });

  it('displays signed-out safety banner when signedOut prop is true', () => {
    render(
      <MemoryRouter>
        <LoginPalette isOpen={true} onClose={vi.fn()} signedOut={true} />
      </MemoryRouter>
    );

    expect(screen.getByText(/You have signed out securely/i)).toBeDefined();
  });

  it('calls onClose when close button is clicked', () => {
    const handleClose = vi.fn();
    render(
      <MemoryRouter>
        <LoginPalette isOpen={true} onClose={handleClose} />
      </MemoryRouter>
    );

    const closeBtn = screen.getByRole('button', { name: /close palette/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('executes login and navigates to dashboard on successful credentials submission', async () => {
    mockLogin.mockResolvedValueOnce({ success: true, user: { role: 'ASSESSOR' } });
    const handleClose = vi.fn();

    render(
      <MemoryRouter>
        <LoginPalette isOpen={true} onClose={handleClose} />
      </MemoryRouter>
    );

    const emailInput = screen.getByPlaceholderText('assessor@kaushaltwin.gov.in');
    const passwordInput = screen.getByPlaceholderText('••••••••');
    const submitBtn = screen.getByRole('button', { name: /sign in to workspace/i });

    fireEvent.change(emailInput, { target: { value: 'assessor@kaushaltwin.gov.in' } });
    fireEvent.change(passwordInput, { target: { value: 'assessor123' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('assessor@kaushaltwin.gov.in', 'assessor123');
      expect(handleClose).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });

  it('triggers 1-click quick demo login for Worker role', async () => {
    mockLogin.mockResolvedValueOnce({ success: true, user: { role: 'WORKER' } });
    const handleClose = vi.fn();

    render(
      <MemoryRouter>
        <LoginPalette isOpen={true} onClose={handleClose} />
      </MemoryRouter>
    );

    const workerDemoBtn = screen.getByText('Candidate Twin').closest('button');
    expect(workerDemoBtn).not.toBeNull();
    fireEvent.click(workerDemoBtn);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('worker@kaushaltwin.gov.in', 'worker123');
      expect(handleClose).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });
});
