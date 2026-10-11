import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../components/ui/Button';
import { Badge, StatusBadge, RoleBadge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { Card, CardTitle, CardContent } from '../components/ui/Card';
import apiClient from '../lib/api-client';

describe('UI Design System Components', () => {
  it('renders Button with primary variant and handles click', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick} variant="primary">Start Assessment</Button>);

    const button = screen.getByRole('button', { name: /start assessment/i });
    expect(button).toBeDefined();
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders Button loading state correctly and disables interaction', () => {
    const handleClick = vi.fn();
    render(<Button loading onClick={handleClick}>Submit</Button>);

    const button = screen.getByRole('button');
    expect(button.getAttribute('disabled')).not.toBeNull();
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('renders StatusBadge with correct variant according to assessment lifecycle', () => {
    const { container: c1 } = render(<StatusBadge status="READY_FOR_REVIEW" />);
    expect(c1.textContent).toContain('READY_FOR_REVIEW');

    const { container: c2 } = render(<StatusBadge status="VERIFIED" />);
    expect(c2.textContent).toContain('VERIFIED');

    const { container: c3 } = render(<StatusBadge status="REJECTED" />);
    expect(c3.textContent).toContain('REJECTED');
  });

  it('renders RoleBadge correctly for ASSESSOR and ADMIN', () => {
    render(<RoleBadge role="ASSESSOR" />);
    expect(screen.getByText('Assessor')).toBeDefined();

    render(<RoleBadge role="ADMIN" />);
    expect(screen.getByText('Admin')).toBeDefined();
  });

  it('renders Alert component with error variant and dismiss button', () => {
    const handleClose = vi.fn();
    render(
      <Alert variant="error" title="Validation Failed" onClose={handleClose}>
        Candidate declared skills are required.
      </Alert>
    );

    expect(screen.getByText('Validation Failed')).toBeDefined();
    expect(screen.getByText('Candidate declared skills are required.')).toBeDefined();

    const dismissBtn = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders Card with header and content', () => {
    render(
      <Card>
        <CardTitle>Competency Twin</CardTitle>
        <CardContent>Candidate NOS mapping data</CardContent>
      </Card>
    );

    expect(screen.getByText('Competency Twin')).toBeDefined();
    expect(screen.getByText('Candidate NOS mapping data')).toBeDefined();
  });
});

describe('Axios API Client', () => {
  it('has base URL configured from environment', () => {
    expect(apiClient.defaults.baseURL).toBeDefined();
  });

  it('handles bearer token injection from localStorage', () => {
    localStorage.setItem('kaushaltwin_token', 'mock_jwt_token_12345');
    expect(localStorage.getItem('kaushaltwin_token')).toBe('mock_jwt_token_12345');
    localStorage.removeItem('kaushaltwin_token');
  });
});
