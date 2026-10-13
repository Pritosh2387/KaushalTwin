import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  ChevronRight
} from 'lucide-react';
import { evidenceApi } from '../../api/evidence.api';
import { workersApi } from '../../api/workers.api';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { SkeletonTableRows } from '../../components/ui/Skeleton';
import { Alert } from '../../components/ui/Alert';
import { EmptyState } from '../../components/ui/EmptyState';

export function EvidencePage() {
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [reviewModal, setReviewModal] = useState({ isOpen: false, item: null });
  const [reviewAction, setReviewAction] = useState('VERIFIED');
  const [reviewNotes, setReviewNotes] = useState('');
  const [uploadData, setUploadData] = useState({
    worker_id: '',
    evidence_type: 'WORK_SAMPLE',
    description: '',
    nos_id: '',
  });
  const [fileToUpload, setFileToUpload] = useState(null);
  const [notification, setNotification] = useState(null);

  // Queries
  const { data: evidenceData, isLoading } = useQuery({
    queryKey: ['evidence', { status: statusFilter || undefined }],
    queryFn: () => evidenceApi.getAll({ limit: 100, verification_status: statusFilter || undefined }),
  });

  const { data: workersData } = useQuery({
    queryKey: ['workers', { limit: 100 }],
    queryFn: () => workersApi.getAll({ limit: 100 }),
  });

  const evidenceList = evidenceData?.items || [];
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
      if (fileToUpload) {
        const formData = new FormData();
        formData.append('file', fileToUpload);
        formData.append('evidence_type', uploadData.evidence_type);
        formData.append('source_type', 'UPLOAD');
        formData.append('description', uploadData.description);
        if (uploadData.nos_id) formData.append('nos_id', uploadData.nos_id);
        return evidenceApi.uploadFile(uploadData.worker_id, formData);
      } else {
        return evidenceApi.submit({
          worker_id: uploadData.worker_id,
          evidence_type: uploadData.evidence_type,
          source_type: 'DIRECT_ENTRY',
          description: uploadData.description,
          nos_id: uploadData.nos_id || undefined,
        });
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
      setIsUploadOpen(false);
      setFileToUpload(null);
      setUploadData({ worker_id: '', evidence_type: 'WORK_SAMPLE', description: '', nos_id: '' });
      setNotification({ type: 'success', message: 'Evidence successfully registered in the system.' });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.response?.data?.detail || 'Failed to submit evidence.',
      });
    },
  });

  // Verify Mutation
  const verifyMutation = useMutation({
    mutationFn: ({ id, payload }) => evidenceApi.verify(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
      setReviewModal({ isOpen: false, item: null });
      setNotification({ type: 'success', message: 'Evidence verification status updated.' });
    },
    onError: (err) => {
      setNotification({
        type: 'error',
        message: err?.response?.data?.detail || 'Failed to update verification status.',
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
    <div className="space-y-6 select-none">
      {/* Editorial Page Header */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-white" />
              <span>Evidence Integrity &amp; Verification</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight uppercase">
              Candidate Evidence
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 font-light">
              Multi-modal artifacts, candidate logbooks, and work sample verification ({evidenceData?.total ?? evidenceList.length} items)
            </p>
          </div>

          <Button
            variant="primary"
            onClick={() => setIsUploadOpen(true)}
            className="font-mono"
          >
            <UploadCloud className="w-3.5 h-3.5 mr-1.5" />
            <span>Upload Evidence</span>
          </Button>
        </div>
      </div>

      {notification && (
        <Alert variant={notification.type} onClose={() => setNotification(null)}>
          {notification.message}
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-[#050505] border border-white/10 p-4 specular-top-edge flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-zinc-500" />
          <input
            type="text"
            placeholder="Search evidence descriptions, artifact types, or standard codes..."
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
            <option value="VERIFIED">Verified</option>
            <option value="REJECTED">Rejected</option>
            <option value="NEEDS_INFO">Needs Additional Information</option>
          </select>
        </div>
      </div>

      {/* Monochromatic Evidence Table */}
      <div className="bg-[#050505] border border-white/10 specular-top-edge">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-[#080808] border-b border-white/15 text-zinc-400 text-[10px] uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5 font-semibold">Artifact / Description</th>
                <th className="px-6 py-3.5 font-semibold">Evidence Type &amp; Standard</th>
                <th className="px-6 py-3.5 font-semibold">Candidate</th>
                <th className="px-6 py-3.5 font-semibold">Status</th>
                <th className="px-6 py-3.5 text-right font-semibold">Assessor Audit</th>
              </tr>
            </thead>
            {isLoading ? (
              <SkeletonTableRows rows={5} cols={5} />
            ) : filtered.length === 0 ? (
              <tbody>
                <tr>
                  <td colSpan={5} className="p-8">
                    <EmptyState
                      icon={FileCheck2}
                      title="No evidence items found"
                      description="No candidate evidence records match your criteria. Upload work samples or certificates to begin."
                      actionLabel="Submit Evidence"
                      onAction={() => setIsUploadOpen(true)}
                    />
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody className="divide-y divide-white/5">
                {filtered.map((item) => {
                  const Icon = getEvidenceIcon(item.evidence_type);
                  return (
                    <tr key={item.id} className="hover:bg-white/[0.03] transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 border border-white/15 bg-[#080808] text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <div className="font-bold text-white leading-snug">
                              {item.description || 'Candidate Work Artifact'}
                            </div>
                            <div className="text-[10px] text-zinc-500 mt-0.5">
                              ID: #{item.id.slice(0, 8)} • SUBMITTED: {new Date(item.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-zinc-300 font-semibold">{item.evidence_type}</div>
                        <div className="text-[10px] text-zinc-500 font-mono">
                          NOS: {item.nos_id || 'UNMAPPED'}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-zinc-300">ID: {item.worker_id.slice(0, 8)}...</div>
                      </td>

                      <td className="px-6 py-4">
                        <StatusBadge status={item.verification_status} size="sm" />
                      </td>

                      <td className="px-6 py-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setReviewModal({ isOpen: true, item })}
                          className="font-mono text-[10px]"
                        >
                          AUDIT ↗
                        </Button>
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
        title="REGISTER CANDIDATE EVIDENCE"
        description="Upload photographs, workshop videos, trade logbooks, or employer testimonials."
        maxWidth="max-w-lg"
      >
        <div className="space-y-4">
          <Select
            label="Candidate Worker"
            required
            value={uploadData.worker_id}
            onChange={(e) => setUploadData({ ...uploadData, worker_id: e.target.value })}
            options={workers.map((w) => ({
              value: w.id,
              label: `${w.full_name || 'Worker'} (${w.trade || 'General'})`,
            }))}
          />

          <Select
            label="Evidence Category"
            value={uploadData.evidence_type}
            onChange={(e) => setUploadData({ ...uploadData, evidence_type: e.target.value })}
            options={[
              { value: 'WORK_SAMPLE', label: 'Physical Work Sample' },
              { value: 'PHOTOGRAPH', label: 'Workshop Photograph' },
              { value: 'VIDEO', label: 'Practical Performance Video' },
              { value: 'CERTIFICATE', label: 'Prior Certificate / Logbook' },
              { value: 'TESTIMONIAL', label: 'Employer / Supervisor Testimonial' },
            ]}
          />

          <Input
            label="Target NOS Standard (Optional)"
            placeholder="e.g. CSC/N0204"
            value={uploadData.nos_id}
            onChange={(e) => setUploadData({ ...uploadData, nos_id: e.target.value })}
          />

          <Input
            label="Artifact Description"
            required
            placeholder="e.g. Butt weld tee-joint specimen in 6G position"
            value={uploadData.description}
            onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
          />

          <div>
            <label className="block text-[11px] font-mono text-zinc-300 uppercase tracking-widest mb-1.5">
              ATTACH FILE ARTIFACT
            </label>
            <input
              type="file"
              onChange={(e) => setFileToUpload(e.target.files[0])}
              className="w-full text-xs font-mono text-zinc-400 file:mr-3 file:py-1.5 file:px-3 file:border file:border-white/20 file:bg-[#0a0a0a] file:text-white file:text-xs file:font-mono file:cursor-pointer"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button
              variant="outline"
              onClick={() => setIsUploadOpen(false)}
              className="font-mono text-xs"
            >
              CANCEL
            </Button>
            <Button
              variant="primary"
              onClick={() => uploadMutation.mutate()}
              loading={uploadMutation.isPending}
              className="font-mono text-xs"
            >
              SUBMIT EVIDENCE ↗
            </Button>
          </div>
        </div>
      </Modal>

      {/* Review Modal */}
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
            placeholder="e.g. Visual weld bead verified against CSC/N0204 inspection criteria."
            value={reviewNotes}
            onChange={(e) => setReviewNotes(e.target.value)}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button
              variant="outline"
              onClick={() => setReviewModal({ isOpen: false, item: null })}
              className="font-mono text-xs"
            >
              CANCEL
            </Button>
            <Button
              variant="primary"
              onClick={() =>
                verifyMutation.mutate({
                  id: reviewModal.item.id,
                  payload: { verification_status: reviewAction, assessor_notes: reviewNotes },
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
    </div>
  );
}

export default EvidencePage;
