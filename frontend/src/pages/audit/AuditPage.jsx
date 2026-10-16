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
  RotateCw,
  AlertTriangle,
  Info,
  Hash,
  Filter
} from 'lucide-react';
import { auditApi } from '../../api/audit.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { Alert } from '../../components/ui/Alert';
import { formatDate } from '../../lib/date';

export function AuditPage() {
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  // 1. Fetch real audit events from backend ledger
  const {
    data: auditData,
    isLoading: eventsLoading,
    refetch: refetchEvents,
  } = useQuery({
    queryKey: ['audit-events', { search, action: actionFilter }],
    queryFn: () => auditApi.getAuditEvents({ search: search || undefined, action: actionFilter || undefined, limit: 100 }),
  });

  // 2. Fetch real cryptographic integrity verification
  const {
    data: integrityData,
    isLoading: verifying,
    refetch: refetchVerification,
  } = useQuery({
    queryKey: ['audit-verification'],
    queryFn: () => auditApi.verifyLedger(),
  });

  const rawEvents = auditData?.items || [];
  const totalCount = auditData?.total ?? rawEvents.length;

  const getActionBadgeColor = (action = '') => {
    if (action.includes('VERIFIED') || action.includes('ACCEPT')) {
      return 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300';
    }
    if (action.includes('REJECT') || action.includes('TAMPER')) {
      return 'bg-rose-950/60 border-rose-500/40 text-rose-300';
    }
    if (action.includes('ML') || action.includes('AI')) {
      return 'bg-cyan-950/60 border-cyan-500/40 text-cyan-300';
    }
    if (action.includes('DECISION') || action.includes('CERTIF')) {
      return 'bg-purple-950/60 border-purple-500/40 text-purple-300';
    }
    return 'bg-white/10 border-white/20 text-zinc-300';
  };

  return (
    <div className="space-y-6 select-none font-mono">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
              <span>Compliance &amp; Governance Ledger</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              Audit History &amp; Activity
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light font-sans">
              Cryptographically timestamped chronological log of all RPL evidence submissions, reviews, ML inferences, and assessor decisions
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                refetchEvents();
                refetchVerification();
              }}
              loading={verifying}
              className="text-xs font-mono"
            >
              <RotateCw className="w-3.5 h-3.5 mr-1.5" />
              <span>Verify Ledger Integrity</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Cryptographic Integrity Status Card */}
      <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 border border-white/20 bg-[#080808] flex items-center justify-center flex-shrink-0 mt-0.5">
              <Lock className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Cryptographic Hash-Chain Status:
                </span>
                {verifying ? (
                  <span className="text-[10px] px-2 py-0.5 bg-zinc-800 text-zinc-300 border border-zinc-700">
                    VERIFYING LEDGER...
                  </span>
                ) : integrityData?.status === 'VERIFIED' ? (
                  <span className="text-[10px] px-2 py-0.5 bg-emerald-950/60 text-emerald-400 border border-emerald-500/40 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>VERIFIED (SHA-256 CHAIN CONTINUOUS)</span>
                  </span>
                ) : integrityData?.status === 'EMPTY' ? (
                  <span className="text-[10px] px-2 py-0.5 bg-zinc-800 text-zinc-400 border border-zinc-700">
                    NO EVENTS RECORDED
                  </span>
                ) : (
                  <span className="text-[10px] px-2 py-0.5 bg-rose-950/60 text-rose-400 border border-rose-500/40 font-bold flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    <span>TAMPER DETECTED</span>
                  </span>
                )}
              </div>
              <p className="text-[11px] text-zinc-400 font-sans mt-1">
                {integrityData?.explanation || 'Independent SHA-256 hash chaining verifies the chronological succession and content immutability of recorded events.'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 text-right text-xs">
            <div className="p-2.5 bg-[#080808] border border-white/10 text-center">
              <span className="text-[10px] text-zinc-500 block">TOTAL</span>
              <span className="font-bold text-white">{integrityData?.total_events ?? totalCount}</span>
            </div>
            <div className="p-2.5 bg-[#080808] border border-white/10 text-center">
              <span className="text-[10px] text-emerald-400 block">VERIFIED</span>
              <span className="font-bold text-emerald-400">{integrityData?.verified_events ?? 0}</span>
            </div>
            <div className="p-2.5 bg-[#080808] border border-white/10 text-center">
              <span className="text-[10px] text-rose-400 block">CORRUPTED</span>
              <span className="font-bold text-rose-400">{integrityData?.corrupted_events ?? 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-zinc-500" />
          <input
            type="text"
            placeholder="Search audit trail by actor, entity ID, action keywords..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs font-mono bg-[#080808] border border-white/15 text-white placeholder-zinc-500 focus:border-white focus:outline-none transition-colors"
          />
        </div>

        <div className="w-full sm:w-64">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="w-full py-2 px-3 text-xs font-mono bg-[#080808] border border-white/15 text-white focus:border-white focus:outline-none"
          >
            <option value="">All Action Types</option>
            <option value="EVIDENCE_SUBMITTED">Evidence Submitted</option>
            <option value="EVIDENCE_VERIFIED">Evidence Verified</option>
            <option value="EVIDENCE_REJECTED">Evidence Rejected</option>
            <option value="ASSESSMENT_CREATED">Assessment Created</option>
            <option value="ASSESSMENT_STARTED">Assessment Started</option>
            <option value="ASSESSOR_DECISION_RECORDED">Assessor Decision Recorded</option>
            <option value="DOSSIER_GENERATED">Dossier Generated</option>
            <option value="WORKER_UPDATED">Worker Profile Updated</option>
          </select>
        </div>
      </div>

      {/* Audit Event Timeline */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider">
            TRANSACTION LOG ({rawEvents.length} OF {totalCount} EVENTS)
          </h2>
          <span className="text-[10px] text-zinc-500 font-mono">
            {integrityData?.is_valid ? 'SHA-256 CHAIN VERIFIED' : 'TAMPER DETECTION ACTIVE'}
          </span>
        </div>

        <div className="p-6">
          {eventsLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : rawEvents.length === 0 ? (
            <div className="p-8">
              <EmptyState
                icon={History}
                title="No Audit Events Found"
                description="User actions, evidence reviews, and certification decisions will automatically record into this immutable ledger."
              />
            </div>
          ) : (
            <div className="space-y-4">
              {rawEvents.map((evt) => {
                const actionBadgeClass = getActionBadgeColor(evt.action);
                const hasPrevHash = Boolean(evt.prev_hash && evt.prev_hash !== '0'.repeat(64));

                return (
                  <div
                    key={evt.id || evt._id}
                    className="p-4 bg-[#080808] border border-white/10 hover:border-white/25 transition-all flex flex-col md:flex-row md:items-start justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`text-[9px] px-2 py-0.5 border font-bold ${actionBadgeClass}`}>
                          {evt.action}
                        </span>
                        <span className="text-zinc-500 text-[10px]">
                          TARGET: <strong className="text-zinc-300 font-mono">{evt.entity_type} #{evt.entity_id?.slice(0, 8)}</strong>
                        </span>
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-[10px] text-zinc-400 font-sans pt-1">
                        <span>ACTOR: <strong className="text-white font-mono">{evt.actor_label || 'system'}</strong> ({evt.actor_role || 'SYSTEM'})</span>
                        <span>•</span>
                        <span>EVENT ID: <code className="text-zinc-500">#{evt.id?.slice(0, 8)}</code></span>
                      </div>

                      {/* Cryptographic Hashes */}
                      <div className="pt-2 text-[10px] text-zinc-500 space-y-0.5 border-t border-white/5 mt-2">
                        <div className="flex items-center gap-1.5 truncate">
                          <Hash className="w-3 h-3 text-zinc-500 flex-shrink-0" />
                          <span className="text-zinc-400">HASH:</span>
                          <span className="font-mono text-zinc-300 truncate max-w-sm sm:max-w-md">
                            {evt.integrity_hash || 'Legacy (Pre-chain)'}
                          </span>
                        </div>
                        {evt.prev_hash && (
                          <div className="flex items-center gap-1.5 truncate text-[9px] text-zinc-500">
                            <span className="text-zinc-500 pl-4">PREV HASH:</span>
                            <span className="font-mono text-zinc-400 truncate max-w-sm sm:max-w-md">
                              {evt.prev_hash}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-right md:flex-shrink-0 text-[10px] text-zinc-500">
                      <div className="flex items-center gap-1 md:justify-end text-zinc-300 font-medium">
                        <Clock className="w-3 h-3" />
                        <span>{formatDate(evt.timestamp)}</span>
                      </div>
                      <div className="mt-0.5 text-zinc-500">
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'N/A'}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Governance & Architecture Notice */}
      <div className="p-4 bg-[#080808] border border-white/10 text-xs font-sans text-zinc-400 space-y-1">
        <div className="flex items-center gap-1.5 text-zinc-300 font-mono text-[11px] font-bold uppercase">
          <Info className="w-3.5 h-3.5 text-emerald-400" />
          <span>Ledger Immutability Architecture Notice</span>
        </div>
        <p className="text-[11px] leading-relaxed">
          Application-level append-only controls prevent non-admin actors from modifying or deleting logged events. SHA-256 cryptographic chaining detects any sequence reordering or payload manipulation during runtime verification.
        </p>
      </div>
    </div>
  );
}

export default AuditPage;
