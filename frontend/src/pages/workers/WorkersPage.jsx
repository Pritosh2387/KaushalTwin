import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  Plus,
  Filter,
  Eye,
  ClipboardCheck,
  Phone,
  Briefcase,
  GraduationCap,
  Calendar,
  Sparkles,
  ChevronRight,
  X
} from 'lucide-react';
import { workersApi } from '../../api/workers.api';
import { assessmentsApi } from '../../api/assessments.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Modal } from '../../components/ui/Modal';
import { SkeletonTableRows } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { EmptyState } from '../../components/ui/EmptyState';

export function WorkersPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState('');
  const [tradeFilter, setTradeFilter] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    trade: '',
    education_level: '10th Standard',
    years_of_experience: 3,
    declared_skills: '',
    languages: 'Hindi, English',
  });
  const [formError, setFormError] = useState(null);

  // Fetch workers
  const { data, isLoading, error } = useQuery({
    queryKey: ['workers', { trade: tradeFilter || undefined }],
    queryFn: () => workersApi.getAll({ limit: 100, trade: tradeFilter || undefined }),
  });

  const workers = data?.items || [];

  // Filter by search
  const filteredWorkers = workers.filter((w) => {
    const q = search.toLowerCase();
    return (
      w.full_name?.toLowerCase().includes(q) ||
      w.phone?.toLowerCase().includes(q) ||
      w.trade?.toLowerCase().includes(q)
    );
  });

  // Create Worker Mutation
  const createMutation = useMutation({
    mutationFn: (newWorker) => workersApi.create(newWorker),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ['workers'] });
      setIsCreateOpen(false);
      setFormData({
        full_name: '',
        phone: '',
        email: '',
        trade: '',
        education_level: '10th Standard',
        years_of_experience: 3,
        declared_skills: '',
        languages: 'Hindi, English',
      });
      navigate(`/workers/${created.id}`);
    },
    onError: (err) => {
      setFormError(
        err?.response?.data?.detail || 'Failed to register worker. Please check the inputs.'
      );
    },
  });

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    setFormError(null);
    if (!formData.full_name || !formData.trade) {
      setFormError('Full name and primary trade are required.');
      return;
    }

    const skillsArray = formData.declared_skills
      ? formData.declared_skills.split(',').map((s) => s.trim()).filter(Boolean)
      : [];
    const languagesArray = formData.languages
      ? formData.languages.split(',').map((l) => l.trim()).filter(Boolean)
      : [];

    createMutation.mutate({
      full_name: formData.full_name,
      phone: formData.phone || undefined,
      email: formData.email || undefined,
      trade: formData.trade,
      education_level: formData.education_level,
      years_of_experience: Number(formData.years_of_experience),
      declared_skills: skillsArray,
      languages: languagesArray,
    });
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span>RPL Worker Candidates</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
              {data?.total ?? workers.length} Total
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Candidates registered for Recognition of Prior Learning skill evaluation
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsCreateOpen(true)}
          className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold shadow-md shadow-cyan-500/20"
        >
          <Plus className="w-4 h-4 mr-1.5" />
          <span>Register New Candidate</span>
        </Button>
      </div>

      {/* Filters & Search */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by worker name, trade, or mobile number..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20 outline-none transition-all"
            />
          </div>

          <div className="w-full sm:w-60">
            <select
              value={tradeFilter}
              onChange={(e) => setTradeFilter(e.target.value)}
              className="w-full py-2 px-3 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            >
              <option value="">All Trades / Sectors</option>
              <option value="Welding & Fabrication">Welding & Fabrication</option>
              <option value="Automotive Repair">Automotive Repair</option>
              <option value="Carpentry & Furniture">Carpentry & Furniture</option>
              <option value="Electrical Installation">Electrical Installation</option>
              <option value="Solar PV Technician">Solar PV Technician</option>
              <option value="Plumbing Services">Plumbing Services</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Workers Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Candidate Name</th>
                <th className="px-6 py-3.5">Trade / Sector</th>
                <th className="px-6 py-3.5">Experience & Education</th>
                <th className="px-6 py-3.5">Declared Skills</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            {isLoading ? (
              <SkeletonTableRows rows={5} cols={5} />
            ) : filteredWorkers.length === 0 ? (
              <tbody>
                <tr>
                  <td colSpan={5} className="p-8">
                    <EmptyState
                      icon={Users}
                      title="No candidates found"
                      description="No registered workers match your current filters. Add a new candidate to begin assessment."
                      actionLabel="Register Candidate"
                      onAction={() => setIsCreateOpen(true)}
                    />
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody className="divide-y divide-slate-100">
                {filteredWorkers.map((w) => (
                  <tr
                    key={w.id}
                    className="hover:bg-slate-50/70 transition-colors group cursor-pointer"
                    onClick={() => navigate(`/workers/${w.id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 group-hover:text-cyan-600 transition-colors flex items-center gap-2">
                        <span>{w.full_name}</span>
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <Phone className="w-3 h-3 text-slate-400" />
                        <span>{w.phone || 'No phone recorded'}</span>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-800 text-xs sm:text-sm">
                        {w.trade || 'General'}
                      </div>
                      <div className="text-xs text-slate-400">
                        RPL Candidate ID: #{w.id.slice(0, 8)}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-xs text-slate-700 flex items-center gap-1.5 font-medium">
                        <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                        <span>{w.years_of_experience || 0} years experience</span>
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                        <GraduationCap className="w-3.5 h-3.5 text-slate-400" />
                        <span>{w.education_level || 'Informal'}</span>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {(w.declared_skills || []).slice(0, 3).map((skill, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[11px] font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                        {(w.declared_skills || []).length > 3 && (
                          <span className="px-1.5 py-0.5 text-[10px] text-slate-400 font-bold">
                            +{(w.declared_skills || []).length - 3} more
                          </span>
                        )}
                        {(!w.declared_skills || w.declared_skills.length === 0) && (
                          <span className="text-xs text-slate-400 italic">None listed</span>
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <div
                        className="inline-flex items-center gap-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/workers/${w.id}`)}
                          className="text-xs hover:border-cyan-500 hover:text-cyan-600"
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" />
                          <span>Profile</span>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            )}
          </table>
        </div>
      </Card>

      {/* Register Worker Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Register RPL Candidate"
        description="Enter the worker's experience, education, and claimed skills for evaluation."
        maxWidth="max-w-2xl"
      >
        {formError && (
          <Alert variant="error" className="mb-4" onClose={() => setFormError(null)}>
            {formError}
          </Alert>
        )}

        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Candidate Full Name *"
              required
              placeholder="e.g. Suraj Kumar Nishad"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
            <Input
              label="Phone Number"
              placeholder="e.g. +91 98765 43210"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Email Address"
              type="email"
              placeholder="suraj@example.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <Input
              label="Primary Trade / Occupation *"
              required
              placeholder="e.g. Welding & Fabrication"
              value={formData.trade}
              onChange={(e) => setFormData({ ...formData, trade: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Education Level"
              value={formData.education_level}
              onChange={(e) => setFormData({ ...formData, education_level: e.target.value })}
              options={[
                { value: 'Informal / None', label: 'Informal / None' },
                { value: '5th Standard', label: '5th Standard' },
                { value: '8th Standard', label: '8th Standard' },
                { value: '10th Standard', label: '10th Standard (Matric)' },
                { value: '12th Standard', label: '12th Standard' },
                { value: 'ITI Certificate', label: 'ITI Certificate' },
                { value: 'Diploma', label: 'Polytechnic Diploma' },
              ]}
            />

            <Input
              label="Years of Work Experience"
              type="number"
              min="0"
              max="50"
              value={formData.years_of_experience}
              onChange={(e) =>
                setFormData({ ...formData, years_of_experience: e.target.value })
              }
            />
          </div>

          <Input
            label="Declared Skills (Comma separated)"
            placeholder="e.g. Arc Welding, TIG Welding, Blueprint Reading, Grinding, Torch Cutting"
            value={formData.declared_skills}
            onChange={(e) => setFormData({ ...formData, declared_skills: e.target.value })}
            helperText="Informally acquired skills reported by the worker during RPL onboarding"
          />

          <Input
            label="Spoken Languages (Comma separated)"
            placeholder="Hindi, Bhojpuri, English"
            value={formData.languages}
            onChange={(e) => setFormData({ ...formData, languages: e.target.value })}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={createMutation.isPending}
            >
              Save Candidate Profile
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
