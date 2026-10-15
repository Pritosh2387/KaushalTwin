import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../context/AuthContext';
import {
  Briefcase,
  ArrowLeft,
  Edit3,
  Calendar,
  CheckCircle2,
  FileText,
  AlertCircle,
  HelpCircle,
  Building2,
  Hammer
} from 'lucide-react';
import { workersApi } from '../../api/workers.api';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { Skeleton } from '../../components/ui/Skeleton';

export function WorkerExperiencePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [formError, setFormError] = useState(null);

  const [formData, setFormData] = useState({
    years_of_experience: 0,
    previous_employment: '',
    informal_work_description: '',
    experience_summary: '',
  });

  // Fetch current worker profile
  const {
    data: worker,
    isLoading: workerLoading,
    error: workerError,
  } = useQuery({
    queryKey: ['worker-profile-me'],
    queryFn: async () => {
      try {
        return await workersApi.getMyProfile();
      } catch (err) {
        if (user?.id) {
          return await workersApi.getById(user.id);
        }
        throw err;
      }
    },
    enabled: !!user?.id,
  });

  useEffect(() => {
    if (worker) {
      setFormData({
        years_of_experience: worker.years_of_experience || 0,
        previous_employment: worker.previous_employment || '',
        informal_work_description: worker.informal_work_description || '',
        experience_summary: worker.experience_summary || '',
      });
    }
  }, [worker]);

  // Update worker mutation
  const updateMutation = useMutation({
    mutationFn: async (payload) => {
      const targetId = worker?.id || user?.id;
      return await workersApi.update(targetId, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worker-profile-me'] });
      queryClient.invalidateQueries({ queryKey: ['worker-profile'] });
      setIsEditOpen(false);
      setSuccessMessage('Work experience details updated successfully.');
      setFormError(null);
    },
    onError: (err) => {
      setFormError(err?.message || 'Failed to update work experience. Please verify your inputs.');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    updateMutation.mutate({
      years_of_experience: Number(formData.years_of_experience) || 0,
      previous_employment: formData.previous_employment || undefined,
      informal_work_description: formData.informal_work_description || undefined,
      experience_summary: formData.experience_summary || undefined,
    });
  };

  if (workerLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const currentWorker = worker || {
    full_name: user?.name || 'Worker',
    years_of_experience: 0,
  };

  return (
    <div className="space-y-6 select-none">
      {/* Top Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 specular-top-edge">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-400 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>
          <span className="text-zinc-600">•</span>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            My Work Experience
          </h1>
        </div>
        <Button
          variant={isEditOpen ? 'outline' : 'primary'}
          size="sm"
          onClick={() => {
            setIsEditOpen(!isEditOpen);
            setFormError(null);
            setSuccessMessage(null);
          }}
          className="text-xs font-mono"
        >
          <Edit3 className="w-3.5 h-3.5 mr-1.5" />
          <span>{isEditOpen ? 'Cancel Editing' : 'Update Experience'}</span>
        </Button>
      </div>

      {successMessage && (
        <Alert variant="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {formError && (
        <Alert variant="error" onClose={() => setFormError(null)}>
          {formError}
        </Alert>
      )}

      {/* Edit Form */}
      {isEditOpen ? (
        <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge space-y-6">
          <div className="border-b border-white/10 pb-3">
            <h2 className="text-xs font-bold font-mono uppercase text-white tracking-wider">
              Document Work History &amp; Informal Background
            </h2>
            <p className="text-xs text-zinc-400 font-sans mt-0.5">
              RPL values informal, self-taught, and on-site practical learning alongside formal employment.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-zinc-300">
                Total Years of Practical Experience <span className="text-red-400">*</span>
              </label>
              <Input
                type="number"
                min="0"
                max="60"
                required
                value={formData.years_of_experience}
                onChange={(e) => setFormData({ ...formData, years_of_experience: e.target.value })}
                placeholder="e.g. 6"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-zinc-300">
                Previous Workshops / Contractors / Employers
              </label>
              <Input
                value={formData.previous_employment}
                onChange={(e) => setFormData({ ...formData, previous_employment: e.target.value })}
                placeholder="e.g. Verma Electricals, Metro Fabrication Works, Self-employed residential contractor"
              />
              <p className="text-[10px] text-zinc-500 font-sans">
                Names of employers, contractors, or shops where you worked.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-zinc-300">
                Informal Work Description &amp; Apprenticeship History
              </label>
              <textarea
                rows={3}
                value={formData.informal_work_description}
                onChange={(e) => setFormData({ ...formData, informal_work_description: e.target.value })}
                className="w-full bg-[#080808] border border-white/15 px-3 py-2 text-xs text-zinc-200 font-sans focus:border-white focus:outline-none"
                placeholder="Describe how you learned your trade (e.g., worked 3 years under a master electrician learning 3-phase wiring, maintenance, and fault diagnosis)..."
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-zinc-300">
                Comprehensive Experience Summary
              </label>
              <textarea
                rows={3}
                value={formData.experience_summary}
                onChange={(e) => setFormData({ ...formData, experience_summary: e.target.value })}
                className="w-full bg-[#080808] border border-white/15 px-3 py-2 text-xs text-zinc-200 font-sans focus:border-white focus:outline-none"
                placeholder="Overall summary of the projects, installations, or fabrication tasks you have completed..."
              />
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setIsEditOpen(false)}
                className="font-mono text-xs"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                loading={updateMutation.isPending}
                className="font-mono text-xs"
              >
                Save Experience Details ↗
              </Button>
            </div>
          </form>
        </div>
      ) : (
        /* Experience View */
        <div className="space-y-6">
          {/* Overview Banner */}
          <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
                  <span>On-The-Job Experience Record</span>
                </div>
                <div className="text-3xl sm:text-4xl font-bold font-mono text-white mt-1">
                  {currentWorker.years_of_experience || 0} Years
                </div>
                <p className="text-xs text-zinc-400 font-sans mt-1">
                  Practiced in <span className="text-white font-medium">{currentWorker.trade || 'General Trade'}</span>
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsEditOpen(true)}
                  className="font-mono text-xs"
                >
                  <Edit3 className="w-3.5 h-3.5 mr-1.5" />
                  <span>Edit Experience</span>
                </Button>
              </div>
            </div>
          </div>

          {/* Cards Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Previous Employment */}
            <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                  <Building2 className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Employment &amp; Workshop History</span>
                </h3>
              </div>
              <p className="text-xs text-zinc-300 font-sans leading-relaxed">
                {currentWorker.previous_employment || currentWorker.experience_summary || 'No formal employment record added yet.'}
              </p>
            </div>

            {/* Informal Work & Apprenticeship */}
            <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                  <Hammer className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Informal Learning &amp; Projects</span>
                </h3>
              </div>
              <p className="text-xs text-zinc-300 font-sans leading-relaxed">
                {currentWorker.informal_work_description || currentWorker.education_summary || 'Informal on-the-job training and site experience.'}
              </p>
            </div>
          </div>

          {/* RPL Valuation Notice */}
          <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge flex items-start gap-3">
            <HelpCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs font-sans text-zinc-400 leading-relaxed">
              <strong className="text-white font-mono uppercase">NCVET RPL Recognition Principle:</strong> Practical experience gained through informal labor, family workshops, or apprenticeship holds equal weight to classroom training when substantiated by evidence and verified by an authorized assessor.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkerExperiencePage;