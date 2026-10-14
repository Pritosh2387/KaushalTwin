import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Shield, ArrowRight, Compass } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
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
      navigate(from, { replace: true });
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

  const handleDemoFill = (roleEmail, rolePass) => {
    setEmail(roleEmail);
    setPassword(rolePass);
  };

  return (
    <div className="min-h-screen bg-[#000000] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden select-none">
      {/* Background ambient grid */}
      <div className="absolute inset-0 obsidian-grid opacity-30 pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-10 h-10 border border-white/30 bg-[#080808] flex items-center justify-center rotate-45 mb-4 shadow-[0_0_20px_rgba(255,255,255,0.1)]">
            <div className="w-4 h-4 bg-white -rotate-45" />
          </div>
          <h1 className="text-xl font-mono font-bold text-white tracking-widest uppercase flex items-center gap-2">
            KAUSHALTWIN
            <span className="text-[10px] font-mono px-1.5 py-0.5 bg-white/10 text-white border border-white/20">
              RPL
            </span>
          </h1>
          <p className="text-xs text-zinc-400 font-sans mt-1 tracking-wider uppercase">
            Skill Intelligence Platform
          </p>
        </div>

        {/* Crystalline Login Panel */}
        <div className="bg-[#050505] py-8 px-6 sm:px-10 border border-white/15 specular-top-edge">
          <div className="mb-6">
            <h2 className="text-sm font-sans font-bold text-white uppercase tracking-wider">
              Sign In to Your Account
            </h2>
            <p className="text-xs text-zinc-400 font-light mt-1">
              Enter credentials to access the Recognition of Prior Learning assessment portal.
            </p>
          </div>

          {error && (
            <Alert variant="error" className="mb-5" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Email Address"
              type="email"
              autoComplete="email"
              required
              placeholder="assessor@kaushaltwin.gov.in"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                className="w-full justify-center py-3 font-mono text-xs tracking-wider uppercase"
                loading={loading}
              >
                <span>Sign In ↗</span>
              </Button>
            </div>
          </form>

          {/* Quick Demo Pre-fill for Hackathon Evaluators */}
          <div className="mt-6 pt-6 border-t border-white/10">
            <p className="text-[10px] font-sans uppercase text-zinc-400 tracking-wider mb-2.5">
              Quick Demo Accounts:
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoFill('assessor@kaushaltwin.gov.in', 'assessor123')}
                className="text-left p-2.5 bg-[#080808] border border-white/10 hover:border-white/30 transition-colors text-xs cursor-pointer"
              >
                <div className="font-sans font-bold text-white text-[11px]">Assessor</div>
                <div className="font-mono text-[10px] text-zinc-400">assessor123</div>
              </button>
              <button
                type="button"
                onClick={() => handleDemoFill('admin@kaushaltwin.gov.in', 'admin123')}
                className="text-left p-2.5 bg-[#080808] border border-white/10 hover:border-white/30 transition-colors text-xs cursor-pointer"
              >
                <div className="font-sans font-bold text-white text-[11px]">Admin</div>
                <div className="font-mono text-[10px] text-zinc-400">admin123</div>
              </button>
              <button
                type="button"
                onClick={() => handleDemoFill('worker@kaushaltwin.gov.in', 'worker123')}
                className="text-left p-2.5 bg-[#080808] border border-white/10 hover:border-white/30 transition-colors text-xs cursor-pointer"
              >
                <div className="font-sans font-bold text-white text-[11px]">Worker</div>
                <div className="font-mono text-[10px] text-zinc-400">worker123</div>
              </button>
            </div>
          </div>

          <div className="mt-6 text-center border-t border-white/5 pt-4">
            <Link
              to="/"
              className="text-xs font-sans text-zinc-400 hover:text-white flex items-center justify-center gap-1.5 tracking-wider transition-colors"
            >
              <Compass className="w-3.5 h-3.5" />
              <span>← Return to Home Page</span>
            </Link>
          </div>
        </div>

        {/* Security & Governance notice */}
        <div className="mt-6 flex items-center justify-center gap-2 text-[10px] font-sans text-zinc-500 uppercase tracking-widest text-center">
          <Shield className="w-3.5 h-3.5 text-zinc-400" />
          <span>Secure Assessor Governance</span>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
