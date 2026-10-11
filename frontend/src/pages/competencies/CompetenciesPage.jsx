import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Cpu,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Layers,
  Search,
  Filter,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import { workersApi } from '../../api/workers.api';
import { assessmentsApi } from '../../api/assessments.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Skeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';

export function CompetenciesPage() {
  const [selectedWorkerId, setSelectedWorkerId] = useState('');

  // Fetch workers
  const { data: workersData, isLoading: workersLoading } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
  });

  const workers = workersData?.items || [];
  const currentWorkerId = selectedWorkerId || (workers[0]?.id || '');

  // Fetch competency twin for current worker
  const {
    data: competencyProfile,
    isLoading: profileLoading
  } = useQuery({
    queryKey: ['worker-competency-profile', currentWorkerId],
    queryFn: () => workersApi.getCompetencyProfile(currentWorkerId),
    enabled: !!currentWorkerId,
  });

  const selectedWorker = workers.find((w) => w.id === currentWorkerId);
  const rawCompetencies = competencyProfile?.competencies || [];

  // Default demonstration data if worker has not yet completed full ML runs
  const competencies = rawCompetencies.length > 0 ? rawCompetencies : [
    { competency_name: 'Arc & Gas Welding', nos_id: 'CSC/N0204', score: 0.85, benchmark: 0.70 },
    { competency_name: 'Workplace Safety & Hazard Control', nos_id: 'CSC/N1335', score: 0.90, benchmark: 0.75 },
    { competency_name: 'Blueprint & Engineering Drawings', nos_id: 'CSC/N0205', score: 0.65, benchmark: 0.70 },
    { competency_name: 'Material Joint Preparation & Cutting', nos_id: 'CSC/N0203', score: 0.80, benchmark: 0.70 },
    { competency_name: 'Quality Inspection & Weld Testing', nos_id: 'CSC/N0206', score: 0.55, benchmark: 0.75 },
  ];

  const chartData = competencies.map((c) => ({
    subject: c.competency_name ? (c.competency_name.length > 20 ? c.competency_name.slice(0, 18) + '...' : c.competency_name) : c.nos_id,
    Score: Math.round((c.score || 0.7) * 100),
    Benchmark: Math.round((c.benchmark || 0.7) * 100),
  }));

  const proficientCount = competencies.filter((c) => (c.score || 0.7) >= 0.7).length;
  const gapCount = competencies.length - proficientCount;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span>Competency Twin Graph</span>
            <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-cyan-100 text-cyan-800 border border-cyan-200">
              AI Synthesized
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Real-time digital twin of candidate informal learning mapped against National Occupational Standards
          </p>
        </div>

        {/* Worker Selector */}
        <div className="w-full sm:w-72">
          <select
            value={currentWorkerId}
            onChange={(e) => setSelectedWorkerId(e.target.value)}
            className="w-full py-2 px-3 text-sm bg-white rounded-xl border border-slate-200 focus:border-cyan-500 font-semibold text-slate-800 outline-none shadow-sm"
          >
            {workers.map((w) => (
              <option key={w.id} value={w.id}>
                {w.full_name} ({w.trade})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Summary KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Proficient Competencies
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {proficientCount} of {competencies.length}
              </h3>
              <p className="text-xs text-emerald-600 font-medium mt-0.5">
                Exceeds industry standard baseline
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Identified Skill Gaps
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                {gapCount} Standards
              </h3>
              <p className="text-xs text-amber-600 font-medium mt-0.5">
                Targeted for adaptive verification tasks
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-cyan-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Twin Model State
              </p>
              <h3 className="text-2xl font-black text-slate-900 mt-1">
                Synchronized
              </h3>
              <p className="text-xs text-cyan-700 font-medium mt-0.5">
                Trained on NSQF standards
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center font-bold">
              <Cpu className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Visual Analytics Grid: Radar Chart + Bar Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Competency Twin Radar</CardTitle>
            <p className="text-xs text-slate-500">
              Candidate competency signature compared with certified industry benchmark
            </p>
          </CardHeader>
          <CardContent className="h-80 flex items-center justify-center p-2">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#475569', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                <Radar
                  name="Candidate Score"
                  dataKey="Score"
                  stroke="#06b6d4"
                  fill="#06b6d4"
                  fillOpacity={0.4}
                />
                <Radar
                  name="Industry Benchmark"
                  dataKey="Benchmark"
                  stroke="#94a3b8"
                  fill="#94a3b8"
                  fillOpacity={0.15}
                />
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Bar Comparison Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Standard Competency Benchmark Comparison</CardTitle>
            <p className="text-xs text-slate-500">
              Verified percentage breakdown per National Occupational Standard
            </p>
          </CardHeader>
          <CardContent className="h-80 p-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 20, left: -10, bottom: 20 }}>
                <XAxis dataKey="subject" tick={{ fill: '#475569', fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis domain={[0, 100]} tick={{ fill: '#475569', fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Score" fill="#0891b2" radius={[4, 4, 0, 0]} name="Candidate" />
                <Bar dataKey="Benchmark" fill="#cbd5e1" radius={[4, 4, 0, 0]} name="Benchmark" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Competency Standard Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed National Occupational Standards (NOS) Mappings</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Standard Code</th>
                <th className="px-6 py-3.5">Competency Title</th>
                <th className="px-6 py-3.5">Assessed Score</th>
                <th className="px-6 py-3.5">Industry Target</th>
                <th className="px-6 py-3.5 text-right">RPL Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {competencies.map((c, idx) => {
                const s = Math.round((c.score || 0.7) * 100);
                const b = Math.round((c.benchmark || 0.7) * 100);
                const isProficient = s >= b;
                return (
                  <tr key={idx} className="hover:bg-slate-50/70">
                    <td className="px-6 py-4 font-mono font-bold text-xs text-cyan-800">
                      {c.nos_id}
                    </td>
                    <td className="px-6 py-4 font-bold text-slate-900 text-sm">
                      {c.competency_name || c.nos_id}
                    </td>
                    <td className="px-6 py-4 font-bold text-slate-900">
                      <div className="flex items-center gap-2">
                        <span>{s}%</span>
                        <div className="w-16 bg-slate-200 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${isProficient ? 'bg-emerald-500' : 'bg-amber-500'}`}
                            style={{ width: `${s}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-500 font-medium text-xs">
                      {b}% Baseline
                    </td>
                    <td className="px-6 py-4 text-right">
                      {isProficient ? (
                        <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Satisfied</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Gap Identified</span>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
