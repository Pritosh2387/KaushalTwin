import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../context/AuthContext';
import {
  Users,
  Briefcase,
  GraduationCap,
  Phone,
  Mail,
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  Edit3,
  Languages,
  Award,
  AlertCircle
} from 'lucide-react';
import { workersApi } from '../../api/workers.api';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Alert } from '../../components/ui/Alert';
import { Skeleton } from '../../components/ui/Skeleton';
import { StatusBadge } from '../../components/ui/Badge';

export function WorkerProfilePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [formError, setFormError] = useState(null);

  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    trade: '',
    education_level: '',
    years_of_experience: 0,
    declared_skills: '',
    languages: '',
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

  // Populate form data when worker data is loaded
  useEffect(() => {
    if (worker) {
      setFormData({
        full_name: worker.full_name || user?.name || '',
        phone: worker.phone || '',
        email: worker.email || user?.email || '',
        trade: worker.trade || '',
        education_level: worker.education_level || 'Informal / Experiential',
        years_of_experience: worker.years_of_experience || 0,
        declared_skills: Array.isArray(worker.declared_skills) ? worker.declared_skills.join(', ') : '',
        languages: Array.isArray(worker.languages) ? worker.languages.join(', ') : 'Hindi',
      });
    }
  }, [worker, user]);

  // Update worker mutation
  const updateMutation = useMutation({
    mutationFn: async (payload) => {
      const targetId = worker?.id || user?.id;
      return await workersApi.update(targetId, payload);
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['worker-profile-me'] });
      queryClient.invalidateQueries({ queryKey: ['worker-profile'] });
      setIsEditOpen(false);
      setSuccessMessage('Profile updated successfully.');
      setFormError(null);
    },
    onError: (err) => {
      setFormError(err?.message || 'Failed to update profile. Please verify your inputs.');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    const skillsArray = formData.declared_skills
      ? formData.declared_skills.split(',').map((s) => s.trim()).filter(Boolean)
      : [];
    const languagesArray = formData.languages
      ? formData.languages.split(',').map((l) => l.trim()).filter(Boolean)
      : [];

    updateMutation.mutate({
      full_name: formData.full_name,
      phone: formData.phone || undefined,
      email: formData.email || undefined,
      trade: formData.trade,
      education_level: formData.education_level || undefined,
      years_of_experience: Number(formData.years_of_experience) || 0,
      declared_skills: skillsArray,
      languages: languagesArray,
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
    email: user?.email || '',
    trade: 'General',
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
            My Worker Profile
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
          <span>{isEditOpen ? 'Cancel Editing' : 'Edit Profile'}</span>
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
              Edit Candidate Information
            </h2>
            <p className="text-xs text-zinc-400 font-sans mt-0.5">
              Updates to declared experience and contact details will be recorded in your RPL audit history.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-mono text-zinc-300">
                  Full Name <span className="text-red-400">*</span>
                </label>
                <Input
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder="e.g. Ramesh Kumar"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono text-zinc-300">
                  Primary Trade / Sector <span className="text-red-400">*</span>
                </label>
                <Select
                  value={formData.trade}
                  onChange={(e) => setFormData({ ...formData, trade: e.target.value })}
                  options={[
                    { value: 'Electrical Installation', label: 'Electrical Installation (ELE/Q1401)' },
                    { value: 'Welding & Fabrication', label: 'Welding & Fabrication (CSC/Q0204)' },
                    { value: 'Automotive Repair', label: 'Automotive Repair (ASC/Q1401)' },
                    { value: 'Carpentry & Furniture', label: 'Carpentry & Furniture (FFS/Q0103)' },
                    { value: 'Solar PV Technician', label: 'Solar PV Technician (SGJ/Q0101)' },
                    { value: 'Plumbing Services', label: 'Plumbing Services (PSC/Q0104)' },
                  ]}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-mono text-zinc-300">Phone Number</label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="e.g. +91 98111 22334"
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono text-zinc-300">Email Address</label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="e.g. ramesh@example.com"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-mono text-zinc-300">Years of Practical Experience</label>
                <Input
                  type="number"
                  min="0"
                  max="60"
                  value={formData.years_of_experience}
                  onChange={(e) => setFormData({ ...formData, years_of_experience: e.target.value })}
                />
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-mono text-zinc-300">Highest Formal Education</label>
                <Select
                  value={formData.education_level}
                  onChange={(e) => setFormData({ ...formData, education_level: e.target.value })}
                  options={[
                    { value: 'Informal / Experiential', label: 'Informal / Experiential Learning' },
                    { value: '10th Standard', label: '10th Standard (Matriculation)' },
                    { value: '12th Standard', label: '12th Standard (Higher Secondary)' },
                    { value: 'ITI Certificate', label: 'ITI / Trade Certificate' },
                    { value: 'Diploma', label: 'Polytechnic Diploma' },
                    { value: 'Bachelors', label: "Bachelor's Degree" },
                  ]}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-zinc-300">
                Self-Declared Practical Skills (comma-separated)
              </label>
              <Input
                value={formData.declared_skills}
                onChange={(e) => setFormData({ ...formData, declared_skills: e.target.value })}
                placeholder="e.g. Domestic Wiring, MCB Distribution, Inverter Installation, Earthing"
              />
              <p className="text-[10px] text-zinc-500 font-sans">
                List the technical tasks you routinely perform without supervision.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-zinc-300">
                Languages Spoken (comma-separated)
              </label>
              <Input
                value={formData.languages}
                onChange={(e) => setFormData({ ...formData, languages: e.target.value })}
                placeholder="e.g. Hindi, English, Bhojpuri"
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
                Save Profile Changes ↗
              </Button>
            </div>
          </form>
        </div>
      ) : (
        /* Profile View */
        <div className="space-y-6">
          {/* Main Worker Overview Card */}
          <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-start sm:items-center gap-4">
                <div className="w-16 h-16 border border-white/20 bg-[#0a0a0a] text-white font-mono font-bold text-2xl flex items-center justify-center flex-shrink-0">
                  {currentWorker.full_name?.charAt(0)?.toUpperCase() || 'W'}
                </div>
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                      {currentWorker.full_name}
                    </h2>
                    <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-950/40 text-emerald-300 border border-emerald-700/40 uppercase">
                      {currentWorker.trade || 'General Trade'}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-400 font-mono">
                    <span className="flex items-center gap-1.5">
                      <Briefcase className="w-3.5 h-3.5 text-zinc-500" />
                      <span>{currentWorker.years_of_experience || 0} Years Experience</span>
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1.5">
                      <GraduationCap className="w-3.5 h-3.5 text-zinc-500" />
                      <span>{currentWorker.education_level || 'Informal Learning'}</span>
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 border-t md:border-t-0 pt-3 md:pt-0 border-white/10">
                <div className="text-left md:text-right">
                  <div className="text-[10px] font-mono text-zinc-500 uppercase">Assessment Status</div>
                  <div className="mt-0.5">
                    <StatusBadge status={currentWorker.assessment_status || 'NOT_STARTED'} size="sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Personal & Contact Details */}
            <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                  <Users className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Contact Information</span>
                </h3>
                <span className="text-[10px] font-mono text-zinc-500">Worker-managed</span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-zinc-500 text-[10px] font-mono uppercase block">Phone Number</span>
                  <p className="text-white font-mono mt-0.5">{currentWorker.phone || 'Not provided'}</p>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] font-mono uppercase block">Email Address</span>
                  <p className="text-white font-mono mt-0.5">{currentWorker.email || user?.email || 'Not provided'}</p>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] font-mono uppercase block">Languages Known</span>
                  <p className="text-white font-sans mt-0.5">
                    {(currentWorker.languages || ['Hindi']).join(', ')}
                  </p>
                </div>
              </div>
            </div>

            {/* Practical Background */}
            <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                  <Award className="w-3.5 h-3.5 text-zinc-400" />
                  <span>RPL Standard Alignment</span>
                </h3>
                <span className="text-[10px] font-mono text-zinc-500">National Qualification</span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-zinc-500 text-[10px] font-mono uppercase block">Assigned Sector</span>
                  <p className="text-white font-sans mt-0.5">{currentWorker.trade || 'General Trade'}</p>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] font-mono uppercase block">Formal Education Level</span>
                  <p className="text-white font-sans mt-0.5">{currentWorker.education_level || 'Informal / Experiential Learning'}</p>
                </div>
                <div>
                  <span className="text-zinc-500 text-[10px] font-mono uppercase block">Work Experience Summary</span>
                  <p className="text-zinc-300 font-sans mt-0.5 leading-relaxed">
                    {currentWorker.experience_summary || `${currentWorker.years_of_experience || 0} years documented in ${currentWorker.trade}.`}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Declared Practical Skills */}
          <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
              <h3 className="text-xs font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Declared Practical Competencies</span>
              </h3>
              <span className="text-[10px] font-mono text-zinc-500">
                {(currentWorker.declared_skills || []).length} Skills Listed
              </span>
            </div>

            {(currentWorker.declared_skills || []).length === 0 ? (
              <p className="text-zinc-500 text-xs font-sans italic py-2">
                No specific skills declared yet. Click "Edit Profile" above to list your core technical skills.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2 pt-1">
                {(currentWorker.declared_skills || []).map((skill, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#0a0a0a] border border-white/15 text-zinc-200 text-xs font-mono"
                  >
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>{skill}</span>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkerProfilePage;