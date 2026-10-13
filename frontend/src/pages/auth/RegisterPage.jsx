import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Shield, ArrowRight, Compass } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Alert } from '../../components/ui/Alert';

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    role: 'ASSESSOR',
    organization: '',
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password || !formData.fullName) {
      setError('Please complete all required fields.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      await register({
        name: formData.fullName,
        email: formData.email,
        password: formData.password,
        role: formData.role,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          'Registration failed. Email may already be registered or invalid.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#000000] flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden select-none">
      <div className="absolute inset-0 obsidian-grid opacity-30 pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0">
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
          <p className="text-xs text-zinc-400 font-mono mt-1 tracking-wider uppercase">
            REGISTER PROFILE
          </p>
        </div>

        <div className="bg-[#050505] py-8 px-6 sm:px-10 border border-white/15 specular-top-edge">
          <div className="mb-6">
            <h2 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
              NEW CANDIDATE / ASSESSOR
            </h2>
            <p className="text-xs text-zinc-400 font-light mt-1">
              Join the national skill assessment framework
            </p>
          </div>

          {error && (
            <Alert variant="error" className="mb-5" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <Input
              label="Full Legal Name"
              type="text"
              name="fullName"
              required
              placeholder="e.g. Ramesh Kumar"
              value={formData.fullName}
              onChange={handleChange}
            />

            <Input
              label="Official Email"
              type="email"
              name="email"
              required
              placeholder="assessor@kaushaltwin.gov.in"
              value={formData.email}
              onChange={handleChange}
            />

            <Select
              label="System Authority Role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              options={[
                { value: 'ASSESSOR', label: 'Accredited Assessor' },
                { value: 'WORKER', label: 'RPL Candidate / Worker' },
                { value: 'ADMIN', label: 'System Administrator' },
              ]}
            />

            <Input
              label="Security Key"
              type="password"
              name="password"
              required
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
            />

            <Input
              label="Confirm Key"
              type="password"
              name="confirmPassword"
              required
              placeholder="••••••••"
              value={formData.confirmPassword}
              onChange={handleChange}
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                className="w-full justify-center py-3 font-mono text-xs tracking-widest uppercase"
                loading={loading}
              >
                <span>CREATE PROFILE ↗</span>
              </Button>
            </div>
          </form>

          <div className="mt-6 text-center border-t border-white/5 pt-4">
            <p className="text-xs font-mono text-zinc-400">
              ALREADY REGISTERED?{' '}
              <Link
                to="/login"
                className="text-white underline hover:text-zinc-200 uppercase"
              >
                SIGN IN HERE
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-center gap-2 text-[10px] font-mono text-zinc-500 uppercase tracking-widest text-center">
          <Shield className="w-3.5 h-3.5 text-zinc-400" />
          <span>HUMAN-CERTIFIED DECISION WORKFLOW</span>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
