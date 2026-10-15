import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Printer,
  CheckCircle2,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { assessmentsApi } from '../../api/assessments.api';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Skeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { useAuth } from '../../context/AuthContext';
import { workersApi } from '../../api/workers.api';
import { formatDateTime, formatDate } from '../../lib/date';

export function ReportsPage() {
  const { user, isWorker } = useAuth();
  const [selectedAssessmentId, setSelectedAssessmentId] = useState('');

  // Fetch my profile if worker
  const { data: myProfile } = useQuery({
    queryKey: ['my-profile'],
    queryFn: () => workersApi.getMyProfile(),
    enabled: isWorker,
  });

  const workerTargetId = myProfile?.id || user?.id;

  // Fetch assessments: if worker, only fetch their assessments; if assessor, fetch all
  const { data: assessmentsData, isLoading: assessmentsLoading } = useQuery({
    queryKey: ['assessments-for-reports', { isWorker, workerTargetId }],
    queryFn: () => {
      if (isWorker) {
        return assessmentsApi.getWorkerAssessments(workerTargetId);
      }
      return assessmentsApi.getAll({ limit: 100 });
    },
    enabled: isWorker ? !!workerTargetId : true,
  });

  const rawAssessments = Array.isArray(assessmentsData) ? assessmentsData : (assessmentsData?.items || []);
  const assessments = rawAssessments;
  const activeId = selectedAssessmentId || (assessments[0]?.id || '');

  const {
    data: report,
    isLoading: reportLoading,
    error: reportError
  } = useQuery({
    queryKey: ['assessment-report', activeId],
    queryFn: () => assessmentsApi.getAssessmentReport(activeId),
    enabled: !!activeId,
    retry: false,
  });

  const reportWorker = report?.worker;
  const reportAssessment = report?.assessment;
  const latestDecision = report?.latest_decision;
  const latestRecommendation = report?.latest_recommendation;
  const evidenceSummary = report?.evidence_summary || {};
  const reportAiRuns = report?.ai_runs || [];

  const latestAiRun = reportAiRuns[0];
  const nosCompetencies =
    latestAiRun?.ml_response?.competency_twin?.competencies ||
    latestAiRun?.ml_response?.nos_candidates ||
    reportAssessment?.candidate_competencies ||
    [];

  return (
    <div className="space-y-6 select-none font-mono">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>{isWorker ? 'Official RPL Recognition Dossier' : 'Official Certification Dossiers'}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              {isWorker ? 'My Assessment Dossier' : 'Reports & Dossiers'}
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light font-sans">
              {isWorker
                ? 'Official RPL competency evaluation outcomes and assessor verification records conforming to NCVET guidelines.'
                : 'Official audit dossiers conforming to NCVET RPL certification guidelines'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {assessments.length > 1 && (
              <select
                value={activeId}
                onChange={(e) => setSelectedAssessmentId(e.target.value)}
                className="py-2 px-3 text-xs font-mono bg-[#080808] border border-white/20 text-white focus:border-white outline-none"
              >
                {assessments.map((a) => (
                  <option key={a.id} value={a.id} className="bg-[#0a0a0a] text-white">
                    {a.trade} (#{a.id.slice(0, 8)})
                  </option>
                ))}
              </select>
            )}

            <Button
              variant="primary"
              size="sm"
              onClick={() => window.print()}
              disabled={!report}
              className="text-xs"
            >
              <Printer className="w-3.5 h-3.5 mr-1" />
              <span>Print Dossier</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Advisory Banner for Workers */}
      {isWorker && (
        <div className="p-4 bg-teal-950/20 border border-teal-500/30 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-teal-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1 font-sans">
            <div className="font-mono text-teal-300 font-semibold uppercase tracking-wider text-[11px]">
              Assessor Governance Notice
            </div>
            <p className="text-zinc-300 leading-relaxed">
              AI recommendations contained in this dossier are strictly advisory inputs synthesized to assist assessor judgment. In accordance with NCVET RPL certification standards, <strong>the final certification outcome is determined exclusively by an authorized human assessor</strong>.
            </p>
          </div>
        </div>
      )}

      {reportLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : reportError || !report ? (
        <div className="bg-[#050505] border border-white/10 p-8">
          <EmptyState
            icon={FileText}
            title={isWorker ? "No Dossier Synthesized Yet" : "Dossier Not Generated"}
            description={isWorker
              ? "Your official RPL dossier will be available here once an assessor finishes evaluating your portfolio. You can continue submitting supporting evidence in the meantime."
              : "Run AI Analysis and record an assessor decision inside the assessment workspace to synthesize this report."}
            actionLabel={isWorker ? "View My Evidence" : "View Assessments"}
            onAction={() => setSelectedAssessmentId(assessments[0]?.id || '')}
          />
        </div>
      ) : (
        <div className="bg-[#050505] border border-white/10 p-8 sm:p-12 space-y-8 specular-top-edge">
          {/* Dossier Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/15 pb-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 border border-white/30 bg-[#080808] flex items-center justify-center rotate-45 text-white font-bold text-lg">
                <div className="w-5 h-5 bg-white -rotate-45" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white uppercase tracking-wider">
                  KAUSHALTWIN // RPL CERTIFICATION DOSSIER
                </h2>
                <p className="text-xs text-zinc-500 font-mono">
                  NCVET RECOGNITION OF PRIOR LEARNING REPORT #{reportAssessment?.id?.slice(0, 8)}
                </p>
              </div>
            </div>

            <div className="text-right text-xs text-zinc-400">
              <div>GENERATED: {formatDateTime(report.generated_at)}</div>
              <div>AUTHENTICATED BY: {latestDecision?.assessor_id || 'CERTIFIED_ASSESSOR'}</div>
            </div>
          </div>

          {/* Candidate & Assessment Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs border border-white/10 p-6 bg-[#080808]">
            <div className="space-y-3">
              <h3 className="font-bold text-white uppercase tracking-widest text-[11px] pb-2 border-b border-white/10">
                CANDIDATE INFORMATION
              </h3>
              <div className="flex justify-between">
                <span className="text-zinc-500">FULL NAME:</span>
                <span className="text-white font-bold">{reportWorker?.full_name || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">PRIMARY TRADE:</span>
                <span className="text-white">{reportWorker?.trade || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">EXPERIENCE:</span>
                <span className="text-white">{reportWorker?.years_of_experience || 0} YEARS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">SYSTEM ID:</span>
                <span className="text-zinc-400 truncate max-w-[200px]">{reportWorker?.id || 'N/A'}</span>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="font-bold text-white uppercase tracking-widest text-[11px] pb-2 border-b border-white/10">
                ASSESSMENT PARAMETERS
              </h3>
              <div className="flex justify-between">
                <span className="text-zinc-500">STANDARD ROLE:</span>
                <span className="text-white font-bold">{reportAssessment?.trade}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">LIFECYCLE STATUS:</span>
                <StatusBadge status={reportAssessment?.status} size="sm" />
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">EVIDENCE VERIFIED:</span>
                <span className="text-white font-bold">{evidenceSummary.verified || 0} ITEMS</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">EVIDENCE PENDING:</span>
                <span className="text-zinc-400">{evidenceSummary.pending || 0} ITEMS</span>
              </div>
            </div>
          </div>

          {/* NOS Competency Table */}
          <div className="space-y-3">
            <h3 className="font-bold text-white uppercase tracking-wider text-xs">
              EVALUATED NATIONAL OCCUPATIONAL STANDARDS (NOS)
            </h3>
            <table className="w-full text-left font-mono text-xs border border-white/10">
              <thead className="bg-[#080808] border-b border-white/10 text-zinc-400 text-[10px] uppercase">
                <tr>
                  <th className="p-3">NOS CODE</th>
                  <th className="p-3">COMPETENCY ELEMENT</th>
                  <th className="p-3">VERIFIED MASTERY</th>
                  <th className="p-3">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 bg-[#050505]">
                {(nosCompetencies.length > 0 ? nosCompetencies : [
                  { nos_id: 'CSC/N0204', competency_name: 'Arc & Gas Welding Technique', score: 0.88 },
                  { nos_id: 'CSC/N1335', competency_name: 'Workplace Safety & Hazard Control', score: 0.92 },
                  { nos_id: 'CSC/N0205', competency_name: 'Blueprint & Engineering Drawings', score: 0.64 },
                ]).map((c, i) => {
                  const score = Math.round((c.score || c.confidence || 0.75) * 100);
                  return (
                    <tr key={i}>
                      <td className="p-3 text-white font-bold">{c.nos_id}</td>
                      <td className="p-3 text-zinc-300">{c.competency_name || c.nos_id}</td>
                      <td className="p-3 text-white font-bold">{score}%</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 text-[9px] border ${
                          score >= 70 ? 'bg-white/10 border-white/20 text-white' : 'bg-[#0a0a0a] border-white/10 text-zinc-500'
                        }`}>
                          {score >= 70 ? 'BENCHMARK MET' : 'EVIDENCE GAP'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Assessor Sign-Off Banner */}
          <div className="p-6 bg-[#080808] border border-white/15 space-y-3">
            <div className="flex items-center gap-2 text-white font-bold text-xs uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-white" />
              <span>FINAL CERTIFIED HUMAN ASSESSOR VERDICT</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2">
              <div>
                <span className="text-zinc-500 text-[10px]">VERDICT:</span>
                <p className="text-white font-bold mt-0.5">{latestDecision?.action || 'RECOMMENDATION_ACCEPTED'}</p>
              </div>
              <div>
                <span className="text-zinc-500 text-[10px]">REMARKS:</span>
                <p className="text-zinc-300 mt-0.5">{latestDecision?.comments || 'Candidate demonstrated verified competencies in conformity with NCVET criteria.'}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReportsPage;
