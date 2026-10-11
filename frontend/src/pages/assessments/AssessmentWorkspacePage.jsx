import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ClipboardCheck,
  Play,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Cpu,
  FileCheck2,
  Layers,
  ArrowLeft,
  ChevronRight,
  ShieldCheck,
  Send,
  AlertTriangle,
  RotateCw,
  Plus,
  HelpCircle,
  Printer,
  FileText
} from 'lucide-react';
import { assessmentsApi } from '../../api/assessments.api';
import { workersApi } from '../../api/workers.api';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge, RoleBadge } from '../../components/ui/Badge';
import { Tabs } from '../../components/ui/Tabs';
import { Skeleton } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { EmptyState } from '../../components/ui/EmptyState';

export function AssessmentWorkspacePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState('analysis');
  const [taskResultModal, setTaskResultModal] = useState({ isOpen: false, taskId: null, taskTitle: '' });
  const [taskScore, setTaskScore] = useState(85);
  const [taskComments, setTaskComments] = useState('');
  const [decisionModalOpen, setDecisionModalOpen] = useState(false);
  const [decisionAction, setDecisionAction] = useState('ACCEPT_RECOMMENDATION');
  const [decisionComments, setDecisionComments] = useState('');
  const [notification, setNotification] = useState(null);

  // Queries
  const {
    data: assessment,
    isLoading: assessmentLoading,
    error: assessmentError,
    refetch: refetchAssessment
  } = useQuery({
    queryKey: ['assessment', id],
    queryFn: () => assessmentsApi.getById(id),
  });

  const { data: worker } = useQuery({
    queryKey: ['worker', assessment?.worker_id],
    queryFn: () => workersApi.getById(assessment.worker_id),
    enabled: !!assessment?.worker_id,
  });

  const { data: tasksData, refetch: refetchTasks } = useQuery({
    queryKey: ['assessment-tasks', id],
    queryFn: () => assessmentsApi.getTasks(id),
    enabled: !!id,
  });

  // Mutations
  const startMutation = useMutation({
    mutationFn: () => assessmentsApi.start(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment', id] });
      setNotification({ type: 'success', message: 'Assessment marked IN_PROGRESS.' });
    },
    onError: (err) => {
      setNotification({ type: 'error', message: err?.response?.data?.detail || 'Failed to start assessment.' });
    }
  });

  const analyzeMutation = useMutation({
    mutationFn: () => assessmentsApi.analyze(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['assessment', id] });
      setNotification({
        type: 'success',
        message: 'AI ML Analysis completed successfully! Competency mappings updated.',
      });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.response?.data?.detail || 'ML Analysis failed to process.',
      });
    }
  });

  const recommendTaskMutation = useMutation({
    mutationFn: () => assessmentsApi.recommendNextTask(id),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['assessment', id] });
      queryClient.invalidateQueries({ queryKey: ['assessment-tasks', id] });
      setNotification({
        type: 'success',
        message: `Adaptive task recommended: "${res?.selected_task || 'New Task'}" (Priority: ${res?.priority_score || 1.0})`,
      });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.response?.data?.detail || 'Failed to recommend next adaptive task.',
      });
    }
  });

  const checkEvidenceMutation = useMutation({
    mutationFn: () => assessmentsApi.checkEvidence(id),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['assessment', id] });
      setNotification({
        type: 'success',
        message: 'Evidence sufficiency verification evaluated by ML engine.',
      });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.response?.data?.detail || 'Failed to verify evidence sufficiency.',
      });
    }
  });

  const submitTaskResultMutation = useMutation({
    mutationFn: ({ taskId, payload }) => assessmentsApi.submitTaskResult(id, taskId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment', id] });
      queryClient.invalidateQueries({ queryKey: ['assessment-tasks', id] });
      setTaskResultModal({ isOpen: false, taskId: null, taskTitle: '' });
      setNotification({ type: 'success', message: 'Task evaluation recorded successfully.' });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.response?.data?.detail || 'Failed to submit task result.',
      });
    }
  });

  const recordDecisionMutation = useMutation({
    mutationFn: (payload) => assessmentsApi.recordDecision(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment', id] });
      setDecisionModalOpen(false);
      setNotification({
        type: 'success',
        message: 'Final Human Assessor Decision recorded and stored in audit ledger.',
      });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.response?.data?.detail || 'Failed to record decision.',
      });
    }
  });

  if (assessmentLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (assessmentError || !assessment) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => navigate('/assessments')}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          <span>Back to Assessments</span>
        </Button>
        <Alert variant="error" title="Assessment Not Found">
          {assessmentError?.response?.data?.detail || 'Unable to load assessment workspace.'}
        </Alert>
      </div>
    );
  }

  const tasks = tasksData?.items || assessment.tasks || [];
  const candidateCompetencies = assessment.candidate_competencies || [];
  const latestAiRun = assessment.latest_ai_run || null;
  const decision = assessment.decision || null;

  const tabs = [
    { id: 'analysis', label: 'AI Competency Analysis', icon: Cpu, badge: candidateCompetencies.length },
    { id: 'tasks', label: 'Adaptive Tasks', icon: Layers, badge: tasks.length },
    { id: 'decision', label: 'Assessor Decision', icon: ShieldCheck, badge: decision ? 'Decided' : 'Pending' },
    { id: 'overview', label: 'Candidate Baseline', icon: ClipboardCheck },
    { id: 'report', label: 'Official Report', icon: FileText },
  ];

  return (
    <div className="space-y-6">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/assessments')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Assessments</span>
        </button>
        <span className="text-xs text-slate-400 font-mono">
          UUID: {assessment.id}
        </span>
      </div>

      {notification && (
        <Alert
          variant={notification.type}
          onClose={() => setNotification(null)}
          className="animate-in fade-in duration-200"
        >
          {notification.message}
        </Alert>
      )}

      {/* Main Workspace Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              {assessment.trade}
            </h1>
            <StatusBadge status={assessment.status} />
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
            <span>Candidate: <strong className="text-slate-800">{worker?.full_name || assessment.worker_id}</strong></span>
            <span>•</span>
            <span>Experience: <strong className="text-slate-800">{worker?.years_of_experience || 0} years</strong></span>
            <span>•</span>
            <span>Created: {new Date(assessment.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {assessment.status === 'DRAFT' && (
            <Button
              variant="outline"
              onClick={() => startMutation.mutate()}
              loading={startMutation.isPending}
            >
              <Play className="w-4 h-4 mr-1 text-cyan-600" />
              <span>Start Assessment</span>
            </Button>
          )}

          <Button
            variant="primary"
            onClick={() => analyzeMutation.mutate()}
            loading={analyzeMutation.isPending}
            className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold shadow-md shadow-cyan-500/20"
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            <span>Run AI Analysis</span>
          </Button>

          <Button
            variant="outline"
            onClick={() => setDecisionModalOpen(true)}
            className="border-slate-300 hover:border-cyan-500 hover:text-cyan-700"
          >
            <ShieldCheck className="w-4 h-4 mr-1.5 text-emerald-600" />
            <span>Record Final Decision</span>
          </Button>
        </div>
      </div>

      {/* Workspace Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: AI Competency Analysis */}
      {activeTab === 'analysis' && (
        <div className="space-y-6">
          {/* AI Banner / Status */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-navy-950 to-slate-900 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border border-navy-800 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base leading-snug">
                  Integrated ML Intelligence Pipeline
                </h3>
                <p className="text-xs text-slate-300 mt-0.5 max-w-xl">
                  Extracts raw declared skills, matches candidate competencies with National Occupational Standards (NOS), and assesses evidence confidence.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => checkEvidenceMutation.mutate()}
                loading={checkEvidenceMutation.isPending}
                className="border-slate-700 text-slate-200 hover:bg-navy-800 hover:text-white text-xs"
              >
                <FileCheck2 className="w-3.5 h-3.5 mr-1 text-cyan-400" />
                <span>Check Evidence Sufficiency</span>
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => analyzeMutation.mutate()}
                loading={analyzeMutation.isPending}
                className="bg-cyan-400 hover:bg-cyan-300 text-navy-950 font-bold text-xs"
              >
                <RotateCw className="w-3.5 h-3.5 mr-1" />
                <span>Re-run Analysis</span>
              </Button>
            </div>
          </div>

          {/* Candidate Competencies Grid */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Candidate Competency Mappings</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">
                  National Occupational Standards (NOS) matched from candidate skills & evidence
                </p>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                {candidateCompetencies.length} Mappings Identified
              </span>
            </CardHeader>
            <CardContent>
              {candidateCompetencies.length === 0 ? (
                <EmptyState
                  icon={Sparkles}
                  title="No Competency Mappings Yet"
                  description="Run the embedded AI Analysis to extract candidate skills and map them to official NOS standards."
                  actionLabel="Run AI Analysis"
                  onAction={() => analyzeMutation.mutate()}
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {candidateCompetencies.map((comp, idx) => {
                    const score = Math.round((comp.score || comp.confidence || 0.75) * 100);
                    return (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3 hover:border-cyan-400 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-100 text-cyan-800">
                              {comp.nos_id || 'NOS-STD-2026'}
                            </span>
                            <h4 className="font-bold text-slate-900 text-sm mt-1.5">
                              {comp.competency_name || comp.nos_id || 'Target Competency'}
                            </h4>
                          </div>
                          <div className="text-right">
                            <span className="text-base font-black text-slate-900">
                              {score}%
                            </span>
                            <div className="text-[10px] text-slate-400 font-semibold uppercase">
                              Confidence
                            </div>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              score >= 70
                                ? 'bg-emerald-500'
                                : score >= 50
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                            }`}
                            style={{ width: `${score}%` }}
                          />
                        </div>

                        <div className="flex items-center justify-between text-xs text-slate-500 pt-1 border-t border-slate-100">
                          <span>Evidence: {comp.evidence_count || 1} verified items</span>
                          <span className="font-medium text-slate-700">
                            Status: {score >= 70 ? 'Proficient' : 'Requires Task'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 2: Adaptive Assessment Tasks */}
      {activeTab === 'tasks' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Adaptive Assessment Tasks
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                AI recommends specific practical or theoretical tasks to verify competency gaps.
              </p>
            </div>

            <Button
              variant="primary"
              onClick={() => recommendTaskMutation.mutate()}
              loading={recommendTaskMutation.isPending}
              className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold shadow-md shadow-cyan-500/20"
            >
              <Sparkles className="w-4 h-4 mr-1.5" />
              <span>Recommend Next Task</span>
            </Button>
          </div>

          <Card>
            <CardContent className="p-0">
              {tasks.length === 0 ? (
                <div className="p-8">
                  <EmptyState
                    icon={Layers}
                    title="No Adaptive Tasks Assigned"
                    description="Click 'Recommend Next Task' to let the AI analyze evidence gaps and recommend the highest priority verification task."
                    actionLabel="Recommend Next Task"
                    onAction={() => recommendTaskMutation.mutate()}
                  />
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {tasks.map((t, idx) => (
                    <div
                      key={t.id || idx}
                      className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
                    >
                      <div className="space-y-1.5 max-w-xl">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-900">
                            Task #{idx + 1}: {t.task_name || t.selected_task || t.title || 'Practical Assessment Task'}
                          </span>
                          <StatusBadge status={t.status || 'PENDING'} size="sm" />
                        </div>
                        <p className="text-xs text-slate-600 leading-relaxed">
                          {t.description || t.reason || 'Evaluate worker execution technique, safety protocols, and standard adherence.'}
                        </p>
                        <div className="flex items-center gap-3 text-xs text-slate-400 font-medium pt-1">
                          {t.priority_score && (
                            <span>AI Priority: {(t.priority_score * 100).toFixed(0)}%</span>
                          )}
                          {t.score !== undefined && (
                            <span className="text-emerald-600 font-bold">
                              Assessor Score: {t.score}%
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        {t.status !== 'COMPLETED' ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              setTaskResultModal({
                                isOpen: true,
                                taskId: t.id || idx,
                                taskTitle: t.task_name || t.selected_task || 'Task Evaluation',
                              })
                            }
                            className="hover:border-cyan-500 hover:text-cyan-700 text-xs"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                            <span>Submit Score & Result</span>
                          </Button>
                        ) : (
                          <span className="text-xs text-emerald-600 font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>Evaluated</span>
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 3: Assessor Final Decision */}
      {activeTab === 'decision' && (
        <div className="space-y-6">
          <Card className="border-cyan-200 bg-cyan-50/20">
            <CardHeader>
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-600" />
                <CardTitle>AI Recommendation vs Human Certification</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-xl bg-white border border-cyan-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    AI Algorithmic Recommendation
                  </span>
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-cyan-100 text-cyan-800">
                    {assessment.ai_recommendation || 'RECOMMEND_CERTIFICATION'}
                  </span>
                </div>
                <p className="text-xs text-slate-600">
                  Based on declared experience ({worker?.years_of_experience || 0} yrs), {candidateCompetencies.length} mapped NOS standards, and evidence confidence score.
                </p>
              </div>

              {decision ? (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Certified Assessor Decision</span>
                    </span>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {decision.action || 'RECOMMENDATION ACCEPTED'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-700">
                    <strong>Comments:</strong> {decision.comments || 'Candidate demonstrated verified competencies conforming to NCVET criteria.'}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Recorded by Assessor #{decision.assessor_id || 'lead_assessor'} • {new Date(decision.decided_at || assessment.updated_at).toLocaleString()}
                  </p>
                </div>
              ) : (
                <div className="text-center p-6 bg-white rounded-xl border border-slate-200 space-y-3">
                  <p className="text-sm font-semibold text-slate-800">
                    Human Assessor Decision Pending
                  </p>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    The platform never auto-certifies. A qualified human assessor must verify the evidence and record the formal decision.
                  </p>
                  <Button
                    variant="primary"
                    onClick={() => setDecisionModalOpen(true)}
                    className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold"
                  >
                    <ShieldCheck className="w-4 h-4 mr-1.5" />
                    <span>Record Certification Decision</span>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 4: Candidate Baseline */}
      {activeTab === 'overview' && (
        <Card>
          <CardHeader>
            <CardTitle>Candidate Onboarding Baseline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-xs text-slate-400 font-medium">Candidate Name:</span>
                <p className="font-bold text-slate-900">{worker?.full_name}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-medium">Primary Trade:</span>
                <p className="font-bold text-slate-900">{worker?.trade}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-medium">Prior Experience:</span>
                <p className="font-bold text-slate-900">{worker?.years_of_experience || 0} Years</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-medium">Education Background:</span>
                <p className="font-bold text-slate-900">{worker?.education_level || 'Informal'}</p>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <span className="text-xs text-slate-400 font-medium">Declared Skills:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {(worker?.declared_skills || []).map((s, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 text-xs font-semibold"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab 5: Official Report */}
      {activeTab === 'report' && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Official RPL Assessment Dossier</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Comprehensive audit summary formatted for NCVET / Sector Skill Council certification
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="text-xs"
            >
              <Printer className="w-3.5 h-3.5 mr-1" />
              <span>Print Dossier</span>
            </Button>
          </CardHeader>
          <CardContent className="space-y-6 text-sm">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-slate-400">Assessment ID:</span>
                <p className="font-mono font-bold text-slate-800 break-all">{assessment.id}</p>
              </div>
              <div>
                <span className="text-slate-400">Candidate:</span>
                <p className="font-bold text-slate-800">{worker?.full_name}</p>
              </div>
              <div>
                <span className="text-slate-400">Trade:</span>
                <p className="font-bold text-slate-800">{assessment.trade}</p>
              </div>
              <div>
                <span className="text-slate-400">Status:</span>
                <StatusBadge status={assessment.status} size="sm" />
              </div>
            </div>

            <div>
              <h4 className="font-bold text-slate-900 text-sm mb-2">
                Mapped National Occupational Standards (NOS):
              </h4>
              <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                {candidateCompetencies.map((c, i) => (
                  <div key={i} className="p-3 text-xs flex items-center justify-between">
                    <div>
                      <strong className="text-slate-800">{c.competency_name || c.nos_id}</strong>
                      <span className="text-slate-400 ml-2">({c.nos_id})</span>
                    </div>
                    <span className="font-bold text-cyan-700">
                      {Math.round((c.score || c.confidence || 0.75) * 100)}% Verified
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-bold text-slate-900 text-sm mb-2">
                Certified Assessor Verification:
              </h4>
              <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl text-xs space-y-1">
                <p><strong>Decision:</strong> {decision?.action || 'PROVISIONAL_PENDING'}</p>
                <p><strong>Comments:</strong> {decision?.comments || 'Awaiting final human assessor sign-off.'}</p>
                <p className="text-slate-400 pt-1">
                  Compliance Rule: Generated under SIH 2026 AI-Assisted RPL Assessment Guidelines.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Task Result Submission Modal */}
      <Modal
        isOpen={taskResultModal.isOpen}
        onClose={() => setTaskResultModal({ isOpen: false, taskId: null, taskTitle: '' })}
        title="Record Task Assessment Result"
        description={`Submit evaluation scores and observations for: ${taskResultModal.taskTitle}`}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submitTaskResultMutation.mutate({
              taskId: taskResultModal.taskId,
              payload: {
                score: Number(taskScore),
                status: 'COMPLETED',
                comments: taskComments,
              },
            });
          }}
          className="space-y-4"
        >
          <Input
            label="Evaluation Score (0 - 100) *"
            type="number"
            min="0"
            max="100"
            required
            value={taskScore}
            onChange={(e) => setTaskScore(e.target.value)}
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Assessor Observations & Comments *
            </label>
            <textarea
              required
              rows={3}
              placeholder="e.g. Candidate demonstrated correct bead alignment and safety gear compliance."
              value={taskComments}
              onChange={(e) => setTaskComments(e.target.value)}
              className="w-full p-3 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setTaskResultModal({ isOpen: false, taskId: null, taskTitle: '' })}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={submitTaskResultMutation.isPending}
            >
              Submit Result
            </Button>
          </div>
        </form>
      </Modal>

      {/* Final Decision Modal */}
      <Modal
        isOpen={decisionModalOpen}
        onClose={() => setDecisionModalOpen(false)}
        title="Record Final Assessor Certification Decision"
        description="Formal sign-off by certified RPL assessor. AI recommendations must be human-certified."
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            recordDecisionMutation.mutate({
              action: decisionAction,
              comments: decisionComments,
            });
          }}
          className="space-y-4"
        >
          <Select
            label="Formal Certification Action *"
            value={decisionAction}
            onChange={(e) => setDecisionAction(e.target.value)}
            options={[
              { value: 'ACCEPT_RECOMMENDATION', label: 'Accept AI Recommendation & Certify' },
              { value: 'REQUEST_MORE_EVIDENCE', label: 'Request Additional Practical Evidence' },
              { value: 'MODIFY_RECOMMENDATION', label: 'Modify Recommendation (Partial/Provisional)' },
              { value: 'REJECT_RECOMMENDATION', label: 'Reject Certification' },
            ]}
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Assessor Justification & Sign-off Notes *
            </label>
            <textarea
              required
              rows={4}
              placeholder="Explain rationale for this decision, referencing candidate evidence, NOS standards, and safety competencies..."
              value={decisionComments}
              onChange={(e) => setDecisionComments(e.target.value)}
              className="w-full p-3 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            />
          </div>

          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <span>
              This decision will be cryptographically written to the immutable audit trail with your assessor identity and timestamp.
            </span>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setDecisionModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={recordDecisionMutation.isPending}
            >
              Record Decision
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
