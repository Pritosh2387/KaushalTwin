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
  const variants = {
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    navy: 'bg-navy-900/10 text-navy-800 border-navy-800/20',
    teal: 'bg-teal-50 text-teal-700 border-teal-200',
    cyan: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    rose: 'bg-rose-50 text-rose-700 border-rose-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
  };

  const dotColors = {
    slate: 'bg-slate-400',
    navy: 'bg-navy-700',
    teal: 'bg-teal-500',
    cyan: 'bg-cyan-500',
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    rose: 'bg-rose-500',
    purple: 'bg-purple-500',
  };

  const sizes = {
    sm: 'text-[10px] px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-semibold',
  };

  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1.5 rounded-full border shadow-2xs uppercase tracking-wider',
          variants[variant],
          sizes[size],
          className
        )
      )}
      {...props}
    >
      {dot && <span className={clsx('w-1.5 h-1.5 rounded-full', dotColors[variant])} />}
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
    case 'ABSTAINED':
    case 'ABSTAIN':
      return (
        <Badge variant="purple" size={size} dot className={className}>
          Abstained
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
        <Badge variant="teal" size={size} className={className}>
          Candidate
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
