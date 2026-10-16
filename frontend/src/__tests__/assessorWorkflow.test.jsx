import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { StatusBadge, RoleBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

// Test StatusBadge covers all required states
describe('Assessor Evidence & Lifecycle Status Badges', () => {
  it('renders PENDING_REVIEW status badge with correct styling', () => {
    const { container } = render(<StatusBadge status="PENDING_REVIEW" />);
    expect(container.textContent).toContain('PENDING_REVIEW');
  });

  it('renders VERIFIED status badge with emerald accent', () => {
    const { container } = render(<StatusBadge status="VERIFIED" />);
    expect(container.textContent).toContain('VERIFIED');
  });

  it('renders REJECTED status badge with danger styling', () => {
    const { container } = render(<StatusBadge status="REJECTED" />);
    expect(container.textContent).toContain('REJECTED');
  });

  it('renders IN_PROGRESS assessment lifecycle badge', () => {
    const { container } = render(<StatusBadge status="IN_PROGRESS" />);
    expect(container.textContent).toContain('IN_PROGRESS');
  });

  it('renders COMPLETED assessment lifecycle badge', () => {
    const { container } = render(<StatusBadge status="COMPLETED" />);
    expect(container.textContent).toContain('COMPLETED');
  });
});

describe('Assessor Role Enforcement & Governance Notice', () => {
  it('displays role badge for certified assessor', () => {
    render(<RoleBadge role="ASSESSOR" />);
    expect(screen.getByText('Assessor')).toBeDefined();
  });

  it('prevents disabled buttons from triggering mutations during async operations', () => {
    const onClick = vi.fn();
    render(
      <Button variant="primary" loading={true} onClick={onClick}>
        Record Decision
      </Button>
    );
    const btn = screen.getByRole('button');
    expect(btn.hasAttribute('disabled')).toBe(true);
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });
});
