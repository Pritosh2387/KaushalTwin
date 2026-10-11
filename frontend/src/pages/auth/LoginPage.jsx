import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Sparkles, Shield, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
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

  const from = location.state?.from?.pathname || '/';

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
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Decorative ambient background */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-400 to-teal-300 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Sparkles className="w-6 h-6 text-navy-950 font-bold" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
              KaushalTwin
              <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-cyan-400/20 text-cyan-300 border border-cyan-400/30">
                SIH 2026
              </span>
            </h1>
            <p className="text-xs text-slate-400 font-medium">
              AI-Assisted RPL Skill Assessment Platform
            </p>
          </div>
        </div>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0">
        <div className="bg-white py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-100">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Sign in to your account
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Access the Recognition of Prior Learning (RPL) assessment console
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
              placeholder="e.g. assessor@kaushaltwin.gov.in"
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
                className="w-full justify-center py-2.5 text-sm"
                loading={loading}
              >
                <span>Sign in to Assessment Portal</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </form>

          {/* Quick Demo Pre-fill for SIH Evaluation */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-xs font-semibold text-slate-600 mb-2">
              Demo Credentials (SIH Evaluator Quick Access):
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleDemoFill('assessor@kaushaltwin.gov.in', 'assessor123')}
                className="text-left px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-cyan-400 hover:bg-cyan-50/50 transition-colors text-xs text-slate-700 font-medium"
              >
                <div className="font-bold text-slate-900">Lead Assessor</div>
                <div className="text-[10px] text-slate-500">assessor123</div>
              </button>
              <button
                type="button"
                onClick={() => handleDemoFill('admin@kaushaltwin.gov.in', 'admin123')}
                className="text-left px-2.5 py-1.5 rounded-lg border border-slate-200 hover:border-cyan-400 hover:bg-cyan-50/50 transition-colors text-xs text-slate-700 font-medium"
              >
                <div className="font-bold text-slate-900">System Admin</div>
                <div className="text-[10px] text-slate-500">admin123</div>
              </button>
            </div>
          </div>

          <div className="mt-6 text-center">
            <p className="text-xs text-slate-500">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="font-semibold text-cyan-600 hover:text-cyan-700 hover:underline"
              >
                Register as Worker / Assessor
              </Link>
            </p>
          </div>
        </div>

        {/* Security & Human Assessor Banner */}
        <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-400 text-center">
          <Shield className="w-4 h-4 text-cyan-400" />
          <span>NCVET/NSQF Aligned • Human-Certified Decision Workflow</span>
        </div>
      </div>
    </div>
  );
}
