import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export const Select = forwardRef(function Select(
  {
    label,
    options = [],
    error,
    helperText,
    className = '',
    required = false,
    id,
    placeholder = 'Select an option...',
    ...props
  },
  ref
) {
  const selectId = id || props.name || Math.random().toString(36).substring(7);

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-[11px] font-mono text-zinc-300 uppercase tracking-widest mb-1.5"
        >
          {label} {required && <span className="text-zinc-500">*</span>}
        </label>
      )}
      <div className="relative">
        <select
          ref={ref}
          id={selectId}
          className={twMerge(
            clsx(
              'block w-full rounded-none border text-sm transition-all duration-150 appearance-none bg-[#050505]',
              'px-3 py-2 pr-8',
              'focus:outline-none focus:ring-1 focus:ring-white/20',
              error
                ? 'border-zinc-400 text-white focus:border-white'
                : 'border-white/15 text-white focus:border-white hover:border-white/30',
              className
            )
          )}
          {...props}
        >
          {placeholder && <option value="" className="bg-[#0a0a0a] text-zinc-400">{placeholder}</option>}
          {options.map((opt) => (
            <option
              key={typeof opt === 'string' ? opt : opt.value}
              value={typeof opt === 'string' ? opt : opt.value}
              className="bg-[#0a0a0a] text-white"
            >
              {typeof opt === 'string' ? opt : opt.label}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-zinc-400">
          <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
          </svg>
        </div>
      </div>
      {error && <p className="mt-1.5 text-xs text-zinc-400 font-mono">{error}</p>}
      {!error && helperText && (
        <p className="mt-1.5 text-xs text-zinc-500 font-light">{helperText}</p>
      )}
    </div>
  );
});

export default Select;
