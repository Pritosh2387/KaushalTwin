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

export function ReportsPage() {
  const [selectedAssessmentId, setSelectedAssessmentId] = useState('');

  // Fetch all assessments for the selector
  const { data: assessmentsData } = useQuery({
    queryKey: ['assessments', { limit: 100 }],
    queryFn: () => assessmentsApi.getAll({ limit: 100 }),
  });

  const assessments = assessmentsData?.items || [];
  const activeId = selectedAssessmentId || (assessments[0]?.id || '');

  // Fetch report — actual schema from backend:
  // { generated_at, worker, assessment, evidence_summary, ai_runs, tasks, latest_recommendation, latest_decision, audit_timeline }
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

  // Extract fields using the actual backend schema
  const reportWorker = report?.worker;
  const reportAssessment = report?.assessment;
  const latestDecision = report?.latest_decision;
  const latestRecommendation = report?.latest_recommendation;
  const evidenceSummary = report?.evidence_summary || {};
  const reportAiRuns = report?.ai_runs || [];

  // Derive competency list from the latest AI run's ml_response
  const latestAiRun = reportAiRuns[0];
  const nosCompetencies =
    latestAiRun?.ml_response?.competency_twin?.competencies ||
    latestAiRun?.ml_response?.nos_candidates ||
    reportAssessment?.candidate_competencies ||
    [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            RPL Assessment Dossiers &amp; Reports
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Official audit-ready evaluation reports conforming to NCVET RPL certification guidelines
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={activeId}
            onChange={(e) => setSelectedAssessmentId(e.target.value)}
            className="py-2 px-3 text-sm bg-white rounded-xl border border-slate-200 focus:border-cyan-500 font-semibold text-slate-800 outline-none shadow-sm"
          >
            {assessments.length === 0 && (
              <option value="">No assessments available</option>
            )}
            {assessments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.trade} (#{a.id.slice(0, 8)})
              </option>
            ))}
          </select>

          <Button
            variant="outline"
            onClick={() => window.print()}
            className="text-xs font-bold"
            disabled={!report}
          >
            <Printer className="w-4 h-4 mr-1.5" />
            <span>Print Report</span>
          </Button>
        </div>
      </div>

      {reportLoading ? (
        <Skeleton className="h-96 w-full rounded-2xl" />
      ) : reportError ? (
        <Card className="p-8">
          <EmptyState
            icon={FileText}
            title="Report Unavailable"
            description="This assessment does not have a completed report yet. Complete the assessment and record a final decision to generate the official dossier."
          />
        </Card>
      ) : !report ? (
        <Card className="p-8">
          <EmptyState
            icon={FileText}
            title="No Report Available"
            description="Select an active assessment to generate its official RPL dossier."
          />
        </Card>
      ) : (
        /* Printable Report Dossier Card */
        <Card className="border-slate-300 shadow-md print:shadow-none print:border-none">
          <CardContent className="p-6 sm:p-10 space-y-8">
            {/* Report Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b-2 border-slate-900 pb-6 gap-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-navy-950 text-cyan-400 font-black flex items-center justify-center text-xl shadow-md">
                  KT
                </div>
                <div>
                  <h2 className="text-xl font-black text-slate-900 uppercase tracking-tight">
                    KaushalTwin RPL Skill Assessment Dossier
                  </h2>
                  <p className="text-xs text-slate-500 font-semibold">
                    Recognition of Prior Learning • National Skills Qualifications Framework (NSQF)
                  </p>
                </div>
              </div>

              <div className="text-right text-xs">
                <div className="font-mono text-slate-400">Ref: {reportAssessment?.id || activeId}</div>
                <div className="text-slate-600 font-semibold mt-0.5">
                  Generated: {report.generated_at
                    ? new Date(report.generated_at).toLocaleDateString()
                    : new Date().toLocaleDateString()}
                </div>
              </div>
            </div>

            {/* Candidate & Assessment Metadata Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div>
                <span className="text-slate-400 font-medium">Candidate Name:</span>
                <p className="font-bold text-slate-900 text-sm mt-0.5">
                  {reportWorker?.full_name || 'RPL Candidate'}
                </p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Target Trade:</span>
                <p className="font-bold text-slate-900 text-sm mt-0.5">
                  {reportAssessment?.trade || 'Not specified'}
                </p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Prior Experience:</span>
                <p className="font-bold text-slate-900 text-sm mt-0.5">
                  {reportWorker?.years_of_experience || 0} Years
                </p>
              </div>
              <div>
                <span className="text-slate-400 font-medium">Lifecycle Status:</span>
                <div className="mt-0.5">
                  <StatusBadge status={reportAssessment?.status || 'DRAFT'} size="sm" />
                </div>
              </div>
            </div>

            {/* Evidence Summary Stats */}
            {Object.keys(evidenceSummary).length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  1. Evidence Portfolio Summary
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {Object.entries(evidenceSummary).map(([key, value]) => (
                    <div key={key} className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-center">
                      <div className="font-black text-slate-900 text-lg">{value}</div>
                      <div className="text-slate-500 capitalize">{key.replace(/_/g, ' ')}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Declared Skills */}
            <div className="space-y-2">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                {Object.keys(evidenceSummary).length > 0 ? '2' : '1'}. Candidate Declared Skill Inventory
              </h3>
              <div className="flex flex-wrap gap-2">
                {(reportWorker?.declared_skills || []).length > 0 ? (
                  reportWorker.declared_skills.map((s, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded bg-slate-100 text-slate-800 text-xs font-semibold">
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-400 italic">No skills declared</span>
                )}
              </div>
            </div>

            {/* NOS Competency Evaluation */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                {Object.keys(evidenceSummary).length > 0 ? '3' : '2'}. National Occupational Standards (NOS) Mappings
              </h3>
              {nosCompetencies.length === 0 ? (
                <div className="p-4 rounded-xl border border-slate-200 text-xs text-slate-500 italic text-center">
                  No NOS mappings yet — run AI analysis on the assessment to generate competency mappings.
                </div>
              ) : (
                <div className="overflow-x-auto border border-slate-200 rounded-xl">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase">
                      <tr>
                        <th className="px-4 py-2.5">NOS Code</th>
                        <th className="px-4 py-2.5">Standard Title</th>
                        <th className="px-4 py-2.5">Confidence Score</th>
                        <th className="px-4 py-2.5 text-right">RPL Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {nosCompetencies.map((c, idx) => {
                        const score = Math.round((c.score || c.confidence || 0.7) * 100);
                        const ok = score >= 70;
                        return (
                          <tr key={idx} className="hover:bg-slate-50/50">
                            <td className="px-4 py-3 font-mono font-bold text-cyan-800">{c.nos_id || '—'}</td>
                            <td className="px-4 py-3 font-semibold text-slate-900">{c.competency_name || c.nos_id}</td>
                            <td className="px-4 py-3 font-bold text-slate-900">{score}%</td>
                            <td className="px-4 py-3 text-right">
                              <span className={`font-bold px-2 py-0.5 rounded text-xs ${ok ? 'text-emerald-700 bg-emerald-50' : 'text-amber-700 bg-amber-50'}`}>
                                {ok ? 'Satisfied' : 'Gap Identified'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* AI Recommendation vs Assessor Decision */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-cyan-50/50 border border-cyan-200 space-y-2 text-xs">
                <div className="flex items-center gap-1.5 text-cyan-800 font-bold uppercase tracking-wider">
                  <Cpu className="w-4 h-4 text-cyan-600" />
                  <span>AI ML System Recommendation</span>
                </div>
                <div className="font-bold text-slate-900 text-sm">
                  {latestRecommendation?.recommendation ||
                    latestAiRun?.recommendation ||
                    latestAiRun?.run_status ||
                    'Pending Analysis'}
                </div>
                <p className="text-slate-600">
                  Algorithmic verification across submitted work samples, declared experience, and adaptive task performance.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200 space-y-2 text-xs">
                <div className="flex items-center gap-1.5 text-emerald-800 font-bold uppercase tracking-wider">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Human Assessor Formal Certification</span>
                </div>
                <div className="font-bold text-slate-900 text-sm">
                  {latestDecision?.action || 'Pending Human Sign-off'}
                </div>
                <p className="text-slate-700">
                  {latestDecision?.comments ||
                    'No assessor decision recorded yet. A qualified human assessor must review and certify.'}
                </p>
              </div>
            </div>

            {/* Signature Block */}
            <div className="pt-8 border-t border-slate-200 grid grid-cols-2 gap-8 text-xs">
              <div className="space-y-1">
                <div className="h-10 border-b border-dashed border-slate-300 flex items-end">
                  {latestDecision ? (
                    <span className="font-serif italic text-slate-700 text-sm">
                      {latestDecision.assessor_id
                        ? `Assessor #${latestDecision.assessor_id.slice(0, 8)}`
                        : 'Certified Assessor'}
                    </span>
                  ) : (
                    <span className="text-slate-400 italic text-xs">Awaiting signature</span>
                  )}
                </div>
                <p className="font-bold text-slate-800">Certified RPL Lead Assessor</p>
                <p className="text-slate-400">NCVET Registered Assessment Authority</p>
              </div>

              <div className="space-y-1 text-right">
                <div className="h-10 border-b border-dashed border-slate-300 flex items-end justify-end">
                  <span className="font-mono text-xs text-slate-600">
                    ID: {activeId.slice(0, 16)}...
                  </span>
                </div>
                <p className="font-bold text-slate-800">Digital Audit Reference</p>
                <p className="text-slate-400">MongoDB Ledger Record</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
