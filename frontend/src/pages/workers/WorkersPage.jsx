import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  Plus,
  Phone,
  Briefcase,
  GraduationCap,
  ChevronRight,
  ShieldCheck,
  FileCheck2
} from 'lucide-react';
import { workersApi } from '../../api/workers.api';
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
  const { data, isLoading } = useQuery({
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
    <div className="space-y-6 select-none">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>Candidate Registry &amp; Profiles</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              Candidates &amp; Workers
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light">
              Registered candidates in the Recognition of Prior Learning pool ({data?.total ?? workers.length} total)
            </p>
          </div>

          <Button
            variant="primary"
            onClick={() => setIsCreateOpen(true)}
            className="font-mono"
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            <span>Add Candidate</span>
          </Button>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-zinc-500" />
          <input
            type="text"
            placeholder="Search candidate by name, trade, or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs font-mono bg-[#080808] border border-white/15 text-white placeholder-zinc-500 focus:border-white focus:outline-none transition-colors"
          />
        </div>

        <div className="w-full sm:w-64">
          <select
            value={tradeFilter}
            onChange={(e) => setTradeFilter(e.target.value)}
            className="w-full py-2 px-3 text-xs font-mono bg-[#080808] border border-white/15 text-white focus:border-white focus:outline-none"
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
      </div>

      {/* Monochromatic Workers Table */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#080808] border-b border-white/15 text-zinc-400 text-[10px] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5 font-semibold">Candidate Name</th>
                <th className="px-6 py-3.5 font-semibold">Trade / Sector</th>
                <th className="px-6 py-3.5 font-semibold">Experience &amp; Education</th>
                <th className="px-6 py-3.5 font-semibold">Declared Competencies</th>
                <th className="px-6 py-3.5 text-right font-semibold">Actions</th>
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
                      description="No registered workers match your current filters. Add a candidate to begin assessment."
                      actionLabel="Register Candidate"
                      onAction={() => setIsCreateOpen(true)}
                    />
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody className="divide-y divide-white/5">
                {filteredWorkers.map((w) => (
                  <tr
                    key={w.id}
                    className="hover:bg-white/[0.03] transition-colors group cursor-pointer"
                    onClick={() => navigate(`/workers/${w.id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="font-bold text-white group-hover:text-zinc-200 transition-colors flex items-center gap-2">
                        <span>{w.full_name}</span>
                      </div>
                      <div className="text-[11px] text-zinc-500 flex items-center gap-1.5 mt-0.5">
                        <Phone className="w-3 h-3 text-zinc-500" />
                        <span>{w.phone || 'No phone recorded'}</span>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-zinc-300 font-semibold">
                        {w.trade || 'General'}
                      </div>
                      <div className="text-[10px] text-zinc-500">
                        RPL ID: #{w.id.slice(0, 8)}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-zinc-300 flex items-center gap-1.5">
                        <Briefcase className="w-3.5 h-3.5 text-zinc-500" />
                        <span>{w.years_of_experience || 0} years experience</span>
                      </div>
                      <div className="text-[10px] text-zinc-500 flex items-center gap-1.5 mt-0.5">
                        <GraduationCap className="w-3.5 h-3.5 text-zinc-500" />
                        <span>{w.education_level || 'Informal'}</span>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {w.declared_skills && w.declared_skills.length > 0 ? (
                          w.declared_skills.slice(0, 3).map((s, idx) => (
                            <span
                              key={idx}
                              className="px-1.5 py-0.5 bg-[#09090b] border border-white/10 text-[10px] text-zinc-400"
                            >
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-zinc-600 text-[10px]">None declared</span>
                        )}
                        {w.declared_skills && w.declared_skills.length > 3 && (
                          <span className="text-[10px] text-zinc-500 self-center">
                            +{w.declared_skills.length - 3} more
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-zinc-400 group-hover:text-white transition-colors">
                        <span>WORKSPACE</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            )}
          </table>
        </div>
      </div>

      {/* Registration Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="REGISTER RPL CANDIDATE"
        description="Candidate informal skills and trade credentials for National Occupational Standards mapping."
        maxWidth="max-w-xl"
      >
        {formError && (
          <Alert variant="error" className="mb-4" onClose={() => setFormError(null)}>
            {formError}
          </Alert>
        )}

        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Input
            label="Candidate Full Name"
            required
            placeholder="e.g. Ramesh Kumar"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Contact Phone"
              placeholder="+91 98765 43210"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            />
            <Input
              label="Email Address"
              placeholder="candidate@gmail.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Primary Trade / Sector"
              required
              value={formData.trade}
              onChange={(e) => setFormData({ ...formData, trade: e.target.value })}
              options={[
                { value: 'Welding & Fabrication', label: 'Welding & Fabrication (CSC/Q0204)' },
                { value: 'Automotive Repair', label: 'Automotive Repair (ASC/Q1401)' },
                { value: 'Carpentry & Furniture', label: 'Carpentry & Furniture (FFS/Q0103)' },
                { value: 'Electrical Installation', label: 'Electrical Installation (ELE/Q1401)' },
                { value: 'Solar PV Technician', label: 'Solar PV Technician (SGJ/Q0101)' },
                { value: 'Plumbing Services', label: 'Plumbing Services (PSC/Q0104)' },
              ]}
            />
            <Input
              label="Years of Trade Experience"
              type="number"
              min="0"
              max="50"
              value={formData.years_of_experience}
              onChange={(e) => setFormData({ ...formData, years_of_experience: e.target.value })}
            />
          </div>

          <Input
            label="Declared Skills (Comma Separated)"
            placeholder="e.g. Arc Welding, Gas Cutting, Joint Preparation"
            value={formData.declared_skills}
            onChange={(e) => setFormData({ ...formData, declared_skills: e.target.value })}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button
              variant="outline"
              onClick={() => setIsCreateOpen(false)}
              className="font-mono text-xs"
            >
              CANCEL
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={createMutation.isPending}
              className="font-mono text-xs"
            >
              REGISTER CANDIDATE ↗
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default WorkersPage;
