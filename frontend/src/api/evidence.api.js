import apiClient from '../lib/api-client';

export const evidenceApi = {
  getAll: async ({ skip = 0, limit = 50, verification_status, worker_id } = {}) => {
    const params = { skip, limit };
    if (verification_status) params.verification_status = verification_status;
    if (worker_id) params.worker_id = worker_id;
    const { data } = await apiClient.get('/api/v1/evidence', { params });
    return data;
  },

  submitMetadata: async (evidenceData) => {
    const { data } = await apiClient.post('/api/v1/evidence', evidenceData);
    return data;
  },

  uploadFile: async (workerId, formData) => {
    const { data } = await apiClient.post(
      `/api/v1/evidence/upload/${workerId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return data;
  },

  getEvidence: async (evidenceId) => {
    const { data } = await apiClient.get(`/api/v1/evidence/${evidenceId}`);
    return data;
  },

  updateMetadata: async (evidenceId, updateData) => {
    const { data } = await apiClient.patch(`/api/v1/evidence/${evidenceId}`, updateData);
    return data;
  },

  verifyEvidence: async (evidenceId, { verification_status, verification_notes, comments }) => {
    const { data } = await apiClient.post(`/api/v1/evidence/${evidenceId}/verify`, {
      verification_status,
      verification_notes: verification_notes || comments,
    });
    return data;
  },

  getDownloadUrl: (evidenceId) => {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${base}/api/v1/evidence/${evidenceId}/download`;
  },

  // Compatibility aliases
  submit: async (data) => evidenceApi.submitMetadata(data),
  verify: async (id, payload) => evidenceApi.verifyEvidence(id, payload),
  getById: async (id) => evidenceApi.getEvidence(id),
};

export default evidenceApi;
