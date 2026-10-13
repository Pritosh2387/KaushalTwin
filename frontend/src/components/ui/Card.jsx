import React from 'react';

export function Card({ children, className = '', interactive = false, ...props }) {
  return (
    <div
      className={`bg-[#050505] rounded-none border border-white/10 relative overflow-hidden transition-all duration-200 specular-top-edge ${
        interactive
          ? 'hover:border-white/25 hover:bg-[#080808] hover:shadow-[0_4px_24px_rgba(0,0,0,0.8)] cursor-pointer'
          : 'shadow-[0_4px_20px_rgba(0,0,0,0.6)]'
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '', ...props }) {
  return (
    <div
      className={`p-5 sm:p-6 border-b border-white/10 flex items-center justify-between gap-4 bg-[#070707] ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '', ...props }) {
  return (
    <h3
      className={`text-base font-semibold text-white tracking-tight uppercase letter-spacing-wide ${className}`}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = '', ...props }) {
  return (
    <p
      className={`text-xs text-zinc-400 mt-1 font-light leading-relaxed ${className}`}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({ children, className = '', ...props }) {
  return (
    <div className={`p-5 sm:p-6 ${className}`} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = '', ...props }) {
  return (
    <div
      className={`p-5 sm:p-6 pt-0 border-t border-white/10 flex items-center gap-3 bg-[#030303] ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
