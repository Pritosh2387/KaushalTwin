import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileCheck2,
  UploadCloud,
  CheckCircle2,
  XCircle,
  Eye,
  Filter,
  Plus,
  Search,
  FileText,
  Image as ImageIcon,
  Award,
  AlertCircle,
  Clock,
  Sparkles
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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span>Evidence Portfolio</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
              {evidenceData?.total ?? evidenceList.length} Items
            </span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Artifacts, work samples, and prior learning documentation submitted by candidates
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => setIsUploadOpen(true)}
          className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold shadow-md shadow-cyan-500/20"
        >
          <UploadCloud className="w-4 h-4 mr-1.5" />
          <span>Upload Evidence</span>
        </Button>
      </div>

      {notification && (
        <Alert variant={notification.type} onClose={() => setNotification(null)}>
          {notification.message}
        </Alert>
      )}

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search evidence descriptions, types, or NOS codes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            />
          </div>

          <div className="w-full sm:w-60">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full py-2 px-3 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            >
              <option value="">All Verification Statuses</option>
              <option value="PENDING">Pending Verification</option>
              <option value="VERIFIED">Verified Valid</option>
              <option value="REJECTED">Rejected</option>
              <option value="NEEDS_INFO">Additional Info Required</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Evidence Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Artifact / Description</th>
                <th className="px-6 py-3.5">Type & Target NOS</th>
                <th className="px-6 py-3.5">Candidate Worker</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Assessor Action</th>
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
                      description="No candidate evidence records match your criteria. Upload work samples or certificates to get started."
                      actionLabel="Upload Evidence"
                      onAction={() => setIsUploadOpen(true)}
                    />
                  </td>
                </tr>
              </tbody>
            ) : (
              <tbody className="divide-y divide-slate-100">
                {filtered.map((item) => {
                  const Icon = getEvidenceIcon(item.evidence_type);
                  return (
                    <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-start gap-3">
                          <div className="w-9 h-9 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="font-bold text-slate-900 leading-snug">
                              {item.description || 'Evidence Submission'}
                            </div>
                            <div className="text-xs text-slate-400 mt-0.5">
                              ID: #{item.id.slice(0, 8)} • {new Date(item.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className="font-semibold text-slate-700 text-xs px-2 py-0.5 rounded bg-slate-100">
                          {item.evidence_type}
                        </span>
                        {item.nos_id && (
                          <div className="text-xs text-cyan-700 font-mono font-medium mt-1">
                            NOS: {item.nos_id}
                          </div>
                        )}
                      </td>

                      <td className="px-6 py-4 text-xs font-semibold text-slate-800">
                        Worker #{item.worker_id.slice(0, 8)}...
                      </td>

                      <td className="px-6 py-4">
                        <StatusBadge status={item.verification_status} size="sm" />
                      </td>

                      <td className="px-6 py-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setReviewModal({ isOpen: true, item })}
                          className="text-xs hover:border-cyan-500 hover:text-cyan-700"
                        >
                          <span>Review & Verify</span>
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            )}
          </table>
        </div>
      </Card>

      {/* Upload Evidence Modal */}
      <Modal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        title="Submit Evidence Artifact"
        description="Upload work samples, job certificates, photos, or supervisor verification letters."
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            uploadMutation.mutate();
          }}
          className="space-y-4"
        >
          <Select
            label="Select Candidate Worker *"
            required
            value={uploadData.worker_id}
            onChange={(e) => setUploadData({ ...uploadData, worker_id: e.target.value })}
            options={[
              { value: '', label: '-- Select Candidate --' },
              ...workers.map((w) => ({
                value: w.id,
                label: `${w.full_name} (${w.trade || 'General'})`,
              })),
            ]}
          />

          <Select
            label="Evidence Category *"
            value={uploadData.evidence_type}
            onChange={(e) => setUploadData({ ...uploadData, evidence_type: e.target.value })}
            options={[
              { value: 'WORK_SAMPLE', label: 'Work Sample / Finished Product' },
              { value: 'PHOTOGRAPH', label: 'Workplace Activity Photograph' },
              { value: 'CERTIFICATE', label: 'Prior Certificate or Course Record' },
              { value: 'EXPERIENCE_DECLARATION', label: 'Employer / Supervisor Experience Declaration' },
              { value: 'VIDEO', label: 'Demonstration Video' },
            ]}
          />

          <Input
            label="Description & Context *"
            required
            placeholder="e.g. Photograph of candidate welding pressure pipe joint with TIG apparatus."
            value={uploadData.description}
            onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
          />

          <Input
            label="Target NOS Standard Code (Optional)"
            placeholder="e.g. CSC/N0204"
            value={uploadData.nos_id}
            onChange={(e) => setUploadData({ ...uploadData, nos_id: e.target.value })}
            helperText="Link directly to a National Occupational Standard if known."
          />

          {/* File Picker */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Attach File Artifact (Optional)
            </label>
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-4 text-center hover:border-cyan-400 transition-colors bg-slate-50/50">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={(e) => setFileToUpload(e.target.files[0])}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center justify-center gap-1.5"
              >
                <UploadCloud className="w-6 h-6 text-slate-400" />
                <span className="text-xs font-semibold text-cyan-600">
                  {fileToUpload ? fileToUpload.name : 'Click to browse or drop file here'}
                </span>
                <span className="text-[11px] text-slate-400">
                  Supports PDF, JPG, PNG, MP4 up to 50MB
                </span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsUploadOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={uploadMutation.isPending}
            >
              Upload Artifact
            </Button>
          </div>
        </form>
      </Modal>

      {/* Review & Verify Modal */}
      <Modal
        isOpen={reviewModal.isOpen}
        onClose={() => setReviewModal({ isOpen: false, item: null })}
        title="Verify Candidate Evidence"
        description={`Item: ${reviewModal.item?.description || 'Artifact'}`}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            verifyMutation.mutate({
              id: reviewModal.item?.id,
              payload: {
                verification_status: reviewAction,
                comments: reviewNotes,
              },
            });
          }}
          className="space-y-4"
        >
          <Select
            label="Verification Verdict *"
            value={reviewAction}
            onChange={(e) => setReviewAction(e.target.value)}
            options={[
              { value: 'VERIFIED', label: 'Verified as Authentic & Valid' },
              { value: 'REJECTED', label: 'Rejected (Inauthentic / Ineligible)' },
              { value: 'NEEDS_INFO', label: 'Needs Additional Documentation' },
            ]}
          />

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Assessor Verification Notes *
            </label>
            <textarea
              required
              rows={3}
              placeholder="State basis of verification (e.g. confirmed with employer stamp or observed standard compliance)..."
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              className="w-full p-3 text-sm bg-slate-50 rounded-xl border border-slate-200 focus:bg-white focus:border-cyan-500 outline-none transition-all"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <Button
              type="button"
              variant="outline"
              onClick={() => setReviewModal({ isOpen: false, item: null })}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={verifyMutation.isPending}
            >
              Commit Verification
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
