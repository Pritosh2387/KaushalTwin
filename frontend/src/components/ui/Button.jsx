import React from 'react';
import { Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  isLoading = false,
  disabled = false,
  className = '',
  icon: Icon,
  type = 'button',
  ...props
}) {
  const isSpinning = loading || isLoading;

  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-all duration-150 focus:outline-none focus:ring-1 focus:ring-white/40 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer active:scale-[0.98] select-none uppercase tracking-wider text-xs';

  const variants = {
    primary:
      'bg-white text-black font-semibold hover:bg-zinc-200 border border-white light-sweep-btn rounded-sm shadow-[0_0_15px_rgba(255,255,255,0.15)]',
    secondary:
      'bg-[#050505] text-white border border-white/20 hover:border-white/50 hover:bg-[#0c0c0e] rounded-sm',
    outline:
      'border border-white/20 text-zinc-300 hover:text-white hover:border-white/40 bg-transparent rounded-sm',
    ghost:
      'text-zinc-400 hover:text-white hover:bg-white/5 rounded-sm',
    danger:
      'bg-[#0a0a0a] text-zinc-300 border border-white/20 hover:border-white/50 hover:text-white rounded-sm',
    ai:
      'bg-[#09090b] text-white border border-white/30 hover:border-white/60 hover:bg-[#121216] font-semibold rounded-sm light-sweep-btn shadow-[0_0_12px_rgba(255,255,255,0.08)]',
    success:
      'bg-[#0a0a0a] text-zinc-200 border border-white/20 hover:border-white/50 hover:text-white rounded-sm',
  };

  const sizes = {
    sm: 'text-[10px] px-3 py-1.5 gap-1.5',
    md: 'text-xs px-4 py-2 gap-2',
    lg: 'text-sm px-6 py-2.5 gap-2.5',
  };

  return (
    <button
      type={type}
      disabled={disabled || isSpinning}
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      {...props}
    >
      {isSpinning ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : Icon ? (
        <Icon className="w-3.5 h-3.5 shrink-0" />
      ) : null}
      {children}
    </button>
  );
}

export default Button;
