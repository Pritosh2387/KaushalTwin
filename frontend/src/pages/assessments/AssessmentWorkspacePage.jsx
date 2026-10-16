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
  RotateCw,
  Plus,
  Printer,
  FileText
} from 'lucide-react';
import { assessmentsApi } from '../../api/assessments.api';
import { workersApi } from '../../api/workers.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Tabs } from '../../components/ui/Tabs';
import { Skeleton } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { Modal } from '../../components/ui/Modal';
import { Select } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { EmptyState } from '../../components/ui/EmptyState';
import { formatDate } from '../../lib/date';

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
  } = useQuery({
    queryKey: ['assessment', id],
    queryFn: () => assessmentsApi.getById(id),
  });

  const { data: worker } = useQuery({
    queryKey: ['worker', assessment?.worker_id],
    queryFn: () => workersApi.getById(assessment.worker_id),
    enabled: !!assessment?.worker_id,
  });

  const { data: tasksData } = useQuery({
    queryKey: ['assessment-tasks', id],
    queryFn: () => assessmentsApi.getTasks(id),
    enabled: !!id,
  });

  const { data: aiRuns } = useQuery({
    queryKey: ['assessment-ai-runs', id],
    queryFn: () => assessmentsApi.getAIResults(id),
    enabled: !!id,
  });

  const { data: recommendation } = useQuery({
    queryKey: ['assessment-recommendation', id],
    queryFn: () => assessmentsApi.getLatestRecommendation(id),
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment', id] });
      queryClient.invalidateQueries({ queryKey: ['assessment-ai-runs', id] });
      setNotification({
        type: 'success',
        message: 'AI ML Analysis completed! NOS mappings and competency vectors updated.',
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
    onSuccess: () => {
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
      queryClient.invalidateQueries({ queryKey: ['assessment-recommendation', id] });
      setDecisionModalOpen(false);
      setNotification({
        type: 'success',
        message: 'Certified Assessor Decision permanently written to audit ledger.',
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
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (assessmentError || !assessment) {
    return (
      <div className="space-y-4">
        <Button variant="outline" size="sm" onClick={() => navigate('/assessments')}>
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          <span>Back to Assessments</span>
        </Button>
        <Alert variant="error" title="Assessment Not Found">
          {assessmentError?.response?.data?.detail || 'Unable to load assessment workspace.'}
        </Alert>
      </div>
    );
  }

  const tasks = tasksData?.items || assessment.tasks || [];
  const latestAiRun = aiRuns?.items?.[0] || aiRuns?.[0] || null;
  const candidateCompetencies = latestAiRun?.ml_response?.competency_twin?.competencies ||
    latestAiRun?.ml_response?.nos_candidates ||
    latestAiRun?.ml_response?.results?.competencies ||
    [];
  const decision = recommendation?.decision || null;
  const aiRecommendation = recommendation?.recommendation ||
    latestAiRun?.ml_response?.recommendation ||
    latestAiRun?.recommendation ||
    null;

  const tabs = [
    { id: 'analysis', label: 'AI Competency Analysis', icon: Cpu, badge: candidateCompetencies.length || (latestAiRun ? '✓' : null) },
    { id: 'tasks', label: 'Adaptive Tasks', icon: Layers, badge: tasks.length },
    { id: 'decision', label: 'Assessor Decision', icon: ShieldCheck, badge: decision ? 'Decided' : 'Pending' },
    { id: 'overview', label: 'Candidate Baseline', icon: ClipboardCheck },
    { id: 'report', label: 'Official Dossier', icon: FileText },
  ];

  return (
    <div className="space-y-6 select-none font-mono">
      {/* Back button & Breadcrumb */}
      <div className="flex items-center justify-between text-xs">
        <button
          onClick={() => navigate('/assessments')}
          className="inline-flex items-center gap-1.5 text-zinc-400 hover:text-white transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Assessments</span>
        </button>
        <span className="text-zinc-500 text-[10px]">
          Assessment #{assessment.id.slice(0, 8)}
        </span>
      </div>

      {notification && (
        <Alert variant={notification.type} onClose={() => setNotification(null)}>
          {notification.message}
        </Alert>
      )}

      {/* Main Workspace Header Card */}
      <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight uppercase">
              {assessment.trade}
            </h1>
            <StatusBadge status={assessment.status} />
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-400">
            <span>Candidate: <strong className="text-white">{worker?.full_name || assessment.worker_id}</strong></span>
            <span>•</span>
            <span>Experience: <strong className="text-white">{worker?.years_of_experience || 0} Years</strong></span>
            <span>•</span>
            <span>Created: {formatDate(assessment.created_at)}</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {assessment.status === 'DRAFT' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => startMutation.mutate()}
              loading={startMutation.isPending}
            >
              <Play className="w-3.5 h-3.5 mr-1" />
              <span>Start Assessment</span>
            </Button>
          )}

          <Button
            variant="primary"
            size="sm"
            onClick={() => analyzeMutation.mutate()}
            loading={analyzeMutation.isPending}
          >
            <Sparkles className="w-3.5 h-3.5 mr-1" />
            <span>Analyze Competencies ↗</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => setDecisionModalOpen(true)}
          >
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            <span>Record Assessor Decision</span>
          </Button>
        </div>
      </div>

      {/* Workspace Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: AI Competency Analysis */}
      {activeTab === 'analysis' && (
        <div className="space-y-6">
          <div className="p-5 bg-[#050505] border border-white/15 specular-top-edge flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 border border-white/20 bg-[#080808] text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-sans font-bold text-white text-xs uppercase tracking-wider">
                  Integrated Evaluation Pipeline
                </h3>
                <p className="text-[11px] text-zinc-400 font-sans mt-0.5 max-w-xl">
                  Extracts declared skills, computes semantic alignment with National Occupational Standards (NOS), and audits evidence sufficiency.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => checkEvidenceMutation.mutate()}
                loading={checkEvidenceMutation.isPending}
                className="text-[10px]"
              >
                <FileCheck2 className="w-3 h-3 mr-1" />
                <span>Verify Evidence</span>
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => analyzeMutation.mutate()}
                loading={analyzeMutation.isPending}
                className="text-[10px]"
              >
                <RotateCw className="w-3 h-3 mr-1" />
                <span>Re-run Analysis</span>
              </Button>
            </div>
          </div>

          {/* Candidate Competencies Grid */}
          <div className="bg-[#050505] border border-white/10 specular-top-edge">
            <div className="p-5 border-b border-white/10 flex items-center justify-between">
              <div>
                <h2 className="font-sans text-xs font-bold text-white uppercase tracking-wider">
                  Identified Standards &amp; Competencies
                </h2>
                <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                  Semantic mappings against National Occupational Standards
                </p>
              </div>
              <span className="text-[10px] px-2 py-0.5 bg-[#0a0a0a] border border-white/15 text-zinc-300 font-sans">
                {candidateCompetencies.length} Competencies
              </span>
            </div>

            <div className="p-6">
              {candidateCompetencies.length === 0 ? (
                <EmptyState
                  icon={Cpu}
                  title="No Competencies Evaluated Yet"
                  description="Run AI Analysis to extract competencies and map them against National Occupational Standards (NOS)."
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
                        className="p-4 bg-[#080808] border border-white/10 hover:border-white/25 transition-all space-y-3"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-[9px] font-mono font-bold uppercase tracking-widest px-1.5 py-0.5 bg-white/10 text-white border border-white/20">
                              {comp.nos_id || 'NOS-STD-2026'}
                            </span>
                            <h4 className="font-sans font-bold text-white text-xs mt-1.5">
                              {comp.competency_name || comp.nos_id}
                            </h4>
                          </div>
                          <div className="text-right">
                            <span className="text-base font-bold text-white">
                              {score}%
                            </span>
                            <div className="text-[9px] text-zinc-400 font-sans uppercase tracking-wider">
                              Proficiency
                            </div>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-[#121214] h-1.5 overflow-hidden">
                          <div
                            className="h-full bg-white transition-all"
                            style={{ width: `${score}%` }}
                          />
                        </div>

                        <div className="flex items-center justify-between text-[10px] text-zinc-400 font-sans pt-1 border-t border-white/5">
                          <span>Evidence: {comp.evidence_count || 1} samples</span>
                          <span className={score >= 70 ? 'text-zinc-200' : 'text-zinc-400 font-medium'}>
                            {score >= 70 ? 'Standard Met' : 'Demonstration Needed'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Adaptive Assessment Tasks */}
      {activeTab === 'tasks' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="font-sans text-xs font-bold text-white uppercase tracking-wider">
                Adaptive Practical Tasks
              </h3>
              <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                Targeted practical evaluations generated to verify hands-on trade skills.
              </p>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => recommendTaskMutation.mutate()}
              loading={recommendTaskMutation.isPending}
              className="text-xs"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              <span>Generate Next Task ↗</span>
            </Button>
          </div>

          <div className="bg-[#050505] border border-white/10 specular-top-edge">
            {tasks.length === 0 ? (
              <div className="p-8">
                <EmptyState
                  icon={Layers}
                  title="No Adaptive Tasks Assigned"
                  description="Click 'Recommend Next Task' to generate practical or diagnostic assessment exercises."
                  actionLabel="Recommend Next Task"
                  onAction={() => recommendTaskMutation.mutate()}
                />
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {tasks.map((t, idx) => (
                  <div
                    key={t.id || idx}
                    className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-1 max-w-xl">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-white">
                          TASK #{idx + 1}: {t.task_name || t.selected_task || t.title || 'Practical Assessment Task'}
                        </span>
                        <StatusBadge status={t.status || 'PENDING'} size="sm" />
                      </div>
                      <p className="text-[11px] text-zinc-400 font-sans leading-relaxed">
                        {t.description || t.reason || 'Assess execution speed, technique compliance, and safety equipment handling.'}
                      </p>
                      <div className="flex items-center gap-3 text-[10px] text-zinc-500 pt-1">
                        {t.priority_score && (
                          <span>AI PRIORITY: {(t.priority_score * 100).toFixed(0)}%</span>
                        )}
                        {t.score !== undefined && (
                          <span className="text-white font-bold">
                            ASSESSOR SCORE: {t.score}%
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
                              taskTitle: t.task_name || t.selected_task || t.title || 'Task Evaluation',
                            })
                          }
                          className="text-[10px]"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                          <span>RECORD SCORE</span>
                        </Button>
                      ) : (
                        <span className="text-[10px] text-zinc-300 font-bold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                          <span>EVALUATED</span>
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Assessor Final Decision */}
      {activeTab === 'decision' && (
        <div className="space-y-6">
          <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
            <div className="flex items-center gap-2 text-white text-xs font-bold uppercase tracking-wider pb-3 border-b border-white/10 font-sans">
              <ShieldCheck className="w-4 h-4 text-white" />
              <span>Advisory Recommendation &amp; Certified Assessor Review</span>
            </div>

            <div className="p-4 bg-[#080808] border border-white/10 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-zinc-400">
                  AI Advisory Recommendation
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 bg-white/10 text-white border border-white/20">
                  {aiRecommendation ? aiRecommendation.replace(/_/g, ' ') : 'Pending Analysis'}
                </span>
              </div>
              <p className="text-xs text-zinc-300 font-sans leading-relaxed">
                Based on declared experience ({worker?.years_of_experience || 0} years), {candidateCompetencies.length} mapped standards, and multi-modal evidence confidence scores.
              </p>
            </div>

            {decision ? (
              <div className="p-4 bg-[#080808] border border-white/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                    <span>Certified Assessor Decision</span>
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-white text-black font-bold">
                    {decision.action ? decision.action.replace(/_/g, ' ') : 'Certification Decision Recorded'}
                  </span>
                </div>
                <p className="text-xs text-zinc-300 font-sans">
                  <strong>Notes:</strong> {decision.comments || 'No remarks provided.'}
                </p>
                <p className="text-[10px] text-zinc-500 font-sans pt-1">
                  Recorded by Assessor #{decision.assessor_id || 'lead_assessor'} • {new Date(decision.decided_at || assessment.updated_at).toLocaleString()}
                </p>
              </div>
            ) : (
              <div className="text-center p-8 bg-[#080808] border border-white/10 space-y-3">
                <p className="text-xs font-sans font-bold text-white uppercase tracking-wider">
                  Assessor Review &amp; Certification Decision Required
                </p>
                <p className="text-[11px] text-zinc-400 max-w-md mx-auto font-sans leading-relaxed">
                  The platform never certifies automatically. A certified assessor must review all evidence and record the formal decision.
                </p>
                <Button
                  variant="primary"
                  onClick={() => setDecisionModalOpen(true)}
                  className="text-xs font-sans"
                >
                  <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                  <span>Record Certification Decision ↗</span>
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Candidate Baseline */}
      {activeTab === 'overview' && (
        <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider pb-3 border-b border-white/10">
            CANDIDATE ONBOARDING BASELINE
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-zinc-500 text-[10px]">CANDIDATE NAME:</span>
              <p className="text-white font-bold">{worker?.full_name}</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">PRIMARY TRADE:</span>
              <p className="text-white font-bold">{worker?.trade}</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">YEARS OF EXPERIENCE:</span>
              <p className="text-white font-bold">{worker?.years_of_experience || 0} Years</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">EDUCATION:</span>
              <p className="text-white font-bold">{worker?.education_level || 'Informal'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Official Report */}
      {activeTab === 'report' && (
        <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                OFFICIAL RPL ASSESSMENT DOSSIER
              </h2>
              <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
                Formatted for NCVET / Sector Skill Council compliance
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.print()}
              className="text-xs"
            >
              <Printer className="w-3.5 h-3.5 mr-1" />
              <span>PRINT DOSSIER</span>
            </Button>
          </div>

          <div className="p-4 bg-[#080808] border border-white/10 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-zinc-500 text-[10px]">WORKSPACE:</span>
              <p className="text-white font-bold truncate">#{assessment.id.slice(0, 8)}</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">CANDIDATE:</span>
              <p className="text-white font-bold">{worker?.full_name}</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">TRADE:</span>
              <p className="text-white font-bold">{assessment.trade}</p>
            </div>
            <div>
              <span className="text-zinc-500 text-[10px]">STATUS:</span>
              <div className="pt-0.5"><StatusBadge status={assessment.status} size="sm" /></div>
            </div>
          </div>
        </div>
      )}

      {/* Task Result Modal */}
      <Modal
        isOpen={taskResultModal.isOpen}
        onClose={() => setTaskResultModal({ isOpen: false, taskId: null, taskTitle: '' })}
        title="Record Task Result"
        description={`Submit evaluation score for: ${taskResultModal.taskTitle}`}
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
            label="Evaluation Score (0 - 100)"
            type="number"
            min="0"
            max="100"
            required
            value={taskScore}
            onChange={(e) => setTaskScore(e.target.value)}
          />
          <Input
            label="Assessor Observations"
            placeholder="e.g. Correct welding travel speed, root face gap within tolerance."
            value={taskComments}
            onChange={(e) => setTaskComments(e.target.value)}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button
              variant="outline"
              onClick={() => setTaskResultModal({ isOpen: false, taskId: null, taskTitle: '' })}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={submitTaskResultMutation.isPending}
              className="text-xs"
            >
              Save Result ↗
            </Button>
          </div>
        </form>
      </Modal>

      {/* Final Decision Recording Modal */}
      <Modal
        isOpen={decisionModalOpen}
        onClose={() => setDecisionModalOpen(false)}
        title="Record Certified Assessor Decision"
        description="Formal sign-off of candidate recognition. This decision is permanently archived."
      >
        <div className="space-y-4">
          <Select
            label="Certification Decision"
            value={decisionAction}
            onChange={(e) => setDecisionAction(e.target.value)}
            options={[
              { value: 'ACCEPT_RECOMMENDATION', label: 'Accept Recommendation — Full RPL Certification' },
              { value: 'MODIFY_RECOMMENDATION', label: 'Modify Recommendation — Partial Certification / Gap Bridge' },
              { value: 'REJECT_RECOMMENDATION', label: 'Reject Recommendation — Insufficient Evidence Benchmark' },
              { value: 'REQUEST_MORE_EVIDENCE', label: 'Request More Evidence — Additional Practical Demonstration' },
            ]}
          />

          <Input
            label="Decision Justification"
            required
            placeholder="e.g. Assessor verified practical joint execution and portfolio authenticity."
            value={decisionComments}
            onChange={(e) => setDecisionComments(e.target.value)}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button
              variant="outline"
              onClick={() => setDecisionModalOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              type="primary"
              variant="primary"
              onClick={() =>
                recordDecisionMutation.mutate({
                  action: decisionAction,
                  comments: decisionComments || 'Assessor formal review recorded.',
                })
              }
              loading={recordDecisionMutation.isPending}
              className="text-xs"
            >
              Confirm Decision ↗
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default AssessmentWorkspacePage;
