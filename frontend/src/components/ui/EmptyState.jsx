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
      className={`flex flex-col items-center justify-center p-8 sm:p-12 text-center bg-slate-50/50 rounded-2xl border border-dashed border-slate-300 ${className}`}
    >
      {Icon && (
        <div className="w-14 h-14 rounded-2xl bg-white border border-slate-200 shadow-sm flex items-center justify-center text-slate-400 mb-4">
          <Icon className="w-7 h-7 text-slate-500" />
        </div>
      )}
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      {description && (
        <p className="text-sm text-slate-500 max-w-sm mt-1.5 leading-relaxed">
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
