import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
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
import { formatDate } from '../../lib/date';

export function AssessmentsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isWorker, isAssessor, isAdmin } = useAuth();

  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedWorkerAssessment, setSelectedWorkerAssessment] = useState(null);
  const [createFormData, setCreateFormData] = useState({
    worker_id: '',
    trade: '',
  });
  const [createError, setCreateError] = useState(null);

  // For worker, fetch their profile to obtain profile ID
  const { data: myProfile } = useQuery({
    queryKey: ['my-profile'],
    queryFn: () => workersApi.getMyProfile(),
    enabled: isWorker,
  });

  const workerTargetId = myProfile?.id || user?.id;

  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['assessments', { status: statusFilter || undefined, workerId: isWorker ? workerTargetId : undefined }],
    queryFn: () => {
      if (isWorker) {
        // Workers only see their own assessments
        return assessmentsApi.getWorkerAssessments(workerTargetId);
      } else {
        // Assessors/admins see all assessments with optional filtering
        return assessmentsApi.getAll({ limit: 100, status: statusFilter || undefined });
      }
    },
    enabled: isWorker ? !!workerTargetId : true,
  });

  // Only fetch workers list for assessors/admins
  const { data: workersData } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
    enabled: !isWorker,
  });

  const rawAssessments = Array.isArray(data) ? data : (data?.items || []);
  const assessments = rawAssessments;
  const workers = workersData?.items || [];

  // Filter by search
  const filtered = assessments.filter((a) => {
    const q = search.toLowerCase();
    return (
      a.trade?.toLowerCase().includes(q) ||
      a.id?.toLowerCase().includes(q) ||
      (a.worker_id && a.worker_id.toLowerCase().includes(q))
    );
  });

  // Create Mutation for Assessors
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

  const handleRowClick = (a) => {
    if (isWorker) {
      setSelectedWorkerAssessment(a);
    } else {
      navigate(`/assessments/${a.id}`);
    }
  };

  return (
    <div className="space-y-6 select-none font-sans">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge font-mono">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>{isWorker ? 'RPL Recognition Progress' : 'Assessment & Certification Pipeline'}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              {isWorker ? 'My Assessments' : 'Candidate Assessments'}
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light font-sans">
              {isWorker
                ? 'Formal RPL evaluations and competency verification sessions linked to your skills profile.'
                : `Formal verification sessions and candidate evidence evaluations (${assessments.length} workspaces)`}
            </p>
          </div>

          {!isWorker && (
            <Button
              variant="primary"
              onClick={() => setIsCreateOpen(true)}
              className="font-mono text-xs"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              <span>New Assessment</span>
            </Button>
          )}

          {isWorker && (
            <Button
              variant="outline"
              onClick={() => navigate('/evidence')}
              className="font-mono text-xs"
            >
              <Briefcase className="w-3.5 h-3.5 mr-1.5" />
              <span>Submit Evidence</span>
            </Button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar for Assessors */}
      {!isWorker && (
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
      )}

      {/* Assessments Table */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#080808] border-b border-white/15 text-zinc-400 text-[10px] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5 font-semibold">ASSESSMENT ID</th>
                <th className="px-6 py-3.5 font-semibold">TARGET TRADE / NOS</th>
                {!isWorker && (
                  <th className="px-6 py-3.5 font-semibold">CANDIDATE WORKER</th>
                )}
                <th className="px-6 py-3.5 font-semibold">STATUS</th>
                <th className="px-6 py-3.5 font-semibold">STARTED DATE</th>
                <th className="px-6 py-3.5 text-right font-semibold">ACTION</th>
              </tr>
            </thead>
            {isLoading ? (
              <SkeletonTableRows rows={5} cols={isWorker ? 5 : 6} />
            ) : filtered.length === 0 ? (
              <tbody>
                <tr>
                  <td colSpan={isWorker ? 5 : 6} className="p-8">
                    <EmptyState
                      icon={ClipboardCheck}
                      title={isWorker ? "No Assessments Scheduled Yet" : "No Assessments Found"}
                      description={isWorker
                        ? "Once an authorized assessor reviews your work evidence, an RPL evaluation session will appear here. In the meantime, you can add more evidence or update your work experience."
                        : "No workspaces match your query. Initialize a new assessment for a registered candidate."
                      }
                      actionLabel={isWorker ? "Upload More Evidence" : "Initialize Assessment"}
                      onAction={() => isWorker ? navigate('/evidence') : setIsCreateOpen(true)}
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
                    onClick={() => handleRowClick(a)}
                  >
                    <td className="px-6 py-4">
                      <div className="font-bold text-white group-hover:text-zinc-200 transition-colors flex items-center gap-2">
                        <span>#{a.id.slice(0, 8)}</span>
                      </div>
                      <div className="text-[10px] text-zinc-500 font-mono">ID: {a.id}</div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="text-zinc-200 font-semibold">{a.trade || 'General'}</div>
                      <div className="text-[10px] text-zinc-500 font-sans">NCVET Level 4 • RPL Pathway</div>
                    </td>

                    {!isWorker && (
                      <td className="px-6 py-4">
                        <div className="text-zinc-300 font-mono">ID: {a.worker_id ? a.worker_id.slice(0, 8) : 'N/A'}...</div>
                      </td>
                    )}

                    <td className="px-6 py-4">
                      <StatusBadge status={a.status} size="sm" />
                    </td>

                    <td className="px-6 py-4 text-zinc-400 text-[11px]">
                      {formatDate(a.created_at)}
                    </td>

                    <td className="px-6 py-4 text-right">
                      {isWorker ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono text-white group-hover:underline">
                          {a.status === 'CERTIFIED' || a.status === 'COMPLETED' ? 'VIEW DOSSIER' : 'VIEW DETAILS'}
                          <ChevronRight className="w-3.5 h-3.5" />
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono text-zinc-400 group-hover:text-white transition-colors">
                          <span>OPEN</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            )}
          </table>
        </div>
      </div>

      {/* Worker Assessment Detail Modal */}
      {isWorker && selectedWorkerAssessment && (
        <Modal
          isOpen={!!selectedWorkerAssessment}
          onClose={() => setSelectedWorkerAssessment(null)}
          title={`ASSESSMENT DETAILS — ${selectedWorkerAssessment.trade || 'RPL'}`}
          description={`Evaluation Session #${selectedWorkerAssessment.id.slice(0, 8)}`}
          maxWidth="max-w-xl"
        >
          <div className="space-y-4 text-xs font-mono">
            <div className="p-4 bg-[#080808] border border-white/10 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-zinc-500">Target Trade Standard:</span>
                <span className="text-white font-bold">{selectedWorkerAssessment.trade}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-500">Lifecycle Status:</span>
                <StatusBadge status={selectedWorkerAssessment.status} size="sm" />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-zinc-500">Initiated Date:</span>
                <span className="text-zinc-300">
                  {formatDate(selectedWorkerAssessment.created_at)}
                </span>
              </div>
            </div>

            <div className="p-4 bg-[#080808] border border-white/10 space-y-2 font-sans">
              <div className="text-white font-semibold text-xs flex items-center gap-1.5 font-mono">
                <ClipboardCheck className="w-4 h-4 text-emerald-400" />
                <span>RPL Assessment Process</span>
              </div>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Your assessment evaluates your informal learning against National Occupational Standards (NOS).
                Your assigned assessor reviews your submitted evidence and AI-suggested mappings before recording a final certification decision.
              </p>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-white/10">
              <Button
                variant="outline"
                onClick={() => setSelectedWorkerAssessment(null)}
                className="font-mono text-xs"
              >
                Close
              </Button>
              {selectedWorkerAssessment.status === 'CERTIFIED' || selectedWorkerAssessment.status === 'COMPLETED' ? (
                <Button
                  variant="primary"
                  onClick={() => {
                    setSelectedWorkerAssessment(null);
                    navigate('/reports');
                  }}
                  className="font-mono text-xs"
                >
                  View Official Dossier ↗
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedWorkerAssessment(null);
                    navigate('/evidence');
                  }}
                  className="font-mono text-xs"
                >
                  Manage Evidence ↗
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Creation Modal - Only for Assessors/Admins */}
      {!isWorker && (
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
      )}
    </div>
  );
}

export default AssessmentsPage;
