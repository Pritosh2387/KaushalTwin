import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = 'max-w-xl',
  className = ''
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-md transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        className={`relative w-full ${maxWidth} bg-[#050505] rounded-none shadow-[0_20px_60px_rgba(0,0,0,0.9)] border border-white/15 z-10 flex flex-col max-h-[90vh] specular-top-edge animate-in fade-in zoom-in-95 duration-150 ${className}`}
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-white/10 bg-[#070707]">
          <div>
            {title && (
              <h2 className="text-lg font-bold text-white uppercase tracking-wider font-mono">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-xs text-zinc-400 mt-1 font-light leading-relaxed">{description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-zinc-400 hover:text-white hover:bg-white/10 rounded-none transition-colors ml-4 cursor-pointer"
          >
            <X className="w-5 h-5" />
            <span className="sr-only">Close modal</span>
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 overflow-y-auto flex-1">{children}</div>
      </div>
    </div>
  );
}

export default Modal;
