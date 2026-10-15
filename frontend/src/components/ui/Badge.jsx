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
  // Refined dark technical aesthetic with subtle semantic accents
  const variants = {
    slate: 'bg-zinc-900/60 text-zinc-300 border-zinc-700/50',
    navy: 'bg-blue-950/40 text-blue-300 border-blue-500/30',
    teal: 'bg-teal-950/40 text-teal-300 border-teal-500/30',
    cyan: 'bg-cyan-950/40 text-cyan-300 border-cyan-500/30',
    emerald: 'bg-emerald-950/50 text-emerald-300 border-emerald-500/40 font-medium',
    amber: 'bg-amber-950/40 text-amber-300 border-amber-500/30',
    rose: 'bg-rose-950/40 text-rose-300 border-rose-500/30',
    purple: 'bg-purple-950/40 text-purple-300 border-purple-500/30',
  };

  const dotColors = {
    slate: 'bg-zinc-400',
    navy: 'bg-blue-400',
    teal: 'bg-teal-400',
    cyan: 'bg-cyan-400',
    emerald: 'bg-emerald-400',
    amber: 'bg-amber-400',
    rose: 'bg-rose-400',
    purple: 'bg-purple-400',
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
        <Badge variant="purple" size={size} className={className}>
          Admin
        </Badge>
      );
    case 'ASSESSOR':
      return (
        <Badge variant="cyan" size={size} className={className}>
          Assessor
        </Badge>
      );
    case 'WORKER':
      return (
        <Badge variant="emerald" size={size} className={className}>
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
