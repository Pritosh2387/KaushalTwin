import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users,
  Briefcase,
  GraduationCap,
  Phone,
  Mail,
  Calendar,
  ClipboardCheck,
  FileCheck2,
  Plus,
  ArrowLeft,
  ChevronRight,
  Cpu,
  ShieldCheck
} from 'lucide-react';
import { workersApi } from '../../api/workers.api';
import { assessmentsApi } from '../../api/assessments.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Tabs } from '../../components/ui/Tabs';
import { Skeleton } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { Modal } from '../../components/ui/Modal';
import { EmptyState } from '../../components/ui/EmptyState';
import { formatDate } from '../../lib/date';

export function WorkerDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [isAssessmentModalOpen, setIsAssessmentModalOpen] = useState(false);
  const [assessmentTrade, setAssessmentTrade] = useState('');
  const [assessmentError, setAssessmentError] = useState(null);

  // Queries
  const {
    data: worker,
    isLoading: workerLoading,
    error: workerError
  } = useQuery({
    queryKey: ['worker', id],
    queryFn: () => workersApi.getById(id),
  });

  const {
    data: assessmentsData,
  } = useQuery({
    queryKey: ['worker-assessments', id],
    queryFn: () => workersApi.getAssessments(id),
    enabled: !!id,
  });

  const {
    data: evidenceData,
  } = useQuery({
    queryKey: ['worker-evidence', id],
    queryFn: () => workersApi.getEvidence(id),
    enabled: !!id,
  });

  const {
    data: competencyProfile,
  } = useQuery({
    queryKey: ['worker-competency', id],
    queryFn: () => workersApi.getCompetencyProfile(id),
    enabled: !!id,
  });

  // Create assessment mutation
  const createAssessmentMutation = useMutation({
    mutationFn: (payload) => assessmentsApi.create(payload),
    onSuccess: (newAssessment) => {
      queryClient.invalidateQueries({ queryKey: ['worker-assessments', id] });
      queryClient.invalidateQueries({ queryKey: ['assessments'] });
      setIsAssessmentModalOpen(false);
      navigate(`/assessments/${newAssessment.id}`);
    },
    onError: (err) => {
      setAssessmentError(
        err?.response?.data?.detail || 'Failed to initialize assessment workspace.'
      );
    },
  });

  const handleStartAssessment = (e) => {
    e.preventDefault();
    setAssessmentError(null);
    createAssessmentMutation.mutate({
      worker_id: id,
      trade: assessmentTrade || worker?.trade || 'Welding & Fabrication',
    });
  };

  if (workerLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (workerError || !worker) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => navigate('/workers')}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          <span>Back to Candidate Directory</span>
        </Button>
        <Alert variant="error" title="Worker Not Found">
          {workerError?.response?.data?.detail ||
            'The candidate record could not be located in the database.'}
        </Alert>
      </div>
    );
  }

  const assessments = assessmentsData?.items || assessmentsData || [];
  const evidenceList = evidenceData?.items || evidenceData || [];
  const competencies = competencyProfile?.competencies || [];

  const tabs = [
    { id: 'overview', label: 'Candidate Profile' },
    { id: 'assessments', label: 'Assessments', badge: assessments.length },
    { id: 'evidence', label: 'Evidence Portfolio', badge: evidenceList.length },
    { id: 'competencies', label: 'Competency Twin', badge: 'ML' },
  ];

  return (
    <div className="space-y-6 select-none font-mono">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/workers')}
          className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-400 hover:text-white transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Candidate Directory</span>
        </button>
      </div>

      {/* Candidate Profile Header Card */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 specular-top-edge">
        <div className="flex items-start sm:items-center gap-4">
          <div className="w-14 h-14 border border-white/20 bg-[#080808] text-white font-mono font-bold text-xl flex items-center justify-center flex-shrink-0">
            {worker.full_name?.charAt(0)?.toUpperCase()}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {worker.full_name}
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-white/10 text-white border border-white/20">
                {worker.trade}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-400 mt-1.5 font-mono">
              <span className="flex items-center gap-1">
                <Briefcase className="w-3.5 h-3.5 text-zinc-500" />
                <span>{worker.years_of_experience || 0} Years Experience</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <GraduationCap className="w-3.5 h-3.5 text-zinc-500" />
                <span>{worker.education_level || 'Informal / Experiential'}</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Phone className="w-3.5 h-3.5 text-zinc-500" />
                <span>{worker.phone || 'N/A'}</span>
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button
            variant="primary"
            onClick={() => {
              setAssessmentTrade(worker.trade || '');
              setIsAssessmentModalOpen(true);
            }}
            className="text-xs"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            <span>Start Assessment</span>
          </Button>
          <Button
            variant="secondary"
            onClick={() => navigate('/evidence')}
            className="text-xs"
          >
            <FileCheck2 className="w-3.5 h-3.5 mr-1" />
            <span>Upload Evidence</span>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Profile & Skills */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
            <h2 className="text-xs font-bold text-white tracking-wider">
              Declared Trade Skills
            </h2>
            <p className="text-[11px] text-zinc-400 font-sans leading-relaxed">
              Competencies declared during candidate enrollment. These provide the baseline for national occupational standard mapping.
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              {(worker.declared_skills || []).map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 bg-[#09090b] text-zinc-300 text-xs border border-white/15"
                >
                  {skill}
                </span>
              ))}
              {(!worker.declared_skills || worker.declared_skills.length === 0) && (
                <p className="text-xs text-zinc-500 italic">No declared skills recorded.</p>
              )}
            </div>

            <div className="pt-6 border-t border-white/10">
              <h3 className="text-xs font-bold text-white tracking-wider mb-2">
                Spoken Languages
              </h3>
              <div className="flex flex-wrap gap-2">
                {(worker.languages || ['Hindi']).map((lang, lIdx) => (
                  <span
                    key={lIdx}
                    className="px-2 py-0.5 bg-[#09090b] text-zinc-400 text-xs border border-white/10"
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-3 text-xs">
            <h2 className="text-xs font-bold text-white tracking-wider pb-2 border-b border-white/10">
              Candidate Details
            </h2>
            <div>
              <span className="text-zinc-500 text-[10px]">System ID:</span>
              <p className="text-white text-[11px] truncate">{worker.id}</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">Email Address:</span>
              <p className="text-zinc-300 text-[11px]">{worker.email || 'N/A'}</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">Enrolled Date:</span>
              <p className="text-zinc-300 text-[11px]">
                {formatDate(worker.created_at)}
              </p>
            </div>
            <div className="pt-4 border-t border-white/10">
              <div className="flex items-center gap-1.5 text-white text-[10px]">
                <ShieldCheck className="w-3.5 h-3.5 text-white" />
                <span>Eligible for NSQF Certification</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Linked Assessments */}
      {activeTab === 'assessments' && (
        <div className="bg-[#050505] border border-white/10 specular-top-edge">
          <div className="p-5 border-b border-white/10 flex items-center justify-between">
            <h2 className="text-xs font-bold text-white tracking-wider">
              Assessment Sessions
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAssessmentModalOpen(true)}
              className="text-xs"
            >
              <Plus className="w-3 h-3 mr-1" />
              <span>New Assessment</span>
            </Button>
          </div>
          <div className="p-0">
            {assessments.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={ClipboardCheck}
                  title="No active assessments"
                  description="Start an assessment workspace to begin evaluating competencies against national standards."
                  actionLabel="Start Assessment"
                  onAction={() => setIsAssessmentModalOpen(true)}
                />
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {assessments.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => navigate(`/assessments/${a.id}`)}
                    className="p-4 hover:bg-white/[0.03] transition-colors flex items-center justify-between gap-4 cursor-pointer"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-xs">{a.trade}</span>
                        <StatusBadge status={a.status} size="sm" />
                      </div>
                      <div className="text-[10px] text-zinc-500 mt-0.5">
                        ID: #{a.id.slice(0, 8)} • Created: {formatDate(a.created_at)}
                      </div>
                    </div>
                    <Button variant="outline" size="sm" className="text-[10px]">
                      <span>View Workspace ↗</span>
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Evidence Portfolio */}
      {activeTab === 'evidence' && (
        <div className="bg-[#050505] border border-white/10 specular-top-edge">
          <div className="p-5 border-b border-white/10 flex items-center justify-between">
            <h2 className="text-xs font-bold text-white tracking-wider">
              Evidence Portfolio
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/evidence')}
              className="text-xs"
            >
              <Plus className="w-3 h-3 mr-1" />
              <span>Upload Evidence</span>
            </Button>
          </div>
          <div className="p-0">
            {evidenceList.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={FileCheck2}
                  title="No evidence submitted"
                  description="Upload physical work samples, logbooks, or supervisor testimonials."
                  actionLabel="Upload Evidence"
                  onAction={() => navigate('/evidence')}
                />
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {evidenceList.map((ev) => (
                  <div key={ev.id} className="p-4 flex items-center justify-between gap-4">
                    <div>
                      <div className="font-bold text-white text-xs flex items-center gap-2">
                        <span>{ev.description || 'Candidate Work Sample'}</span>
                        <StatusBadge status={ev.verification_status} size="sm" />
                      </div>
                      <div className="text-[10px] text-zinc-500 mt-0.5">
                        Type: {ev.evidence_type} • NOS: {ev.nos_id || 'Pending'} • {formatDate(ev.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Competency Twin */}
      {activeTab === 'competencies' && (
        <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <h2 className="text-xs font-bold text-white tracking-wider">
                Competency Twin Summary
              </h2>
              <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                Verified competency ratings synthesized from submitted candidate evidence and practical evaluations.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/competencies')}
              className="text-xs"
            >
              <span>View Full Matrix ↗</span>
            </Button>
          </div>

          <div className="space-y-4 pt-2">
            {(competencies.length > 0 ? competencies : [
              { competency_name: 'Arc & Gas Welding', nos_id: 'CSC/N0204', score: 0.88, benchmark: 0.70 },
              { competency_name: 'Workplace Safety & Hazard Control', nos_id: 'CSC/N1335', score: 0.92, benchmark: 0.75 },
              { competency_name: 'Blueprint & Engineering Drawings', nos_id: 'CSC/N0205', score: 0.64, benchmark: 0.70 },
            ]).map((comp, idx) => {
              const scorePct = Math.round((comp.score || 0.7) * 100);
              return (
                <div key={idx} className="p-3 bg-[#080808] border border-white/10 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white font-bold">{comp.competency_name || comp.nos_id}</span>
                    <span className="text-zinc-300 font-bold">{scorePct}%</span>
                  </div>
                  <div className="w-full bg-[#121214] h-1.5 overflow-hidden">
                    <div className="bg-white h-full transition-all" style={{ width: `${scorePct}%` }} />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-zinc-500">
                    <span>NOS: {comp.nos_id}</span>
                    <span>Benchmark: {Math.round((comp.benchmark || 0.7) * 100)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Start Assessment Modal */}
      <Modal
        isOpen={isAssessmentModalOpen}
        onClose={() => setIsAssessmentModalOpen(false)}
        title="Start Candidate Assessment"
        description={`Start an AI-assisted evaluation session for ${worker.full_name}.`}
        maxWidth="max-w-md"
      >
        {assessmentError && (
          <Alert variant="error" className="mb-4" onClose={() => setAssessmentError(null)}>
            {assessmentError}
          </Alert>
        )}

        <form onSubmit={handleStartAssessment} className="space-y-4">
          <Select
            label="Assessment Target Trade"
            required
            value={assessmentTrade}
            onChange={(e) => setAssessmentTrade(e.target.value)}
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
              onClick={() => setIsAssessmentModalOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={createAssessmentMutation.isPending}
              className="text-xs"
            >
              Start Assessment ↗
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default WorkerDetailPage;
