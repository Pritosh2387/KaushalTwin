import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardCheck,
  Search,
  Plus,
  Filter,
  Eye,
  Calendar,
  Briefcase,
  User,
  ArrowRight,
  Sparkles,
  ShieldAlert,
  ChevronRight
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
  const { data, isLoading, error } = useQuery({
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span>RPL Assessments</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
              {data?.total ?? assessments.length} Workspaces
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Recognition of Prior Learning evaluations, NOS mapping, and competency certification
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsCreateOpen(true)}
          className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold shadow-md shadow-cyan-500/20"
        >
          <Plus className="w-4 h-4 mr-1.5" />
          <span>New Assessment</span>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by assessment ID, trade, or candidate ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            />
          </div>

          <div className="w-full sm:w-64">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-2 px-3 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            >
              <option value="">All Lifecycle States</option>
              <option value="DRAFT">Draft</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="READY_FOR_REVIEW">Ready for Review (AI Ready)</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="COMPLETED">Completed / Certified</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Assessments Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Assessment Trade</th>
                <th className="px-6 py-3.5">Candidate Worker</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Created Date</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            {isLoading ? (
              <SkeletonTableRows rows={5} cols={5} />
            ) : filtered.length === 0 ? (
              <tbody>
                <tr>
                  <td colSpan={5} className="p-8">
                    <EmptyState
                      icon={ClipboardCheck}
                      title="No assessments found"
                      description="No assessment workspaces match your filter criteria. Initialize a new assessment to begin."
                      actionLabel="Create Assessment"
                      onAction={() => setIsCreateOpen(true)}
                    />
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody className="divide-y divide-slate-100">
                {filtered.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-slate-50/70 transition-colors group cursor-pointer"
                    onClick={() => navigate(`/assessments/${a.id}`)}
                  >
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900 group-hover:text-cyan-600 transition-colors">
                        {a.trade}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">
                        Assessment #{a.id.slice(0, 8)}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>Worker #{a.worker_id.slice(0, 8)}...</span>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <StatusBadge status={a.status} size="sm" />
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500">
                      {new Date(a.created_at).toLocaleDateString()}
                    </td>

                    <td className="px-6 py-4 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/assessments/${a.id}`);
                        }}
                        className="text-xs hover:border-cyan-500 hover:text-cyan-600"
                      >
                        <span>Workspace</span>
                        <ChevronRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            )}
          </table>
        </div>
      </Card>

      {/* Create Assessment Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Initialize RPL Assessment"
        description="Select a candidate worker to begin the AI-assisted assessment workflow."
      >
        {createError && (
          <Alert variant="error" className="mb-4" onClose={() => setCreateError(null)}>
            {createError}
          </Alert>
        )}

        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Select
            label="Select Candidate Worker *"
            value={createFormData.worker_id}
            onChange={(e) => {
              const selectedId = e.target.value;
              const found = workers.find((w) => w.id === selectedId);
              setCreateFormData({
                worker_id: selectedId,
                trade: found?.trade || createFormData.trade || '',
              });
            }}
            options={[
              { value: '', label: '-- Select Candidate --' },
              ...workers.map((w) => ({
                value: w.id,
                label: `${w.full_name} (${w.trade || 'General'}) - ${w.years_of_experience || 0} yrs exp`,
              })),
            ]}
          />

          <Input
            label="Assessment Trade / Sector *"
            required
            placeholder="e.g. Welding & Fabrication"
            value={createFormData.trade}
            onChange={(e) => setCreateFormData({ ...createFormData, trade: e.target.value })}
            helperText="The occupational trade domain against which NOS standards will be mapped."
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
              Launch Assessment
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
