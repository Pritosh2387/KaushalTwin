import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

const VARIANTS = {
  info: {
    container: 'bg-[#050505] border-white/20 text-white',
    icon: Info,
    iconColor: 'text-zinc-300',
  },
  success: {
    container: 'bg-[#050505] border-white/25 text-white',
    icon: CheckCircle2,
    iconColor: 'text-white',
  },
  warning: {
    container: 'bg-[#050505] border-white/20 text-zinc-200',
    icon: AlertTriangle,
    iconColor: 'text-zinc-300',
  },
  error: {
    container: 'bg-[#080808] border-white/25 text-zinc-100',
    icon: AlertCircle,
    iconColor: 'text-zinc-300',
  },
  ai: {
    container: 'bg-[#060608] border-white/30 text-white specular-top-edge',
    icon: Info,
    iconColor: 'text-white',
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
      className={`border rounded-none p-4 flex gap-3 text-sm relative transition-all ${current.container} ${className}`}
    >
      <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${current.iconColor}`} />
      <div className="flex-1">
        {title && <h5 className="font-semibold text-white mb-1 uppercase text-xs tracking-wider font-mono">{title}</h5>}
        <div className="text-zinc-300 leading-relaxed text-xs">{children}</div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="p-1 text-zinc-400 hover:text-white rounded transition-colors self-start cursor-pointer"
        >
          <X className="w-4 h-4" />
          <span className="sr-only">Dismiss</span>
        </button>
      )}
    </div>
  );
}

export default Alert;
