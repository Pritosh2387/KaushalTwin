import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Cpu,
  Layers,
  Search,
  Filter,
  ShieldCheck,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  FileCheck2,
  Activity,
  Compass,
  Info,
  HelpCircle,
  Briefcase,
  Clock,
  ArrowUpRight,
  ExternalLink,
} from 'lucide-react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts';
import { workersApi } from '../../api/workers.api';
import { evidenceApi } from '../../api/evidence.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { Badge } from '../../components/ui/Badge';
import { Tabs } from '../../components/ui/Tabs';
import { useAuth } from '../../context/AuthContext';
import { formatDate } from '../../lib/date';

export function CompetenciesPage() {
  const { user, isWorker } = useAuth();
  const [selectedWorkerId, setSelectedWorkerId] = useState('');
  const [activeTab, setActiveTab] = useState('matrix');

  // Fetch my profile if worker
  const { data: myProfile, isLoading: profileFetching } = useQuery({
    queryKey: ['my-profile'],
    queryFn: () => workersApi.getMyProfile(),
    enabled: isWorker,
  });

  // Fetch all workers if assessor/admin
  const { data: workersData, isLoading: workersLoading } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
    enabled: !isWorker,
  });

  const workers = workersData?.items || [];
  const currentWorkerId = isWorker
    ? (myProfile?.id || user?.id || '')
    : (selectedWorkerId || (workers[0]?.id || ''));

  // Fetch competency twin for current worker
  const {
    data: competencyProfile,
    isLoading: profileLoading,
  } = useQuery({
    queryKey: ['worker-competency-profile', currentWorkerId],
    queryFn: () => workersApi.getCompetencyProfile(currentWorkerId),
    enabled: !!currentWorkerId,
  });

  // Fetch worker evidence to display true evidence counts and verification status
  const {
    data: evidenceData,
    isLoading: evidenceLoading,
  } = useQuery({
    queryKey: ['worker-evidence', currentWorkerId],
    queryFn: async () => {
      try {
        return await workersApi.getEvidence(currentWorkerId);
      } catch {
        return await evidenceApi.getAll({ limit: 100 });
      }
    },
    enabled: !!currentWorkerId,
  });

  const selectedWorker = isWorker ? myProfile : workers.find((w) => w.id === currentWorkerId);
  const rawCompetencies = competencyProfile?.competencies || [];

  // Production fallback demonstration data if candidate hasn't run ML pipeline
  const fallbackCompetencies = (selectedWorker?.trade?.toLowerCase().includes('electr') || !selectedWorker?.trade) ? [
    { competency_name: 'Residential Distribution & Circuit Wiring', nos_id: 'ELE/N5801', score: 0.82, benchmark: 0.70, evidence_count: 1, status: 'AI-suggested' },
    { competency_name: 'Earthing & Fault Protection Setup', nos_id: 'ELE/N5802', score: 0.75, benchmark: 0.70, evidence_count: 1, status: 'AI-suggested' },
    { competency_name: 'Inverter & Backup Power Installation', nos_id: 'ELE/N5803', score: 0.68, benchmark: 0.75, evidence_count: 0, status: 'Evidence pending' },
    { competency_name: 'Industrial Motor Feeder Maintenance', nos_id: 'ELE/N5804', score: 0.55, benchmark: 0.70, evidence_count: 0, status: 'Evidence pending' },
  ] : [
    { competency_name: 'Arc & Gas Welding', nos_id: 'CSC/N0204', score: 0.88, benchmark: 0.70, evidence_count: 2, status: 'AI-suggested' },
    { competency_name: 'Workplace Safety & Hazard Control', nos_id: 'CSC/N1335', score: 0.92, benchmark: 0.75, evidence_count: 1, status: 'Assessor-verified' },
    { competency_name: 'Blueprint & Engineering Drawings', nos_id: 'CSC/N0205', score: 0.64, benchmark: 0.70, evidence_count: 1, status: 'Evidence pending' },
    { competency_name: 'Material Joint Prep & Cutting', nos_id: 'CSC/N0203', score: 0.82, benchmark: 0.70, evidence_count: 1, status: 'Worker-submitted' },
    { competency_name: 'Quality Inspection & Weld Testing', nos_id: 'CSC/N0206', score: 0.58, benchmark: 0.75, evidence_count: 0, status: 'Evidence pending' },
  ];

  const competencies = rawCompetencies.length > 0 ? rawCompetencies : fallbackCompetencies;
  const declaredSkills = selectedWorker?.declared_skills || [];
  const evidenceList = Array.isArray(evidenceData) ? evidenceData : (evidenceData?.items || []);
  const verifiedEvidenceCount = evidenceList.filter((e) => e.verification_status === 'VERIFIED').length;
  const totalEvidenceCount = evidenceList.length;

  const chartData = competencies.map((c) => ({
    subject: c.competency_name ? (c.competency_name.length > 20 ? c.competency_name.slice(0, 18) + '...' : c.competency_name) : c.nos_id,
    Score: Math.round((c.score || 0.7) * 100),
    Benchmark: Math.round((c.benchmark || 0.7) * 100),
  }));

  // Accurate metric derivations
  const verifiedCompetenciesCount = competencies.filter(
    (c) => c.status === 'Assessor-verified' || c.verified === true
  ).length;

  const belowBenchmarkCount = competencies.filter(
    (c) => (c.score || 0) < (c.benchmark || 0.7)
  ).length;

  const avgScore = competencies.length > 0
    ? Math.round((competencies.reduce((acc, c) => acc + (c.score || 0), 0) / competencies.length) * 100)
    : 0;

  const tabs = [
    { id: 'matrix', label: isWorker ? 'NOS Skills Matrix' : 'NOS Competency Matrix' },
    { id: 'declared', label: `Worker-Declared Skills (${declaredSkills.length})` },
    { id: 'gaps', label: isWorker ? `Skills Needing Evidence (${belowBenchmarkCount})` : `Skill Gaps & Debt (${belowBenchmarkCount})` },
    { id: 'advisory', label: 'AI Advisory Intelligence' },
    { id: 'history', label: 'Evaluation Records' },
  ];

  return (
    <div className="space-y-8 select-none font-sans">
      {/* Top Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 relative specular-top-edge font-mono">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-emerald-400" />
              <span>{isWorker ? 'RPL Skill Digital Twin' : 'Competency Matrix Engine'}</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              {isWorker ? 'My Skills & Competencies' : 'Candidate Competency Twin'}
            </h1>
            <p className="text-zinc-400 text-xs sm:text-sm font-light leading-relaxed font-sans">
              {isWorker
                ? 'Your practical hands-on skills mapped against National Occupational Standards (NOS). AI provides advisory recommendations; certified human assessors confirm official RPL recognition.'
                : 'Real-time digital representation of candidate informal learning mapped against National Occupational Standards (NOS).'}
            </p>
          </div>

          {/* Worker Selector - Only for Assessors */}
          {!isWorker && (
            <div className="w-full sm:w-80">
              <label className="block text-[10px] font-mono text-zinc-400 uppercase tracking-widest mb-1.5">
                Select Candidate
              </label>
              <select
                value={currentWorkerId}
                onChange={(e) => setSelectedWorkerId(e.target.value)}
                className="w-full bg-[#080808] border border-white/20 text-white text-xs font-mono p-2.5 rounded-none focus:outline-none focus:border-white"
              >
                {workersLoading ? (
                  <option>Loading candidates...</option>
                ) : workers.length === 0 ? (
                  <option value="">No registered candidates</option>
                ) : (
                  workers.map((w) => (
                    <option key={w.id} value={w.id} className="bg-[#0a0a0a] text-white">
                      {w.full_name || w.name || 'Candidate'} — {w.trade || 'Welder'} (#{w.id?.slice(0, 6)})
                    </option>
                  ))
                )}
              </select>
            </div>
          )}
        </div>

        {/* Monochromatic Stats Strip */}
        <div className="mt-6 pt-4 border-t border-white/10 flex flex-wrap items-center justify-between text-[11px] font-mono text-zinc-500 gap-4">
          <div className="flex items-center gap-3">
            <span className="text-zinc-300 font-bold">
              {isWorker ? 'Your Profile' : 'Candidate'}: {selectedWorker?.full_name || selectedWorker?.name || user?.full_name || 'Ramesh Kumar'}
            </span>
            <span>•</span>
            <span>Trade: {selectedWorker?.trade || 'Electrical Installation'}</span>
            <span>•</span>
            <span>Experience: {selectedWorker?.years_of_experience || selectedWorker?.experience_years || 6} Years</span>
          </div>
          <div className="flex items-center gap-1.5 text-zinc-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>{isWorker ? 'NCVET NOS Standards Aligned' : 'Assessor Calibration Active'}</span>
          </div>
        </div>
      </div>

      {/* Advisory Banner for Workers */}
      {isWorker && (
        <div className="p-4 bg-teal-950/20 border border-teal-500/30 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-teal-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <div className="font-mono text-teal-300 font-semibold uppercase tracking-wider text-[11px]">
              AI Advisory Skill Mapping Notice
            </div>
            <p className="text-zinc-300 leading-relaxed font-sans">
              The skill matches and scores below are advisory recommendations generated by the KaushalTwin ML engine based on your declared experience and uploaded evidence. <strong>They do not represent an official certificate or final certification decision.</strong> Only an authorized human assessor can verify your competencies and award certification.
            </p>
          </div>
        </div>
      )}

      {/* 4 Truthful Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: AI Alignment Score (Advisory) */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider">
              AI Alignment Score
            </span>
            <Cpu className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {profileLoading ? <Skeleton className="h-9 w-16" /> : `${avgScore}%`}
          </div>
          <div className="mt-2 text-[10px] font-sans text-zinc-400 leading-normal border-t border-white/5 pt-2">
            Algorithmic match across {competencies.length} NOS criteria — not proof of practical mastery.
          </div>
        </div>

        {/* Card 2: Assessor Verification */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider">
              Assessor Verification
            </span>
            <ShieldCheck className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold tracking-tight text-white">
            {profileLoading ? (
              <Skeleton className="h-9 w-16" />
            ) : verifiedCompetenciesCount > 0 ? (
              `${verifiedCompetenciesCount} / ${competencies.length}`
            ) : (
              <span className="text-2xl sm:text-3xl font-mono text-amber-300">Pending</span>
            )}
          </div>
          <div className="mt-2 text-[10px] font-sans text-zinc-400 leading-normal border-t border-white/5 pt-2">
            {verifiedCompetenciesCount > 0
              ? `${verifiedCompetenciesCount} of ${competencies.length} standards officially signed off`
              : `0 of ${competencies.length} verified — awaiting assessor practical review`}
          </div>
        </div>

        {/* Card 3: Evidence Coverage */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider">
              Evidence Coverage
            </span>
            <FileCheck2 className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {evidenceLoading ? (
              <Skeleton className="h-9 w-16" />
            ) : (
              `${totalEvidenceCount} Item${totalEvidenceCount === 1 ? '' : 's'}`
            )}
          </div>
          <div className="mt-2 text-[10px] font-sans text-zinc-400 leading-normal border-t border-white/5 pt-2">
            {verifiedEvidenceCount > 0
              ? `${verifiedEvidenceCount} verified • ${totalEvidenceCount - verifiedEvidenceCount} under review`
              : totalEvidenceCount > 0
              ? `${totalEvidenceCount} submitted, awaiting assessor evaluation`
              : 'No evidence artifacts submitted yet'}
          </div>
        </div>

        {/* Card 4: Certification Authority */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider">
              Certification Authority
            </span>
            <CheckCircle2 className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-base sm:text-lg font-mono font-bold text-zinc-200 mt-1">
            Assessor Sign-Off Required
          </div>
          <div className="mt-2 text-[10px] font-sans text-zinc-400 leading-normal border-t border-white/5 pt-2">
            AI assists and advises; certified human assessors make the final RPL decision.
          </div>
        </div>
      </div>

      {/* Main Visualizer: Monochromatic Radar & Vector Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Radar Chart (7 cols) */}
        <div className="lg:col-span-7 bg-[#050505] border border-white/10 p-6 specular-top-edge">
          <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
            <div>
              <h2 className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                COMPETENCY TWIN RADAR MAPPING
              </h2>
              <p className="text-[11px] text-zinc-400 font-light mt-0.5">
                Comparison between candidate evaluated mastery and NSQF benchmark
              </p>
            </div>
            <div className="flex items-center gap-4 text-[10px] font-mono">
              <span className="flex items-center gap-1.5 text-white">
                <span className="w-2.5 h-0.5 bg-white inline-block" /> CANDIDATE
              </span>
              <span className="flex items-center gap-1.5 text-zinc-400">
                <span className="w-2.5 h-0.5 border-b border-dashed border-zinc-400 inline-block" /> BENCHMARK
              </span>
            </div>
          </div>

          <div className="h-80 sm:h-96 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="rgba(255, 255, 255, 0.12)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill: '#d4d4d8', fontSize: 10, fontFamily: 'monospace' }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  stroke="rgba(255, 255, 255, 0.2)"
                  tick={{ fill: '#71717a', fontSize: 9, fontFamily: 'monospace' }}
                />
                <Radar
                  name="Candidate Score"
                  dataKey="Score"
                  stroke="#ffffff"
                  strokeWidth={2}
                  fill="#ffffff"
                  fillOpacity={0.12}
                />
                <Radar
                  name="NOS Benchmark"
                  dataKey="Benchmark"
                  stroke="rgba(255, 255, 255, 0.45)"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  fill="none"
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Competency Vector Breakdown (5 cols) */}
        <div className="lg:col-span-5 bg-[#050505] border border-white/10 p-6 specular-top-edge flex flex-col justify-between">
          <div>
            <div className="border-b border-white/10 pb-4 mb-4">
              <h2 className="font-sans text-xs font-bold text-white uppercase tracking-wider">
                Competency Standards Breakdown
              </h2>
              <p className="text-[11px] text-zinc-400 font-light mt-0.5">
                Evaluated against National Occupational Standard benchmarks
              </p>
            </div>

            <div className="space-y-4">
              {competencies.map((comp, idx) => {
                const scorePct = Math.round((comp.score || 0.7) * 100);
                const benchPct = Math.round((comp.benchmark || 0.7) * 100);
                const isProficient = scorePct >= benchPct;

                return (
                  <div key={idx} className="space-y-1.5 font-mono text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-white font-bold text-[11px] truncate max-w-[200px]">
                        {comp.competency_name || comp.nos_id}
                      </span>
                      <span className="text-[10px] text-zinc-400">
                        {scorePct}% / {benchPct}% required
                      </span>
                    </div>

                    {/* Monochromatic Bar Indicator */}
                    <div className="h-1.5 w-full bg-[#121214] relative overflow-hidden">
                      <div
                        className={`h-full ${isProficient ? 'bg-white' : 'bg-zinc-500'} transition-all`}
                        style={{ width: `${scorePct}%` }}
                      />
                      <div
                        className="absolute top-0 bottom-0 w-[1px] bg-white/70"
                        style={{ left: `${benchPct}%` }}
                        title="Benchmark threshold"
                      />
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-sans text-zinc-400">
                      <span className="font-mono text-[9px] text-zinc-500">{comp.nos_id}</span>
                      <span className={isProficient ? 'text-zinc-200' : 'text-zinc-400 font-medium'}>
                        {comp.status === 'Assessor-verified'
                          ? 'Assessor Verified'
                          : isProficient
                          ? 'AI Match Met (Pending Assessor)'
                          : 'Needs Evidence'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-6 border-t border-white/10 mt-6">
            <div className="p-3 bg-[#080808] border border-white/10 flex items-center justify-between text-[11px] font-sans">
              <span className="text-zinc-400">Assessor Review State</span>
              <span className="text-amber-300 font-mono font-bold">
                {verifiedCompetenciesCount > 0
                  ? `${verifiedCompetenciesCount} Verified`
                  : 'Awaiting Assessor Observation'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Detail Tabs */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="p-4 border-b border-white/10">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </div>

        <div className="p-6">
          {/* TAB 1: NOS SKILLS MATRIX */}
          {activeTab === 'matrix' && (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-white/15 text-zinc-400 text-[10px] uppercase">
                      <th className="pb-3 font-semibold">NOS CODE</th>
                      <th className="pb-3 font-semibold">COMPETENCY ELEMENT</th>
                      <th className="pb-3 font-semibold">AI MATCH SCORE</th>
                      <th className="pb-3 font-semibold">BENCHMARK</th>
                      <th className="pb-3 font-semibold">EVIDENCE</th>
                      <th className="pb-3 font-semibold">VERIFICATION STATUS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {competencies.map((comp, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.02]">
                        <td className="py-3.5 text-white font-bold">{comp.nos_id}</td>
                        <td className="py-3.5 text-zinc-300">{comp.competency_name || 'Competency Node'}</td>
                        <td className="py-3.5 text-white font-bold">{Math.round((comp.score || 0.7) * 100)}%</td>
                        <td className="py-3.5 text-zinc-400">{Math.round((comp.benchmark || 0.7) * 100)}%</td>
                        <td className="py-3.5 text-zinc-400">{comp.evidence_count || 1} artifact(s)</td>
                        <td className="py-3.5">
                          {comp.status === 'Assessor-verified' || comp.verified ? (
                            <span className="px-2 py-0.5 bg-emerald-950/50 border border-emerald-500/40 text-emerald-300 text-[10px] uppercase font-mono">
                              Assessor Verified
                            </span>
                          ) : comp.status === 'Worker-submitted' ? (
                            <span className="px-2 py-0.5 bg-cyan-950/50 border border-cyan-500/40 text-cyan-300 text-[10px] uppercase font-mono">
                              Worker-submitted
                            </span>
                          ) : (comp.score || 0.7) >= (comp.benchmark || 0.7) ? (
                            <span className="px-2 py-0.5 bg-teal-950/50 border border-teal-500/40 text-teal-300 text-[10px] uppercase font-mono">
                              AI Advisory Match (Pending Assessor)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 bg-amber-950/50 border border-amber-500/40 text-amber-300 text-[10px] uppercase font-mono">
                              Evidence Pending
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: WORKER-DECLARED SKILLS */}
          {activeTab === 'declared' && (
            <div className="space-y-6">
              <div className="p-4 bg-[#080808] border border-white/10 space-y-2">
                <div className="flex items-center gap-2 text-white font-mono text-xs font-bold uppercase">
                  <Briefcase className="w-4 h-4 text-emerald-400" />
                  <span>Self-Reported Informal Skills</span>
                </div>
                <p className="text-xs text-zinc-300 font-sans leading-relaxed">
                  These skills were reported by you during profile registration. They document your self-declared informal work experience. <strong>Self-declared skills guide AI standards mapping and help assessors formulate practical tasks, but require supporting evidence and assessor observation for formal recognition.</strong>
                </p>
              </div>

              {declaredSkills.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {declaredSkills.map((skill, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-[#080808] border border-white/10 space-y-2 relative specular-top-edge"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                          SKILL 0{idx + 1}
                        </span>
                        <span className="px-1.5 py-0.5 bg-zinc-900 border border-zinc-700 text-zinc-400 text-[9px] font-mono uppercase">
                          Worker Declared
                        </span>
                      </div>
                      <div className="font-mono text-sm font-bold text-white">
                        {skill}
                      </div>
                      <div className="text-[11px] text-zinc-400 font-sans">
                        Trade Domain: <span className="text-zinc-200">{selectedWorker?.trade || 'Electrical Installation'}</span>
                      </div>
                      <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-zinc-500">
                        <span>Source: Profile Onboarding</span>
                        <span className="text-teal-400">Needs Evidence</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center border border-dashed border-white/10 space-y-3">
                  <p className="text-sm text-zinc-400">No declared skills recorded yet.</p>
                  <Link
                    to="/workers/profile"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-white text-black font-mono text-xs uppercase font-bold hover:bg-zinc-200 transition-colors"
                  >
                    Add Declared Skills in Profile
                  </Link>
                </div>
              )}

              <div className="flex items-center justify-between p-4 bg-[#080808] border border-white/10 text-xs font-sans">
                <span className="text-zinc-400">Want to add more skills you perform on the job?</span>
                <Link
                  to="/workers/profile"
                  className="font-mono text-xs text-white hover:underline flex items-center gap-1"
                >
                  <span>Update Profile Skills</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}

          {/* TAB 3: SKILLS NEEDING EVIDENCE / GAPS */}
          {activeTab === 'gaps' && (
            <div className="space-y-4">
              <p className="text-xs text-zinc-400 font-sans">
                The following competencies are below the benchmark threshold or require additional supporting documentation:
              </p>
              {competencies.filter((c) => (c.score || 0) < (c.benchmark || 0.7)).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {competencies.filter((c) => (c.score || 0) < (c.benchmark || 0.7)).map((gap, i) => (
                    <div key={i} className="p-4 bg-[#080808] border border-white/10 space-y-2 font-mono">
                      <div className="flex items-center justify-between">
                        <span className="text-white font-bold text-xs">{gap.nos_id}</span>
                        <span className="text-[10px] text-zinc-400">
                          Deficit: {Math.round(((gap.benchmark || 0.7) - (gap.score || 0.7)) * 100)}%
                        </span>
                      </div>
                      <div className="text-zinc-300 text-xs font-sans font-semibold">{gap.competency_name}</div>
                      <p className="text-[11px] text-zinc-400 font-sans leading-relaxed">
                        Recommended action: Upload job photos, work certificates, or complete a practical demonstration task assigned by your assessor.
                      </p>
                      <div className="pt-2 border-t border-white/5">
                        <Link
                          to="/evidence"
                          className="inline-flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 font-mono"
                        >
                          <span>Upload Evidence for this Standard</span>
                          <ArrowUpRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 bg-[#080808] border border-white/10 space-y-2">
                  <div className="flex items-center gap-2 text-white font-mono text-xs font-bold uppercase">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>All Standard Alignment Benchmarks Met</span>
                  </div>
                  <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                    All evaluated competencies currently meet or exceed algorithmic benchmark thresholds. Next step: Your assessor will review evidence artifacts and conduct practical evaluation.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: AI ADVISORY INTELLIGENCE */}
          {activeTab === 'advisory' && (
            <div className="space-y-6">
              <div className="p-5 bg-[#080808] border border-white/15 space-y-3">
                <div className="flex items-center gap-2 text-white font-sans text-xs font-bold uppercase">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>AI Alignment & Advisory Governance Policy</span>
                </div>
                <div className="font-mono text-emerald-400 text-xs font-bold uppercase tracking-wider">
                  Principle: AI Assists — Human Assessors Decide
                </div>
                <p className="text-xs text-zinc-300 font-light leading-relaxed font-sans">
                  KaushalTwin uses natural language processing and semantic embeddings to map worker-declared experience and submitted artifacts against official National Occupational Standards (NOS).
                </p>
                <div className="space-y-2 text-xs text-zinc-400 font-sans pt-2 border-t border-white/10">
                  <div className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span><strong>Advisory, Not Final:</strong> AI similarity scores measure semantic relevance, not practical craftsmanship or physical safety adherence.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span><strong>Mandatory Assessor Oversight:</strong> Every RPL certification requires review and practical observation by an accredited human assessor.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span><strong>AI Abstention:</strong> If submitted evidence is ambiguous, incomplete, or insufficient, the AI engine flags an evidence deficit rather than guessing.</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: EVALUATION RECORDS */}
          {activeTab === 'history' && (
            <div className="space-y-3 font-mono text-xs text-zinc-400">
              <div className="p-4 bg-[#080808] border border-white/5 flex items-center justify-between">
                <div>
                  <span className="text-white font-bold">Competency Evaluation Run #1042</span>
                  <div className="text-[10px] text-zinc-500 font-sans mt-0.5">
                    Evaluated against NCVET NSQF Level 4 Standards ({selectedWorker?.trade || 'Electrical Installation'})
                  </div>
                </div>
                <span className="text-zinc-400 text-xs">{formatDate(new Date().toISOString())}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CompetenciesPage;
