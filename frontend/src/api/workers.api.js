import apiClient from '../lib/api-client';

export const workersApi = {
  getWorkers: async ({ skip = 0, limit = 20, trade } = {}) => {
    const params = { skip, limit };
    if (trade) params.trade = trade;
    const { data } = await apiClient.get('/api/v1/workers', { params });
    return data;
  },

  getWorker: async (workerId) => {
    const { data } = await apiClient.get(`/api/v1/workers/${workerId}`);
    return data;
  },

  createWorker: async (workerData) => {
    const { data } = await apiClient.post('/api/v1/workers', workerData);
    return data;
  },

  updateWorker: async (workerId, updateData) => {
    const { data } = await apiClient.patch(`/api/v1/workers/${workerId}`, updateData);
    return data;
  },

  getWorkerAssessments: async (workerId) => {
    const { data } = await apiClient.get(`/api/v1/workers/${workerId}/assessments`);
    return data;
  },

  getWorkerEvidence: async (workerId) => {
    const { data } = await apiClient.get(`/api/v1/workers/${workerId}/evidence`);
    return data;
  },

  getWorkerCompetencyProfile: async (workerId) => {
    const { data } = await apiClient.get(`/api/v1/workers/${workerId}/competency-profile`);
    return data;
  },

  getMyProfile: async () => {
    const { data } = await apiClient.get('/api/v1/workers/me');
    return data;
  },

  // Aliases for compatibility
  getAll: async (params) => workersApi.getWorkers(params),
  getById: async (id) => workersApi.getWorker(id),
  create: async (data) => workersApi.createWorker(data),
  update: async (id, data) => workersApi.updateWorker(id, data),
  getAssessments: async (id) => workersApi.getWorkerAssessments(id),
  getEvidence: async (id) => workersApi.getWorkerEvidence(id),
  getCompetencyProfile: async (id) => workersApi.getWorkerCompetencyProfile(id),
  getMe: async () => workersApi.getMyProfile(),
};

export default workersApi;