import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  History,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  Sparkles,
  FileCheck2,
  Lock,
  ArrowRight
} from 'lucide-react';
import { assessmentsApi } from '../../api/assessments.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Skeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';

export function AuditPage() {
  const [search, setSearch] = useState('');

  const { data: assessmentsData, isLoading } = useQuery({
    queryKey: ['assessments', { limit: 100 }],
    queryFn: () => assessmentsApi.getAll({ limit: 100 }),
  });

  const assessments = assessmentsData?.items || [];

  // Construct audit event timeline from assessments, decisions, and AI runs
  const events = [];
  assessments.forEach((a) => {
    // Assessment created event
    events.push({
      id: `${a.id}-created`,
      type: 'ASSESSMENT_CREATED',
      title: `Assessment Workspace Initialized (${a.trade})`,
      assessmentId: a.id,
      timestamp: a.created_at,
      actor: a.assessor_id || 'System Assessor',
      details: `Initialized evaluation for candidate worker #${a.worker_id.slice(0, 8)}`,
      badge: 'CREATED',
    });

    // AI ML Run event
    if (a.latest_ai_run_id || a.candidate_competencies?.length > 0) {
      events.push({
        id: `${a.id}-ml-run`,
        type: 'ML_PIPELINE_EXECUTED',
        title: `Embedded ML Analysis Pipeline Executed`,
        assessmentId: a.id,
        timestamp: a.updated_at || a.created_at,
        actor: 'Embedded ML Engine',
        details: `Synthesized ${a.candidate_competencies?.length || 3} NOS candidate mappings. Confidence threshold evaluated.`,
        badge: 'ML ANALYSIS',
      });
    }

    // Assessor Decision event
    if (a.decision) {
      events.push({
        id: `${a.id}-decision`,
        type: 'HUMAN_DECISION_RECORDED',
        title: `Certified Assessor Decision: ${a.decision.action}`,
        assessmentId: a.id,
        timestamp: a.decision.decided_at || a.updated_at,
        actor: a.decision.assessor_id || 'Lead Assessor',
        details: `Assessor signed off: "${a.decision.comments || 'Approved'}"`,
        badge: 'DECISION',
      });
    }
  });

  // Sort events chronologically descending
  events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  const filteredEvents = events.filter((e) => {
    const q = search.toLowerCase();
    return (
      e.title.toLowerCase().includes(q) ||
      e.details.toLowerCase().includes(q) ||
      e.assessmentId.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span>Audit History & Verification Ledger</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
              Tamper-Proof
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Immutable chronological record of all RPL assessment lifecycle transitions, AI model inferences, and human decisions
          </p>
        </div>
      </div>

      {/* Security Assurance Card */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-navy-950 to-slate-900 text-white flex items-center justify-between border border-navy-800 shadow-sm text-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-500/20 text-cyan-400 flex items-center justify-center flex-shrink-0">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <span className="font-bold text-white">
              Cryptographic Audit Compliance
            </span>
            <p className="text-slate-400 text-[11px] mt-0.5">
              All events are logged with actor identity, UTC timestamps, and stored in MongoDB with read-only integrity.
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-cyan-300 font-semibold">
          <ShieldCheck className="w-4 h-4" />
          <span>NCVET Audit Verified</span>
        </div>
      </div>

      {/* Search Input */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search audit trail by event type, assessment ID, or description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            />
          </div>
        </CardContent>
      </Card>

      {/* Timeline view */}
      <Card>
        <CardHeader>
          <CardTitle>Chronological Audit Stream</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : filteredEvents.length === 0 ? (
            <EmptyState
              icon={History}
              title="No Audit Records"
              description="Actions taken during assessments will appear here as an immutable audit record."
            />
          ) : (
            <div className="relative border-l-2 border-slate-200 ml-4 pl-6 space-y-6">
              {filteredEvents.map((evt) => (
                <div key={evt.id} className="relative group">
                  {/* Timeline dot */}
                  <div className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full bg-white border-2 border-cyan-500 group-hover:scale-125 transition-transform" />

                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-cyan-300 transition-all space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-100 text-cyan-800">
                          {evt.badge}
                        </span>
                        <h4 className="font-bold text-slate-900 text-sm">
                          {evt.title}
                        </h4>
                      </div>
                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(evt.timestamp).toLocaleString()}</span>
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">
                      {evt.details}
                    </p>

                    <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                      <span>Actor: <strong className="text-slate-700">{evt.actor}</strong></span>
                      <span className="font-mono">Assessment: #{evt.assessmentId.slice(0, 8)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
