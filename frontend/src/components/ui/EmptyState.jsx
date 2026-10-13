import React from 'react';
import { Button } from './Button';

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  className = ''
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 sm:p-12 text-center bg-[#050505] rounded-none border border-dashed border-white/15 ${className}`}
    >
      {Icon && (
        <div className="w-12 h-12 rounded-none bg-[#09090b] border border-white/20 flex items-center justify-center text-zinc-300 mb-4">
          <Icon className="w-5 h-5 text-zinc-200" />
        </div>
      )}
      <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">{title}</h3>
      {description && (
        <p className="text-xs text-zinc-400 max-w-sm mt-1.5 leading-relaxed font-light">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <div className="mt-5">
          <Button onClick={onAction} variant="outline" size="sm">
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
}

export default EmptyState;
