import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardCheck,
  Search,
  Plus,
  ChevronRight,
  ShieldAlert,
  Calendar,
  Briefcase
} from 'lucide-react';
import { assessmentsApi } from '../../api/assessments.api';
import { workersApi } from '../../api/workers.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { SkeletonTableRows } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { EmptyState } from '../../components/ui/EmptyState';

export function AssessmentsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    worker_id: '',
    trade: '',
  });
  const [createError, setCreateError] = useState(null);

  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['assessments', { status: statusFilter || undefined }],
    queryFn: () => assessmentsApi.getAll({ limit: 100, status: statusFilter || undefined }),
  });

  const { data: workersData } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
  });

  const assessments = data?.items || [];
  const workers = workersData?.items || [];

  // Filter by search
  const filtered = assessments.filter((a) => {
    const q = search.toLowerCase();
    return (
      a.trade?.toLowerCase().includes(q) ||
      a.id?.toLowerCase().includes(q) ||
      a.worker_id?.toLowerCase().includes(q)
    );
  });

  // Create Mutation
  const createMutation = useMutation({
    mutationFn: (newAssessment) => assessmentsApi.create(newAssessment),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ['assessments'] });
      setIsCreateOpen(false);
      navigate(`/assessments/${created.id}`);
    },
    onError: (err) => {
      setCreateError(
        err?.response?.data?.detail || 'Failed to initialize assessment workspace.'
      );
    },
  });

  const handleCreateSubmit = (e) => {
    e.preventDefault();
    setCreateError(null);
    if (!createFormData.worker_id || !createFormData.trade) {
      setCreateError('Please select a candidate worker and enter the assessment trade.');
      return;
    }
    createMutation.mutate(createFormData);
  };

  return (
    <div className="space-y-6 select-none">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>Assessment &amp; Certification Pipeline</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              Candidate Assessments
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light">
              Formal verification sessions and candidate evidence evaluations ({data?.total ?? assessments.length} workspaces)
            </p>
          </div>

          <Button
            variant="primary"
            onClick={() => setIsCreateOpen(true)}
            className="font-mono"
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            <span>New Assessment</span>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-zinc-500" />
          <input
            type="text"
            placeholder="Search by assessment ID, trade, or candidate ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs font-mono bg-[#080808] border border-white/15 text-white placeholder-zinc-500 focus:border-white focus:outline-none transition-colors"
          />
        </div>

        <div className="w-full sm:w-64">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full py-2 px-3 text-xs font-mono bg-[#080808] border border-white/15 text-white focus:border-white focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="READY_FOR_REVIEW">Ready for Review</option>
            <option value="COMPLETED">Completed</option>
            <option value="CERTIFIED">Certified</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
      </div>

      {/* Monochromatic Assessments Table */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#080808] border-b border-white/15 text-zinc-400 text-[10px] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5 font-semibold">ASSESSMENT ID</th>
                <th className="px-6 py-3.5 font-semibold">TARGET TRADE / NOS</th>
                <th className="px-6 py-3.5 font-semibold">CANDIDATE WORKER</th>
                <th className="px-6 py-3.5 font-semibold">STATUS</th>
                <th className="px-6 py-3.5 font-semibold">TIMESTAMP</th>
                <th className="px-6 py-3.5 text-right font-semibold">WORKSPACE</th>
              </tr>
            </thead>
            {isLoading ? (
              <SkeletonTableRows rows={5} cols={6} />
            ) : filtered.length === 0 ? (
              <tbody>
                <tr>
                  <td colSpan={6} className="p-8">
                    <EmptyState
                      icon={ClipboardCheck}
                      title="No assessments found"
                      description="No workspaces match your query. Initialize a new assessment for a candidate."
                      actionLabel="Initialize Assessment"
                      onAction={() => setIsCreateOpen(true)}
                    />
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody className="divide-y divide-white/5">
                {filtered.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-white/[0.03] transition-colors group cursor-pointer"
                    onClick={() => navigate(`/assessments/${a.id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="font-bold text-white group-hover:text-zinc-200 transition-colors flex items-center gap-2">
                        <span>#{a.id.slice(0, 8)}</span>
                      </div>
                      <div className="text-[10px] text-zinc-500">UUID: {a.id}</div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-zinc-200 font-semibold">{a.trade || 'Welder'}</div>
                      <div className="text-[10px] text-zinc-500">NSQF Level 4</div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-zinc-300 font-mono">ID: {a.worker_id.slice(0, 8)}...</div>
                    </td>

                    <td className="px-6 py-4">
                      <StatusBadge status={a.status} size="sm" />
                    </td>

                    <td className="px-6 py-4 text-zinc-400 text-[11px]">
                      {new Date(a.created_at).toLocaleDateString()}
                    </td>

                    <td className="px-6 py-4 text-right">
                      <span className="inline-flex items-center gap-1 text-[11px] font-mono text-zinc-400 group-hover:text-white transition-colors">
                        <span>OPEN</span>
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

      {/* Creation Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="INITIALIZE RPL ASSESSMENT"
        description="Launch an end-to-end ML skill evaluation workspace for a registered candidate."
        maxWidth="max-w-lg"
      >
        {createError && (
          <Alert variant="error" className="mb-4" onClose={() => setCreateError(null)}>
            {createError}
          </Alert>
        )}

        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Select
            label="Candidate Worker"
            required
            value={createFormData.worker_id}
            onChange={(e) => setCreateFormData({ ...createFormData, worker_id: e.target.value })}
            options={workers.map((w) => ({
              value: w.id,
              label: `${w.full_name || 'Candidate'} (${w.trade || 'General'})`,
            }))}
          />

          <Select
            label="Assessment Trade Standard"
            required
            value={createFormData.trade}
            onChange={(e) => setCreateFormData({ ...createFormData, trade: e.target.value })}
            options={[
              { value: 'Welding & Fabrication', label: 'Welding & Fabrication (CSC/Q0204)' },
              { value: 'Automotive Repair', label: 'Automotive Repair (ASC/Q1401)' },
              { value: 'Carpentry & Furniture', label: 'Carpentry & Furniture (FFS/Q0103)' },
              { value: 'Electrical Installation', label: 'Electrical Installation (ELE/Q1401)' },
              { value: 'Solar PV Technician', label: 'Solar PV Technician (SGJ/Q0101)' },
              { value: 'Plumbing Services', label: 'Plumbing Services (PSC/Q0104)' },
            ]}
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
              CREATE WORKSPACE ↗
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default AssessmentsPage;
