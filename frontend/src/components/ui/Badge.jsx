import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Badge({
  children,
  variant = 'slate',
  size = 'md',
  className = '',
  dot = false,
  ...props
}) {
  // Purely monochromatic luxury badge styles
  const variants = {
    slate: 'bg-[#0a0a0a] text-zinc-300 border-white/15',
    navy: 'bg-[#080808] text-white border-white/20',
    teal: 'bg-[#080808] text-zinc-200 border-white/25',
    cyan: 'bg-[#0a0a0a] text-white border-white/30',
    emerald: 'bg-[#09090b] text-white border-white/30 font-medium',
    amber: 'bg-[#080808] text-zinc-300 border-white/20',
    rose: 'bg-[#080808] text-zinc-400 border-white/20',
    purple: 'bg-[#080808] text-zinc-300 border-white/20',
  };

  const dotColors = {
    slate: 'bg-zinc-500',
    navy: 'bg-zinc-300',
    teal: 'bg-white',
    cyan: 'bg-white',
    emerald: 'bg-white',
    amber: 'bg-zinc-400',
    rose: 'bg-zinc-500',
    purple: 'bg-zinc-400',
  };

  const sizes = {
    sm: 'text-[9px] px-2 py-0.5 font-medium tracking-wider',
    md: 'text-[11px] px-2.5 py-1 font-semibold tracking-wider',
  };

  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1.5 rounded-none border shadow-none uppercase font-mono tracking-wider',
          variants[variant] || variants.slate,
          sizes[size] || sizes.md,
          className
        )
      )}
      {...props}
    >
      {dot && <span className={clsx('w-1 h-1 rounded-full', dotColors[variant] || 'bg-white')} />}
      {children}
    </span>
  );
}

export function StatusBadge({ status, size = 'md', className = '' }) {
  if (!status) return null;

  const normalized = String(status).toUpperCase();

  switch (normalized) {
    case 'VERIFIED':
    case 'COMPLETED':
    case 'CERTIFIED':
      return (
        <Badge variant="emerald" size={size} dot className={className}>
          {status}
        </Badge>
      );
    case 'IN_PROGRESS':
    case 'RUNNING':
      return (
        <Badge variant="cyan" size={size} dot className={className}>
          {status}
        </Badge>
      );
    case 'READY_FOR_REVIEW':
    case 'REVIEWED':
    case 'PENDING_REVIEW':
      return (
        <Badge variant="teal" size={size} dot className={className}>
          {status}
        </Badge>
      );
    case 'DRAFT':
    case 'PENDING':
    case 'NOT_STARTED':
    case 'UNVERIFIED':
      return (
        <Badge variant="amber" size={size} dot className={className}>
          {status}
        </Badge>
      );
    case 'REJECTED':
    case 'FAILED':
    case 'NOT_CERTIFIED':
      return (
        <Badge variant="rose" size={size} dot className={className}>
          {status}
        </Badge>
      );
    default:
      return (
        <Badge variant="slate" size={size} dot className={className}>
          {status}
        </Badge>
      );
  }
}

export function RoleBadge({ role, size = 'md', className = '' }) {
  if (!role) return null;

  const normalized = String(role).toUpperCase();

  switch (normalized) {
    case 'ADMIN':
      return (
        <Badge variant="navy" size={size} className={className}>
          Admin
        </Badge>
      );
    case 'ASSESSOR':
      return (
        <Badge variant="teal" size={size} className={className}>
          Assessor
        </Badge>
      );
    case 'WORKER':
      return (
        <Badge variant="slate" size={size} className={className}>
          Worker
        </Badge>
      );
    default:
      return (
        <Badge variant="slate" size={size} className={className}>
          {role}
        </Badge>
      );
  }
}

export default Badge;
