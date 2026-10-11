import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

const VARIANTS = {
  info: {
    container: 'bg-cyan-50 border-cyan-200 text-cyan-900',
    icon: Info,
    iconColor: 'text-cyan-600',
  },
  success: {
    container: 'bg-emerald-50 border-emerald-200 text-emerald-900',
    icon: CheckCircle2,
    iconColor: 'text-emerald-600',
  },
  warning: {
    container: 'bg-amber-50 border-amber-200 text-amber-900',
    icon: AlertTriangle,
    iconColor: 'text-amber-600',
  },
  error: {
    container: 'bg-rose-50 border-rose-200 text-rose-900',
    icon: AlertCircle,
    iconColor: 'text-rose-600',
  },
  ai: {
    container: 'bg-gradient-to-r from-cyan-50/80 to-blue-50/80 border-cyan-300 text-slate-900',
    icon: Info,
    iconColor: 'text-cyan-600',
  }
};

export function Alert({
  variant = 'info',
  title,
  children,
  onClose,
  className = ''
}) {
  const current = VARIANTS[variant] || VARIANTS.info;
  const Icon = current.icon;

  return (
    <div
      role="alert"
      className={`border rounded-xl p-4 flex gap-3 text-sm relative transition-all ${current.container} ${className}`}
    >
      <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${current.iconColor}`} />
      <div className="flex-1">
        {title && <h5 className="font-semibold mb-1 leading-snug">{title}</h5>}
        <div className="text-slate-700 leading-relaxed text-xs sm:text-sm">{children}</div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-slate-600 rounded transition-colors self-start"
        >
          <X className="w-4 h-4" />
          <span className="sr-only">Dismiss</span>
        </button>
      )}
    </div>
  );
}
