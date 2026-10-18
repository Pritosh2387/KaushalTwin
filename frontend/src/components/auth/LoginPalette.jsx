import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { X, Shield, Lock, Mail, ArrowRight, CheckCircle2, Eye, EyeOff } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Alert } from '../ui/Alert';
import { RoleBadge } from '../ui/Badge';

export function LoginPalette({ isOpen, onClose, initialRole = null, signedOut = false }) {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState(initialRole || 'ASSESSOR');

  // Sync initial role when opened or changed
  useEffect(() => {
    if (initialRole) {
      setSelectedRole(initialRole);
    }
  }, [initialRole]);

  // Handle ESC key to close
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

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const res = await login(email, password);
      if (res?.success === false) {
        setError(res.error || 'Incorrect email or password. Please try again.');
        return;
      }
      onClose();
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to sign in. Please verify your credentials or server status.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async (roleEmail, rolePass, roleName) => {
    setEmail(roleEmail);
    setPassword(rolePass);
    setSelectedRole(roleName);
    setError(null);
    setLoading(true);

    try {
      const res = await login(roleEmail, rolePass);
      if (res?.success === false) {
        setError(res.error || `Failed to sign in as ${roleName}.`);
        return;
      }
      onClose();
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err?.message || `Failed to sign in as ${roleName}.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/85 backdrop-blur-md transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Palette Container */}
      <div
        className="relative w-full max-w-lg bg-[#050505] rounded-none shadow-[0_25px_70px_rgba(0,0,0,0.95)] border border-white/20 z-10 flex flex-col specular-top-edge animate-in fade-in zoom-in-95 duration-150 overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-palette-title"
      >
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10 bg-[#070707]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 border border-white/30 bg-[#000000] flex items-center justify-center rotate-45 shadow-[0_0_15px_rgba(255,255,255,0.15)]">
              <div className="w-3.5 h-3.5 bg-white -rotate-45" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="login-palette-title" className="text-sm font-mono font-bold text-white tracking-widest uppercase">
                  Sign In to KaushalTwin
                </h2>
                <span className="text-[9px] font-mono px-1.5 py-0.5 bg-white/10 text-white border border-white/20">
                  RPL
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                Recognition of Prior Learning Intelligence Platform
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-zinc-400 hover:text-white hover:bg-white/10 rounded-none transition-colors cursor-pointer"
            aria-label="Close palette"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Notice for Signed Out Users */}
        {signedOut && (
          <div className="bg-emerald-950/40 border-b border-emerald-500/20 px-6 py-2.5 flex items-center gap-2 text-xs text-emerald-300 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>You have signed out securely. Select a role below to sign back in.</span>
          </div>
        )}

        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {error && (
            <Alert variant="error" className="text-xs" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Quick 1-Click Demo Accounts */}
          <div>
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider">
                1-Click Demo Access
              </span>
              <span className="text-[10px] font-mono text-zinc-500">Instant sign-in</span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickDemo('assessor@kaushaltwin.gov.in', 'assessor123', 'ASSESSOR')}
                className="group relative text-left p-3 bg-[#080808] border border-white/15 hover:border-white/40 hover:bg-[#111111] transition-all text-xs cursor-pointer disabled:opacity-50"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-xs font-semibold text-white">Assessor</span>
                  <RoleBadge role="ASSESSOR" size="sm" />
                </div>
                <div className="text-[10px] text-zinc-400 font-mono truncate">Evaluation Console</div>
                <div className="mt-2 text-[9px] font-mono text-zinc-500 group-hover:text-white flex items-center gap-1 transition-colors">
                  <span>Enter</span>
                  <ArrowRight className="w-2.5 h-2.5" />
                </div>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickDemo('worker@kaushaltwin.gov.in', 'worker123', 'WORKER')}
                className="group relative text-left p-3 bg-[#080808] border border-white/15 hover:border-white/40 hover:bg-[#111111] transition-all text-xs cursor-pointer disabled:opacity-50"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-xs font-semibold text-white">Worker</span>
                  <RoleBadge role="WORKER" size="sm" />
                </div>
                <div className="text-[10px] text-zinc-400 font-mono truncate">Candidate Twin</div>
                <div className="mt-2 text-[9px] font-mono text-zinc-500 group-hover:text-white flex items-center gap-1 transition-colors">
                  <span>Enter</span>
                  <ArrowRight className="w-2.5 h-2.5" />
                </div>
              </button>

              <button
                type="button"
                disabled={loading}
                onClick={() => handleQuickDemo('admin@kaushaltwin.gov.in', 'admin123', 'ADMIN')}
                className="group relative text-left p-3 bg-[#080808] border border-white/15 hover:border-white/40 hover:bg-[#111111] transition-all text-xs cursor-pointer disabled:opacity-50"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-xs font-semibold text-white">Admin</span>
                  <RoleBadge role="ADMIN" size="sm" />
                </div>
                <div className="text-[10px] text-zinc-400 font-mono truncate">Governance</div>
                <div className="mt-2 text-[9px] font-mono text-zinc-500 group-hover:text-white flex items-center gap-1 transition-colors">
                  <span>Enter</span>
                  <ArrowRight className="w-2.5 h-2.5" />
                </div>
              </button>
            </div>
          </div>

          {/* Divider */}
          <div className="relative flex items-center">
            <div className="flex-grow border-t border-white/10" />
            <span className="flex-shrink mx-3 text-[10px] font-mono uppercase tracking-widest text-zinc-500">
              Or Sign In With Email
            </span>
            <div className="flex-grow border-t border-white/10" />
          </div>

          {/* Login Form */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-mono text-zinc-300 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  autoComplete="email"
                  required
                  placeholder="assessor@kaushaltwin.gov.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-[#000000] border border-white/20 text-white placeholder-zinc-600 font-mono text-xs focus:outline-none focus:border-white transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono text-zinc-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2 bg-[#000000] border border-white/20 text-white placeholder-zinc-600 font-mono text-xs focus:outline-none focus:border-white transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full justify-center py-2.5 font-mono text-xs tracking-wider uppercase mt-2"
              loading={loading}
            >
              <span>Sign In to Workspace ↗</span>
            </Button>
          </form>

          {/* Registration Link & Governance Footer */}
          <div className="pt-3 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <button
              type="button"
              onClick={() => {
                onClose();
                navigate('/register');
              }}
              className="text-zinc-400 hover:text-white font-sans text-xs transition-colors cursor-pointer"
            >
              Don't have an account? <span className="text-white underline">Register Candidate</span>
            </button>
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
              <Shield className="w-3 h-3 text-zinc-400" />
              <span>Assessor Governance</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPalette;
