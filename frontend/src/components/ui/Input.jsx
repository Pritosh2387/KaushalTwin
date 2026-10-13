import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Input = forwardRef(function Input(
  {
    label,
    error,
    helperText,
    icon: Icon,
    className = '',
    required = false,
    id,
    ...props
  },
  ref
) {
  const inputId = id || props.name || Math.random().toString(36).substring(7);

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-[11px] font-mono text-zinc-300 uppercase tracking-widest mb-1.5"
        >
          {label} {required && <span className="text-zinc-500">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-500">
            <Icon className="h-4 w-4" />
          </div>
        )}
        <input
          ref={ref}
          id={inputId}
          className={twMerge(
            clsx(
              'block w-full rounded-none border text-sm transition-all duration-150',
              'placeholder:text-zinc-600 focus:outline-none focus:ring-1 focus:ring-white/20',
              Icon ? 'pl-9 pr-3' : 'px-3',
              'py-2',
              error
                ? 'border-zinc-400 text-white focus:border-white bg-[#080808]'
                : 'border-white/15 text-white focus:border-white bg-[#050505] hover:border-white/30',
              className
            )
          )}
          {...props}
        />
      </div>
      {error && <p className="mt-1.5 text-xs text-zinc-400 font-mono">{error}</p>}
      {!error && helperText && (
        <p className="mt-1.5 text-xs text-zinc-500 font-light">{helperText}</p>
      )}
    </div>
  );
});

export default Input;
