import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import {
  Users,
  ClipboardCheck,
  FileCheck2,
  Clock,
  ArrowRight,
  Plus,
  ChevronRight,
  ShieldCheck,
  Activity,
  Cpu,
  FileText
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { workersApi } from '../../api/workers.api';
import { assessmentsApi } from '../../api/assessments.api';
import { evidenceApi } from '../../api/evidence.api';
import { mlApi } from '../../api/ml.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge, RoleBadge } from '../../components/ui/Badge';
import { Skeleton } from '../../components/ui/Skeleton';

export function DashboardPage() {
  const { user, isAssessor, isAdmin, isWorker } = useAuth();
  const navigate = useNavigate();

  // Backend Queries
  const {
    data: workersData,
    isLoading: workersLoading,
  } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
  });

  const {
    data: assessmentsData,
    isLoading: assessmentsLoading,
  } = useQuery({
    queryKey: ['assessments', { limit: 100 }],
    queryFn: () => assessmentsApi.getAll({ limit: 100 }),
  });

  const {
    data: evidenceData,
    isLoading: evidenceLoading
  } = useQuery({
    queryKey: ['evidence', { limit: 100 }],
    queryFn: () => evidenceApi.getAll({ limit: 100 }),
  });

  const { data: mlHealth } = useQuery({
    queryKey: ['ml-health'],
    queryFn: () => mlApi.getHealth(),
    refetchInterval: 30000,
  });

  const workers = workersData?.items || [];
  const assessments = assessmentsData?.items || [];
  const evidenceList = evidenceData?.items || [];

  // Metrics computation
  const totalWorkers = workersData?.total ?? workers.length;
  const totalAssessments = assessmentsData?.total ?? assessments.length;
  const activeAssessments = assessments.filter(
    (a) => a.status === 'IN_PROGRESS' || a.status === 'DRAFT'
  ).length;
  const decisionsRequired = assessments.filter(
    (a) => a.status === 'READY_FOR_REVIEW' || a.status === 'PENDING_REVIEW'
  ).length;
  const pendingEvidence = evidenceList.filter(
    (e) => e.verification_status === 'PENDING'
  ).length;

  const recentAssessments = [...assessments]
    .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
    .slice(0, 5);

  return (
    <div className="space-y-8 select-none">
      {/* Top Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 relative overflow-hidden specular-top-edge">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>KaushalTwin • Skill Assessment Platform</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              Assessor Dashboard
            </h1>
            <p className="text-zinc-400 text-xs sm:text-sm font-light leading-relaxed">
              Evidence-driven skill assessment platform. Review candidate competency profiles, audit automated standard extractions, and record certified assessor decisions.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {isAssessor && (
              <>
                <Button
                  variant="primary"
                  onClick={() => navigate('/assessments')}
                  className="font-mono"
                >
                  <Plus className="w-3.5 h-3.5 mr-1" />
                  <span>Start Assessment</span>
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => navigate('/workers')}
                  className="font-mono"
                >
                  <Users className="w-3.5 h-3.5 mr-1" />
                  <span>Candidates</span>
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Reassuring Status Line */}
        <div className="mt-6 pt-4 border-t border-white/10 flex flex-wrap items-center justify-between text-[11px] font-sans text-zinc-400 gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-zinc-300">
              <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
              <span className="font-medium">Evaluation Engine Active</span>
            </div>
            <span>•</span>
            <span>NSQF Competency Standards Loaded</span>
            <span>•</span>
            <span>Verified Local Environment</span>
          </div>
          <div className="flex items-center gap-1.5 text-zinc-300">
            <ShieldCheck className="w-3.5 h-3.5 text-white" />
            <span>Assessor-in-the-Loop Governance</span>
          </div>
        </div>
      </div>

      {/* 4 PRIMARY DASHBOARD METRICS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Assigned Workers */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-3">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Candidate Profiles
            </span>
            <Users className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {workersLoading ? <Skeleton className="h-9 w-16" /> : totalWorkers}
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>Candidate pool</span>
            <span className="text-zinc-500">Registered</span>
          </div>
        </div>

        {/* Metric 2: Active Assessments */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-3">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Active Assessments
            </span>
            <Clock className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {assessmentsLoading ? <Skeleton className="h-9 w-16" /> : activeAssessments}
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>In-progress evaluations</span>
            <span className="text-zinc-500">{totalAssessments} total</span>
          </div>
        </div>

        {/* Metric 3: Pending Evidence Reviews */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-3">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Pending Evidence Reviews
            </span>
            <FileCheck2 className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {evidenceLoading ? <Skeleton className="h-9 w-16" /> : pendingEvidence}
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>Portfolio submissions</span>
            <span className="text-zinc-500">Awaiting audit</span>
          </div>
        </div>

        {/* Metric 4: Decisions Required */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-3">
            <span className="font-mono text-[11px] uppercase tracking-wider text-white font-semibold">
              Certifications Pending Review
            </span>
            <ClipboardCheck className="w-4 h-4 text-white" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {assessmentsLoading ? <Skeleton className="h-9 w-16" /> : decisionsRequired}
          </div>
          <div className="mt-3 flex items-center justify-between text-[10px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>Ready for sign-off</span>
            <span className="text-white font-medium">Assessor action</span>
          </div>
        </div>
      </div>

      {/* Main Content Area: Recent Assessments Table & Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Assessments Table (2 cols) */}
        <div className="lg:col-span-2 bg-[#050505] border border-white/10 specular-top-edge">
          <div className="p-5 border-b border-white/10 flex items-center justify-between">
            <div>
              <h2 className="font-sans text-xs font-bold text-white uppercase tracking-wider">
                Recent Candidate Evaluations
              </h2>
              <p className="text-[11px] text-zinc-400 font-light mt-0.5">
                Active candidate submissions and assessment statuses
              </p>
            </div>
            <Link
              to="/assessments"
              className="font-mono text-xs text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="p-0">
            {assessmentsLoading ? (
              <div className="p-6 space-y-3">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : recentAssessments.length === 0 ? (
              <div className="p-12 text-center text-zinc-500 text-xs font-sans">
                No evaluations recorded yet. Start an assessment to begin reviewing candidate competencies.
              </div>
            ) : (
              <div className="divide-y divide-white/5">
                {recentAssessments.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => navigate(`/assessments/${a.id}`)}
                    className="p-4 hover:bg-white/[0.03] transition-colors flex items-center justify-between gap-4 cursor-pointer"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="w-9 h-9 border border-white/15 bg-[#080808] text-white font-mono font-bold flex items-center justify-center text-xs">
                        {a.trade ? a.trade.slice(0, 2).toUpperCase() : 'TR'}
                      </div>
                      <div>
                        <div className="font-mono text-xs font-bold text-white flex items-center gap-2">
                          <span>{a.trade || 'General Trade'}</span>
                          <span className="text-[10px] text-zinc-500 font-normal">
                            #{a.id.slice(0, 8)}
                          </span>
                        </div>
                        <div className="text-[11px] font-mono text-zinc-500 flex items-center gap-2 mt-0.5">
                          <span>Candidate: {a.worker_id.slice(0, 8)}</span>
                          <span>•</span>
                          <span>{new Date(a.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <StatusBadge status={a.status} size="sm" />
                      <ChevronRight className="w-4 h-4 text-zinc-500" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Intelligence Actions & System Guide (1 col) */}
        <div className="space-y-4">
          <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge space-y-4">
            <div className="flex items-center gap-2 text-white font-sans text-xs font-bold tracking-wider uppercase">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>Certification Workflow Guide</span>
            </div>
            
            <div className="space-y-3 font-sans text-xs text-zinc-400">
              <div className="p-3 bg-[#080808] border border-white/5 space-y-1">
                <div className="text-white font-bold text-[11px]">1. Evidence Capture</div>
                <p className="text-[11px] text-zinc-400">
                  Candidate logs prior trade experience, photos, and workplace artifacts.
                </p>
              </div>

              <div className="p-3 bg-[#080808] border border-white/5 space-y-1">
                <div className="text-white font-bold text-[11px]">2. Standard Mapping</div>
                <p className="text-[11px] text-zinc-400">
                  Semantic engine computes skill alignment with National Occupational Standards.
                </p>
              </div>

              <div className="p-3 bg-[#080808] border border-white/5 space-y-1">
                <div className="text-white font-bold text-[11px]">3. Advisory Insights</div>
                <p className="text-[11px] text-zinc-400">
                  Platform highlights competency strengths and flags evidence sufficiency.
                </p>
              </div>

              <div className="p-3 bg-[#080808] border border-white/5 space-y-1">
                <div className="text-white font-bold text-[11px]">4. Assessor Certification</div>
                <p className="text-[11px] text-zinc-400">
                  Certified assessor conducts practical reviews and authorizes final certification.
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/competencies')}
              className="w-full justify-center font-mono text-xs"
            >
              <Cpu className="w-3.5 h-3.5 mr-1 text-white" />
              <span>Explore Competency Matrix</span>
            </Button>
          </div>

          {/* Quick Shortcuts */}
          <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge space-y-2">
            <h3 className="font-sans text-[11px] font-bold text-zinc-400 uppercase tracking-wider mb-2">
              Quick Actions
            </h3>
            <button
              onClick={() => navigate('/evidence')}
              className="w-full flex items-center justify-between p-2.5 bg-[#080808] border border-white/5 hover:border-white/20 text-left transition-colors font-mono text-xs text-zinc-300 hover:text-white cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <FileCheck2 className="w-3.5 h-3.5 text-white" />
                <span>Audit Pending Evidence</span>
              </div>
              <span className="text-[10px] text-zinc-500">{pendingEvidence} items</span>
            </button>
            <button
              onClick={() => navigate('/audit')}
              className="w-full flex items-center justify-between p-2.5 bg-[#080808] border border-white/5 hover:border-white/20 text-left transition-colors font-mono text-xs text-zinc-300 hover:text-white cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-white" />
                <span>Compliance Audit Logs</span>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-zinc-500" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
