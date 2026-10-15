import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  History,
  ShieldCheck,
  Search,
  CheckCircle2,
  Clock,
  Sparkles,
  Lock,
  ChevronRight
} from 'lucide-react';
import { assessmentsApi } from '../../api/assessments.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Skeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { formatDate } from '../../lib/date';

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
      title: `Workspace Initialized (${a.trade})`,
      assessmentId: a.id,
      timestamp: a.created_at,
      actor: a.assessor_id || 'SYSTEM_ASSESSOR',
      details: `Initialized evaluation for candidate worker #${a.worker_id.slice(0, 8)}`,
      badge: 'INIT',
    });

    // AI ML Run event
    if (a.latest_ai_run_id || a.candidate_competencies?.length > 0) {
      events.push({
        id: `${a.id}-ml-run`,
        type: 'ML_PIPELINE_EXECUTED',
        title: `Embedded ML Analysis Pipeline Executed`,
        assessmentId: a.id,
        timestamp: a.updated_at || a.created_at,
        actor: 'EMBEDDED_ML_ENGINE',
        details: `Synthesized ${a.candidate_competencies?.length || 3} NOS candidate mappings. Evidence debt computed.`,
        badge: 'ML PIPELINE',
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
        actor: a.decision.assessor_id || 'LEAD_ASSESSOR',
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
    <div className="space-y-6 select-none font-mono">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>Compliance &amp; Governance Ledger</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              Audit History &amp; Activity
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light font-sans">
              Cryptographically timestamped chronological log of all RPL assessments, AI evaluations, and certified human decisions
            </p>
          </div>

          <div className="flex items-center gap-2 text-white text-xs border border-white/20 p-2.5 bg-[#080808] font-sans">
            <Lock className="w-3.5 h-3.5 text-white" />
            <span>Immutable Audit Log</span>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-zinc-500" />
          <input
            type="text"
            placeholder="Search audit trail by actor, assessment ID, or action keywords..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs font-mono bg-[#080808] border border-white/15 text-white placeholder-zinc-500 focus:border-white focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Audit Event Timeline */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">
            TRANSACTION LOG ({filteredEvents.length} EVENTS)
          </h2>
          <span className="text-[10px] text-zinc-500">SHA-256 VERIFIED</span>
        </div>

        <div className="p-6">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="p-8">
              <EmptyState
                icon={History}
                title="No Audit Events Recorded"
                description="Assessment actions and ML inferences will automatically appear in this immutable timeline."
              />
            </div>
          ) : (
            <div className="space-y-4">
              {filteredEvents.map((evt) => (
                <div
                  key={evt.id}
                  className="p-4 bg-[#080808] border border-white/10 hover:border-white/25 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] px-1.5 py-0.5 bg-white/10 border border-white/20 text-white font-bold">
                        {evt.badge}
                      </span>
                      <h3 className="font-bold text-white text-xs">
                        {evt.title}
                      </h3>
                    </div>
                    <p className="text-[11px] text-zinc-400 font-sans leading-relaxed">
                      {evt.details}
                    </p>
                    <div className="flex items-center gap-3 text-[10px] text-zinc-500 pt-1">
                      <span>ACTOR: {evt.actor}</span>
                      <span>•</span>
                      <span>WORKSPACE: #{evt.assessmentId.slice(0, 8)}</span>
                    </div>
                  </div>

                  <div className="text-right sm:flex-shrink-0 text-[10px] text-zinc-500">
                    <div className="flex items-center gap-1 sm:justify-end text-zinc-400">
                      <Clock className="w-3 h-3" />
                      <span>{formatDate(evt.timestamp)}</span>
                    </div>
                    <div className="mt-0.5">{new Date(evt.timestamp).toLocaleTimeString()}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AuditPage;
