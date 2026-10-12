import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Sparkles, Shield, ArrowRight } from 'lucide-react';
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
      navigate('/', { replace: true });
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
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10 text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-400 to-teal-300 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Sparkles className="w-6 h-6 text-navy-950 font-bold" />
          </div>
          <div className="text-left">
            <h1 className="text-2xl font-black text-white tracking-tight">
              KaushalTwin
            </h1>
            <p className="text-xs text-slate-400 font-medium">
              Create an RPL Assessor or Worker Profile
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 sm:mx-auto sm:w-full sm:max-w-md relative z-10 px-4 sm:px-0">
        <div className="bg-white py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-100">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Register New User
            </h2>
            <p className="text-xs text-slate-500 mt-1">
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
              label="Full Name"
              name="fullName"
              required
              placeholder="e.g. Ramesh Chandra Verma"
              value={formData.fullName}
              onChange={handleChange}
            />

            <Input
              label="Email Address"
              name="email"
              type="email"
              required
              placeholder="e.g. ramesh@example.org"
              value={formData.email}
              onChange={handleChange}
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Password"
                name="password"
                type="password"
                required
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
              />
              <Input
                label="Confirm Password"
                name="confirmPassword"
                type="password"
                required
                placeholder="••••••••"
                value={formData.confirmPassword}
                onChange={handleChange}
              />
            </div>

            <Select
              label="Role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              options={[
                { value: 'ASSESSOR', label: 'Certified RPL Assessor' },
                { value: 'WORKER', label: 'Candidate / Worker' },
                { value: 'ADMIN', label: 'System Administrator' },
              ]}
            />

            <Input
              label="Organization / Sector Council (Optional)"
              name="organization"
              placeholder="e.g. Automotive Skills Development Council (ASDC)"
              value={formData.organization}
              onChange={handleChange}
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                className="w-full justify-center py-2.5 text-sm"
                loading={loading}
              >
                <span>Complete Registration</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </form>

          <div className="mt-6 text-center">
            <p className="text-xs text-slate-500">
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-semibold text-cyan-600 hover:text-cyan-700 hover:underline"
              >
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
