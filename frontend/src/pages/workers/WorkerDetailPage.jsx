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
  Sparkles,
  ClipboardCheck,
  FileCheck2,
  Plus,
  ArrowLeft,
  ChevronRight,
  Cpu,
  CheckCircle2,
  Clock,
  ShieldCheck
} from 'lucide-react';
import { workersApi } from '../../api/workers.api';
import { assessmentsApi } from '../../api/assessments.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge, RoleBadge } from '../../components/ui/Badge';
import { Tabs } from '../../components/ui/Tabs';
import { Skeleton } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { EmptyState } from '../../components/ui/EmptyState';

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
    isLoading: assessmentsLoading
  } = useQuery({
    queryKey: ['worker-assessments', id],
    queryFn: () => workersApi.getAssessments(id),
    enabled: !!id,
  });

  const {
    data: evidenceData,
    isLoading: evidenceLoading
  } = useQuery({
    queryKey: ['worker-evidence', id],
    queryFn: () => workersApi.getEvidence(id),
    enabled: !!id,
  });

  const {
    data: competencyProfile,
    isLoading: competencyLoading
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
        err?.response?.data?.detail || 'Failed to create assessment for this candidate.'
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
        <Skeleton className="h-40 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (workerError || !worker) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => navigate('/workers')}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          <span>Back to Workers</span>
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
    { id: 'competencies', label: 'Competency Twin', badge: 'AI' },
  ];

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/workers')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Candidate Directory</span>
        </button>
      </div>

      {/* Candidate Profile Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start sm:items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-navy-950 text-cyan-400 font-black text-2xl flex items-center justify-center shadow-md flex-shrink-0">
            {worker.full_name?.charAt(0)?.toUpperCase()}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight">
                {worker.full_name}
              </h1>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-200">
                {worker.trade}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 mt-1.5">
              <span className="flex items-center gap-1">
                <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                <span>{worker.years_of_experience || 0} years experience</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <GraduationCap className="w-3.5 h-3.5 text-slate-400" />
                <span>{worker.education_level || 'Informal education'}</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>{worker.phone || 'No phone'}</span>
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
            className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold shadow-md shadow-cyan-500/20"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            <span>Start RPL Assessment</span>
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate('/evidence')}
          >
            <FileCheck2 className="w-4 h-4 mr-1.5" />
            <span>Upload Evidence</span>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Profile & Skills */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Declared Skill Inventory</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-slate-500">
                Skills claimed during onboarding interview. These form the input baseline for the ML Skill Extractor and NOS Matcher.
              </p>
              <div className="flex flex-wrap gap-2">
                {(worker.declared_skills || []).map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-800 text-xs font-semibold border border-slate-200"
                  >
                    {skill}
                  </span>
                ))}
                {(!worker.declared_skills || worker.declared_skills.length === 0) && (
                  <p className="text-sm text-slate-400 italic">No skills declared yet.</p>
                )}
              </div>

              <div className="pt-4 border-t border-slate-100">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Spoken Languages
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(worker.languages || ['Hindi']).map((lang, lIdx) => (
                    <span
                      key={lIdx}
                      className="px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-medium"
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Candidate Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 font-medium">System UUID:</span>
                <p className="font-mono text-slate-700 break-all">{worker.id}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Email:</span>
                <p className="text-slate-700">{worker.email || 'N/A'}</p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Registered At:</span>
                <p className="text-slate-700">
                  {new Date(worker.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="pt-2 border-t border-slate-100">
                <div className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>NCVET Assessment Eligible</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 2: Linked Assessments */}
      {activeTab === 'assessments' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Assessment Workspaces</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAssessmentModalOpen(true)}
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              <span>New Assessment</span>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {assessments.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={ClipboardCheck}
                  title="No assessments started"
                  description="Start an assessment to run ML skill extraction and NOS mapping for this candidate."
                  actionLabel="Start Assessment Now"
                  onAction={() => setIsAssessmentModalOpen(true)}
                />
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {assessments.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => navigate(`/assessments/${a.id}`)}
                    className="p-5 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4 cursor-pointer"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">
                          {a.trade}
                        </span>
                        <StatusBadge status={a.status} size="sm" />
                      </div>
                      <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                        <span>ID: #{a.id.slice(0, 8)}</span>
                        <span>•</span>
                        <span>Created: {new Date(a.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" className="text-xs">
                        <span>Open Workspace</span>
                        <ChevronRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Evidence Portfolio */}
      {activeTab === 'evidence' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Uploaded Evidence Portfolio</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/evidence')}
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              <span>Submit New Evidence</span>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {evidenceList.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={FileCheck2}
                  title="No evidence submitted"
                  description="Upload work samples, certificates, photographs, or supervisor declarations."
                  actionLabel="Upload Evidence"
                  onAction={() => navigate('/evidence')}
                />
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {evidenceList.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-4 flex items-center justify-between gap-4"
                  >
                    <div>
                      <div className="font-semibold text-slate-900 text-sm flex items-center gap-2">
                        <span>{ev.description || 'Uploaded Evidence Item'}</span>
                        <StatusBadge status={ev.verification_status} size="sm" />
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-3">
                        <span className="font-mono text-[11px]">{ev.evidence_type}</span>
                        {ev.nos_id && <span>Target NOS: {ev.nos_id}</span>}
                        <span>•</span>
                        <span>{new Date(ev.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 4: Competency Twin */}
      {activeTab === 'competencies' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-cyan-100 text-cyan-700 flex items-center justify-center font-bold">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <CardTitle>Candidate Competency Twin</CardTitle>
                  <p className="text-xs text-slate-500">
                    Aggregated skill graph synthesized from declared experience, verified evidence, and completed assessment tasks.
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {competencies.length === 0 ? (
                <EmptyState
                  icon={Sparkles}
                  title="No Competency Twin Data Yet"
                  description="Run an AI Analysis inside an active assessment to generate the competency twin graph."
                  actionLabel="Go to Assessments"
                  onAction={() => setActiveTab('assessments')}
                />
              ) : (
                <div className="space-y-4">
                  {competencies.map((comp, cIdx) => (
                    <div
                      key={cIdx}
                      className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="font-bold text-slate-900 text-sm">
                          {comp.competency_name || comp.nos_id}
                        </div>
                        <div className="text-xs font-bold text-cyan-700">
                          {Math.round((comp.score || comp.confidence || 0) * 100)}%
                        </div>
                      </div>
                      <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-cyan-500 to-teal-400 h-full rounded-full transition-all"
                          style={{
                            width: `${Math.round((comp.score || comp.confidence || 0) * 100)}%`,
                          }}
                        />
                      </div>
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span>NOS: {comp.nos_id || 'General'}</span>
                        <span>Evidence coverage: {comp.evidence_count || 1} items</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Start Assessment Modal */}
      <Modal
        isOpen={isAssessmentModalOpen}
        onClose={() => setIsAssessmentModalOpen(false)}
        title="Start New RPL Assessment"
        description={`Initialize an assessment workspace for candidate ${worker.full_name}.`}
      >
        {assessmentError && (
          <Alert variant="error" className="mb-4" onClose={() => setAssessmentError(null)}>
            {assessmentError}
          </Alert>
        )}

        <form onSubmit={handleStartAssessment} className="space-y-4">
          <Input
            label="Candidate"
            value={worker.full_name}
            disabled
            helperText={`Years of Experience: ${worker.years_of_experience || 0}`}
          />

          <Input
            label="Assessment Trade / Qualification Pack *"
            required
            placeholder="e.g. Welding & Fabrication"
            value={assessmentTrade}
            onChange={(e) => setAssessmentTrade(e.target.value)}
          />

          <div className="p-3 bg-cyan-50 border border-cyan-200 rounded-xl text-xs text-cyan-900 flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-cyan-600 mt-0.5 flex-shrink-0" />
            <span>
              Creating this workspace links the candidate's declared skills and evidence to the embedded ML analysis engine for NOS mapping.
            </span>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsAssessmentModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={createAssessmentMutation.isPending}
            >
              Initialize Assessment
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
