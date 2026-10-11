import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import {
  Users,
  ClipboardCheck,
  FileCheck2,
  Clock,
  ArrowRight,
  Sparkles,
  Plus,
  AlertCircle,
  CheckCircle2,
  Cpu,
  ChevronRight,
  TrendingUp,
  ShieldCheck,
  BookOpen
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
import { Alert } from '../../components/ui/Alert';

export function DashboardPage() {
  const { user, isAssessor, isAdmin, isWorker } = useAuth();
  const navigate = useNavigate();

  // Queries
  const {
    data: workersData,
    isLoading: workersLoading,
    error: workersError
  } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
  });

  const {
    data: assessmentsData,
    isLoading: assessmentsLoading,
    error: assessmentsError
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
  const awaitingReview = assessments.filter(
    (a) => a.status === 'READY_FOR_REVIEW'
  ).length;
  const pendingEvidence = evidenceList.filter(
    (e) => e.verification_status === 'PENDING'
  ).length;
  const completedAssessments = assessments.filter(
    (a) => a.status === 'COMPLETED' || a.status === 'REVIEWED'
  ).length;

  const recentAssessments = [...assessments]
    .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome Header */}
      <div className="bg-gradient-to-r from-navy-950 via-slate-900 to-navy-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden border border-navy-800">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-cyan-500/10 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                SIH 2026 RPL Framework
              </span>
              <span className="text-xs text-slate-400">
                National Occupational Standards (NOS)
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
              Welcome back, {user?.full_name?.split(' ')[0] || 'Assessor'}
            </h1>
            <p className="text-slate-300 text-sm max-w-2xl leading-relaxed">
              AI-assisted Recognition of Prior Learning platform. Track informal skills, map candidate competencies to NOS standards, and conduct transparent human-verified evaluations.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            {isAssessor && (
              <>
                <Button
                  variant="primary"
                  onClick={() => navigate('/assessments')}
                  className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold shadow-md shadow-cyan-500/20"
                >
                  <Plus className="w-4 h-4 mr-1.5" />
                  <span>New Assessment</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/workers')}
                  className="border-slate-700 text-slate-200 hover:bg-navy-800 hover:text-white"
                >
                  <Users className="w-4 h-4 mr-1.5" />
                  <span>Manage Workers</span>
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Embedded ML Health strip */}
        <div className="mt-6 pt-4 border-t border-navy-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  mlHealth?.status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                }`}
              />
              <span className="text-slate-300 font-semibold">
                Embedded ML Intelligence:
              </span>
              <span className="text-cyan-300">
                {mlHealth?.models?.skill_extractor ? 'Active' : 'Standby'}
              </span>
            </div>
            <span className="text-slate-600">•</span>
            <span>Task Recommender: Active</span>
            <span className="text-slate-600">•</span>
            <span>Competency Twin: Synchronized</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>Human In The Loop Certified</span>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Workers */}
        <Card className="hover:border-cyan-500/40">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Assigned Workers
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {workersLoading ? <Skeleton className="h-8 w-14" /> : totalWorkers}
              </h3>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span>RPL Candidate Pool</span>
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
              <Users className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        {/* Active Assessments */}
        <Card className="hover:border-cyan-500/40">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Active Assessments
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {assessmentsLoading ? <Skeleton className="h-8 w-14" /> : activeAssessments}
              </h3>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-amber-500" />
                <span>In-progress evaluations</span>
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
              <Clock className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        {/* Awaiting Review */}
        <Card className="hover:border-cyan-500/40">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Awaiting Decision
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {assessmentsLoading ? <Skeleton className="h-8 w-14" /> : awaitingReview}
              </h3>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-cyan-500" />
                <span>AI recommendation ready</span>
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center font-bold">
              <ClipboardCheck className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>

        {/* Pending Evidence */}
        <Card className="hover:border-cyan-500/40">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Pending Evidence
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {evidenceLoading ? <Skeleton className="h-8 w-14" /> : pendingEvidence}
              </h3>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                <FileCheck2 className="w-3.5 h-3.5 text-emerald-500" />
                <span>Requires verification</span>
              </p>
            </div>
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <FileCheck2 className="w-6 h-6" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content: Recent Assessments & Quick Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Assessments List (2 cols) */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div>
              <CardTitle>Recent Assessments</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Active candidates undergoing competency verification
              </p>
            </div>
            <Link
              to="/assessments"
              className="text-xs font-semibold text-cyan-600 hover:text-cyan-700 flex items-center gap-1"
            >
              <span>View all</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {assessmentsLoading ? (
              <div className="p-6 space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : recentAssessments.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No assessments found. Create an assessment to get started.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {recentAssessments.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => navigate(`/assessments/${a.id}`)}
                    className="p-4 hover:bg-slate-50/80 transition-colors flex items-center justify-between gap-4 cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 font-bold flex items-center justify-center text-xs">
                        {a.trade ? a.trade.slice(0, 2).toUpperCase() : 'TR'}
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                          <span>{a.trade || 'General Trade'}</span>
                          <span className="text-xs font-normal text-slate-400">
                            • #{a.id.slice(0, 8)}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">
                          <span>Worker ID: {a.worker_id.slice(0, 8)}...</span>
                          <span>•</span>
                          <span>{new Date(a.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <StatusBadge status={a.status} size="sm" />
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* AI RPL Workflow Guide & Quick Tools (1 col) */}
        <div className="space-y-4">
          <Card className="bg-gradient-to-br from-slate-900 to-navy-950 text-white border-navy-800">
            <CardContent className="p-5 space-y-4">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold text-xs tracking-wider uppercase">
                <Sparkles className="w-4 h-4" />
                <span>RPL Intelligence Workflow</span>
              </div>
              <h3 className="text-base font-bold text-white leading-snug">
                How KaushalTwin Works
              </h3>
              <ol className="space-y-3 text-xs text-slate-300">
                <li className="flex gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center justify-center flex-shrink-0 font-bold text-[10px]">
                    1
                  </span>
                  <span>
                    <strong className="text-white">Profile & Evidence:</strong> Worker records declared skills, work samples, and experience.
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center justify-center flex-shrink-0 font-bold text-[10px]">
                    2
                  </span>
                  <span>
                    <strong className="text-white">ML Analysis:</strong> Skills extracted and mapped to candidate NOS standards with confidence scores.
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center justify-center flex-shrink-0 font-bold text-[10px]">
                    3
                  </span>
                  <span>
                    <strong className="text-white">Adaptive Tasks:</strong> System recommends target tasks to fill verified evidence gaps.
                  </span>
                </li>
                <li className="flex gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 flex items-center justify-center flex-shrink-0 font-bold text-[10px]">
                    4
                  </span>
                  <span>
                    <strong className="text-white">Assessor Decision:</strong> Certified human assessor reviews AI reasoning and certifies outcome.
                  </span>
                </li>
              </ol>

              <div className="pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/competencies')}
                  className="w-full justify-center border-slate-700 text-slate-200 hover:bg-navy-900 hover:text-white text-xs"
                >
                  <Cpu className="w-3.5 h-3.5 mr-1 text-cyan-400" />
                  <span>Inspect Competency Twin</span>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Quick Shortcuts */}
          <Card>
            <CardContent className="p-4 space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                Quick Shortcuts
              </h4>
              <button
                onClick={() => navigate('/evidence')}
                className="w-full flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 text-left transition-colors text-xs font-semibold text-slate-700"
              >
                <div className="flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-600" />
                  <span>Review Pending Evidence</span>
                </div>
                <span className="text-xs text-slate-400">{pendingEvidence}</span>
              </button>
              <button
                onClick={() => navigate('/audit')}
                className="w-full flex items-center justify-between p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 text-left transition-colors text-xs font-semibold text-slate-700"
              >
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-cyan-600" />
                  <span>Audit History & Logs</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
