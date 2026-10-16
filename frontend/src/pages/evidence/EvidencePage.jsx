import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../context/AuthContext';
import {
  FileCheck2,
  UploadCloud,
  CheckCircle2,
  XCircle,
  Eye,
  Search,
  FileText,
  Image as ImageIcon,
  Award,
  ShieldCheck,
  ChevronRight,
  Download,
  Clock,
  HelpCircle
} from 'lucide-react';
import { evidenceApi } from '../../api/evidence.api';
import { workersApi } from '../../api/workers.api';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { SkeletonTableRows } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { EmptyState } from '../../components/ui/EmptyState';
import { formatDate } from '../../lib/date';

export function EvidencePage() {
  const queryClient = useQueryClient();
  const { user, isWorker } = useAuth();

  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [reviewModal, setReviewModal] = useState({ isOpen: false, item: null });
  const [reviewAction, setReviewAction] = useState('VERIFIED');
  const [reviewNotes, setReviewNotes] = useState('');
  const [fileToUpload, setFileToUpload] = useState(null);
  const [notification, setNotification] = useState(null);

  // For worker: fetch current worker profile to get worker id
  const { data: myWorkerProfile } = useQuery({
    queryKey: ['worker-profile-me'],
    queryFn: async () => {
      try {
        return await workersApi.getMyProfile();
      } catch {
        if (user?.id) return await workersApi.getById(user.id);
        return null;
      }
    },
    enabled: isWorker && !!user?.id,
  });

  const workerEffectiveId = isWorker ? (myWorkerProfile?.id || user?.id) : '';

  const [uploadData, setUploadData] = useState({
    worker_id: '',
    evidence_type: 'WORK_SAMPLE',
    description: '',
    nos_id: '',
  });

  // Queries
  const { data: evidenceData, isLoading } = useQuery({
    queryKey: ['evidence', { status: statusFilter || undefined, workerEffectiveId, isWorker }],
    queryFn: async () => {
      if (isWorker) {
        if (workerEffectiveId) {
          try {
            return await workersApi.getWorkerEvidence(workerEffectiveId);
          } catch {
            return await evidenceApi.getAll({ limit: 100 });
          }
        }
        return await evidenceApi.getAll({ limit: 100 });
      } else {
        return await evidenceApi.getAll({ limit: 100, verification_status: statusFilter || undefined });
      }
    },
    enabled: !isWorker || !!workerEffectiveId,
  });

  // Only fetch candidate workers list for assessors/admins
  const { data: workersData } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
    enabled: !isWorker,
  });

  const evidenceList = Array.isArray(evidenceData) ? evidenceData : (evidenceData?.items || []);
  const workers = workersData?.items || [];

  const filtered = evidenceList.filter((e) => {
    const q = search.toLowerCase();
    return (
      e.description?.toLowerCase().includes(q) ||
      e.evidence_type?.toLowerCase().includes(q) ||
      e.nos_id?.toLowerCase().includes(q) ||
      e.worker_id?.toLowerCase().includes(q)
    );
  });

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: async () => {
      const targetWorkerId = isWorker ? workerEffectiveId : uploadData.worker_id;
      if (!targetWorkerId) {
        throw new Error('Please select or specify a candidate worker.');
      }
      if (!uploadData.description.trim()) {
        throw new Error('Please enter a description for the evidence.');
      }

      if (fileToUpload) {
        const formData = new FormData();
        formData.append('file', fileToUpload);
        formData.append('evidence_type', uploadData.evidence_type);
        formData.append('source_type', 'UPLOAD');
        formData.append('description', uploadData.description);
        if (uploadData.nos_id) formData.append('nos_id', uploadData.nos_id);
        return await evidenceApi.uploadFile(targetWorkerId, formData);
      } else {
        return await evidenceApi.submit({
          worker_id: targetWorkerId,
          evidence_type: uploadData.evidence_type,
          source_type: 'DIRECT_ENTRY',
          description: uploadData.description,
          nos_id: uploadData.nos_id || undefined,
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
      queryClient.invalidateQueries({ queryKey: ['worker-evidence'] });
      setIsUploadOpen(false);
      setFileToUpload(null);
      setUploadData({ worker_id: '', evidence_type: 'WORK_SAMPLE', description: '', nos_id: '' });
      setNotification({ type: 'success', message: 'Evidence successfully registered and submitted for review.' });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.message || 'Failed to submit evidence.',
      });
    },
  });

  // Verify Mutation (Assessor Only)
  const verifyMutation = useMutation({
    mutationFn: ({ id, payload }) => evidenceApi.verify(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
      queryClient.invalidateQueries({ queryKey: ['worker-evidence'] });
      setReviewModal({ isOpen: false, item: null });
      setNotification({ type: 'success', message: 'Evidence verification status updated.' });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.message || 'Failed to update verification status.',
      });
    },
  });

  const getEvidenceIcon = (type) => {
    switch (type) {
      case 'CERTIFICATE':
        return Award;
      case 'PHOTOGRAPH':
      case 'VIDEO':
        return ImageIcon;
      default:
        return FileText;
    }
  };

  return (
    <div className="space-y-6 select-none font-mono">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
              <span>{isWorker ? 'My Supporting Evidence Portfolio' : 'Evidence Integrity & Verification'}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight uppercase">
              {isWorker ? 'My Evidence' : 'Evidence Review Queue'}
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light font-sans">
              {isWorker
                ? `Upload and track your work samples, photographs, certificates, and employer references (${evidenceList.length} total items).`
                : `Multi-modal artifacts, candidate logbooks, and work sample verification (${evidenceData?.total ?? evidenceList.length} items).`}
            </p>
          </div>

          <Button
            variant="primary"
            onClick={() => {
              setUploadData({
                worker_id: isWorker ? workerEffectiveId : '',
                evidence_type: 'WORK_SAMPLE',
                description: '',
                nos_id: '',
              });
              setFileToUpload(null);
              setIsUploadOpen(true);
            }}
            className="font-mono text-xs"
          >
            <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
            <span>{isWorker ? 'Submit Evidence' : 'Register Evidence'}</span>
          </Button>
        </div>
      </div>

      {notification && (
        <Alert variant={notification.type} onClose={() => setNotification(null)}>
          {notification.message}
        </Alert>
      )}

      {/* Worker Evidence Guidance Banner (Worker Only) */}
      {isWorker && (
        <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-sans">
          <div className="flex items-center gap-3">
            <HelpCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <div className="text-zinc-300">
              <span className="text-white font-mono uppercase font-semibold">What can you submit? </span>
              Photos of physical work, toolkits, workshop setup, previous course certificates, or employer reference letters.
            </div>
          </div>
          <span className="text-[10px] font-mono text-zinc-500 uppercase flex-shrink-0">
            Reviewed by certified assessor
          </span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-zinc-500" />
          <input
            type="text"
            placeholder="Search descriptions, artifact types, or standard codes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs font-mono bg-[#080808] border border-white/15 text-white placeholder-zinc-500 focus:border-white focus:outline-none transition-colors"
          />
        </div>

        <div className="w-full sm:w-64">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full py-2 px-3 text-xs font-mono bg-[#080808] border border-white/15 text-white focus:border-white focus:outline-none"
          >
            <option value="">All Verification Statuses</option>
            <option value="PENDING">Pending Review</option>
            <option value="UNVERIFIED">Unverified</option>
            <option value="VERIFIED">Verified</option>
            <option value="REJECTED">Rejected</option>
            <option value="NEEDS_INFO">Needs Additional Information</option>
          </select>
        </div>
      </div>

      {/* Evidence Table */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#080808] border-b border-white/15 text-zinc-400 text-[10px] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5 font-semibold">Artifact / Description</th>
                <th className="px-6 py-3.5 font-semibold">Category &amp; Standard</th>
                {!isWorker && <th className="px-6 py-3.5 font-semibold">Candidate</th>}
                <th className="px-6 py-3.5 font-semibold">Status</th>
                <th className="px-6 py-3.5 font-semibold">Submitted</th>
                {isWorker ? (
                  <th className="px-6 py-3.5 text-right font-semibold">Assessor Feedback</th>
                ) : (
                  <th className="px-6 py-3.5 text-right font-semibold">Assessor Audit</th>
                )}
              </tr>
            </thead>
            {isLoading ? (
              <SkeletonTableRows rows={4} cols={isWorker ? 5 : 6} />
            ) : filtered.length === 0 ? (
              <tbody>
                <tr>
                  <td colSpan={isWorker ? 5 : 6} className="p-8">
                    <EmptyState
                      icon={FileCheck2}
                      title={isWorker ? "No evidence submitted yet" : "No evidence records found"}
                      description={
                        isWorker
                          ? "You haven't submitted any supporting work samples yet. Upload photos, references, or certificates to prove your skills."
                          : "No candidate evidence records match your current filter."
                      }
                      actionLabel={isWorker ? "Submit Your First Evidence" : "Register Evidence"}
                      onAction={() => {
                        setUploadData({
                          worker_id: isWorker ? workerEffectiveId : '',
                          evidence_type: 'WORK_SAMPLE',
                          description: '',
                          nos_id: '',
                        });
                        setFileToUpload(null);
                        setIsUploadOpen(true);
                      }}
                    />
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody className="divide-y divide-white/5">
                {filtered.map((item) => {
                  const Icon = getEvidenceIcon(item.evidence_type);
                  const isVerified = item.verification_status === 'VERIFIED';
                  const isRejected = item.verification_status === 'REJECTED';
                  const isPending = !isVerified && !isRejected;

                  return (
                    <tr key={item.id} className="hover:bg-white/[0.03] transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 border border-white/15 bg-[#080808] text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Icon className="w-3.5 h-3.5 text-zinc-300" />
                          </div>
                          <div>
                            <div className="font-bold text-white leading-snug">
                              {item.description}
                            </div>
                            <div className="text-[10px] text-zinc-500 mt-0.5">
                              {item.file_name ? (
                                <a
                                  href={evidenceApi.getDownloadUrl(item.id)}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-zinc-400 hover:text-white underline inline-flex items-center gap-1"
                                >
                                  <Download className="w-2.5 h-2.5" />
                                  <span>{item.file_name}</span>
                                </a>
                              ) : (
                                <span>Direct text submission</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-zinc-300 font-bold">{item.evidence_type}</div>
                        <div className="text-[10px] text-zinc-500">
                          {item.nos_id ? `NOS: ${item.nos_id}` : 'General Trade Standard'}
                        </div>
                      </td>

                      {!isWorker && (
                        <td className="px-6 py-4">
                          <div className="text-white font-medium">
                            {workers.find((w) => w.id === item.worker_id)?.full_name || 'Candidate'}
                          </div>
                          <div className="text-[10px] text-zinc-500 font-mono">
                            #{item.worker_id ? String(item.worker_id).slice(0, 8) : 'N/A'}
                          </div>
                        </td>
                      )}

                      <td className="px-6 py-4">
                        <StatusBadge status={item.verification_status || 'PENDING'} size="sm" />
                      </td>

                      <td className="px-6 py-4 text-zinc-400 text-[10px]">
                        {formatDate(item.created_at)}
                      </td>

                      <td className="px-6 py-4 text-right">
                        {isWorker ? (
                          <div className="text-left md:text-right">
                            {item.verification_notes ? (
                              <span className="text-xs text-zinc-300 font-sans italic" title={item.verification_notes}>
                                "{item.verification_notes.length > 30 ? item.verification_notes.slice(0, 30) + '...' : item.verification_notes}"
                              </span>
                            ) : isVerified ? (
                              <span className="text-[10px] text-emerald-400 font-mono">Verified by Assessor</span>
                            ) : (
                              <span className="text-[10px] text-zinc-500 font-mono">Awaiting Review</span>
                            )}
                          </div>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setReviewModal({ isOpen: true, item });
                              setReviewAction(item.verification_status || 'VERIFIED');
                              setReviewNotes(item.verification_notes || '');
                            }}
                            className="font-mono text-[10px]"
                          >
                            AUDIT ↗
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            )}
          </table>
        </div>
      </div>

      {/* Upload Modal */}
      <Modal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        title={isWorker ? "SUBMIT SUPPORTING EVIDENCE" : "REGISTER CANDIDATE EVIDENCE"}
        description={
          isWorker
            ? "Upload proof of your hands-on skill, on-site photographs, reference letters, or workshop certificates."
            : "Upload photographs, workshop videos, trade logbooks, or employer testimonials on behalf of a candidate."
        }
        maxWidth="max-w-lg"
      >
        <div className="space-y-4">
          {!isWorker && (
            <Select
              label="Candidate Worker"
              required
              value={uploadData.worker_id}
              onChange={(e) => setUploadData({ ...uploadData, worker_id: e.target.value })}
              options={[
                { value: '', label: 'Select candidate...' },
                ...workers.map((w) => ({
                  value: w.id,
                  label: `${w.full_name || 'Worker'} (${w.trade || 'General'})`,
                })),
              ]}
            />
          )}

          <Select
            label="Evidence Category"
            value={uploadData.evidence_type}
            onChange={(e) => setUploadData({ ...uploadData, evidence_type: e.target.value })}
            options={[
              { value: 'WORK_SAMPLE', label: 'Work Sample (Photograph / Finished Item)' },
              { value: 'PHOTOGRAPH', label: 'On-Site Photograph' },
              { value: 'VIDEO', label: 'Practical Performance Demonstration' },
              { value: 'CERTIFICATE', label: 'Prior Certificate / Trade Logbook' },
              { value: 'EXPERIENCE_DECLARATION', label: 'Employer / Supervisor Reference Letter' },
            ]}
          />

          <Input
            label="Target NOS Standard Code (Optional)"
            placeholder="e.g. ELE/N5801 or CSC/N0204"
            value={uploadData.nos_id}
            onChange={(e) => setUploadData({ ...uploadData, nos_id: e.target.value })}
          />

          <Input
            label="Description & Context"
            required
            placeholder="e.g. Residential distribution board wiring with proper earth connection"
            value={uploadData.description}
            onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
          />

          <div>
            <label className="block text-[11px] font-mono text-zinc-300 uppercase tracking-widest mb-1.5">
              ATTACH FILE (OPTIONAL)
            </label>
            <input
              type="file"
              onChange={(e) => setFileToUpload(e.target.files[0])}
              className="w-full text-xs font-mono text-zinc-400 file:mr-3 file:py-1.5 file:px-3 file:border file:border-white/20 file:bg-[#0a0a0a] file:text-white file:text-xs file:font-mono file:cursor-pointer"
            />
            <p className="text-[10px] text-zinc-500 font-sans mt-1">
              Supported formats: JPEG, PNG, PDF, MP4 up to 50MB.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsUploadOpen(false)}
              className="font-mono text-xs"
            >
              CANCEL
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => uploadMutation.mutate()}
              loading={uploadMutation.isPending}
              className="font-mono text-xs"
            >
              SUBMIT EVIDENCE ↗
            </Button>
          </div>
        </div>
      </Modal>

      {/* Review Modal (Assessors Only) */}
      {!isWorker && (
        <Modal
          isOpen={reviewModal.isOpen}
          onClose={() => setReviewModal({ isOpen: false, item: null })}
          title="ASSESSOR EVIDENCE AUDIT"
          description={`Audit candidate item #${reviewModal.item?.id?.slice(0, 8)} against National Occupational Standards.`}
          maxWidth="max-w-lg"
        >
          <div className="space-y-4 font-mono text-xs">
            <div className="p-3 bg-[#080808] border border-white/10 space-y-1">
              <div className="text-zinc-400 text-[10px]">DESCRIPTION:</div>
              <div className="text-white font-bold">{reviewModal.item?.description}</div>
              <div className="text-zinc-500 text-[10px] pt-1">
                TYPE: {reviewModal.item?.evidence_type} • NOS: {reviewModal.item?.nos_id || 'UNMAPPED'}
              </div>
            </div>

            <Select
              label="Assessor Verdict"
              value={reviewAction}
              onChange={(e) => setReviewAction(e.target.value)}
              options={[
                { value: 'VERIFIED', label: 'VERIFIED — Authentic and NOS-Compliant' },
                { value: 'REJECTED', label: 'REJECTED — Insufficient or Inconclusive' },
                { value: 'NEEDS_INFO', label: 'NEEDS INFO — Request Secondary Demonstration' },
              ]}
            />

            <Input
              label="Assessor Review Notes"
              placeholder="e.g. Visual inspection confirms compliance with standard."
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
            />

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setReviewModal({ isOpen: false, item: null })}
                className="font-mono text-xs"
              >
                CANCEL
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() =>
                  verifyMutation.mutate({
                    id: reviewModal.item.id,
                    payload: { verification_status: reviewAction, verification_notes: reviewNotes },
                  })
                }
                loading={verifyMutation.isPending}
                className="font-mono text-xs"
              >
                CONFIRM VERDICT ↗
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default EvidencePage;
