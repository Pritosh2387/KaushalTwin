import apiClient from '../lib/api-client';

export const assessmentsApi = {
  getAssessments: async ({ skip = 0, limit = 20, status } = {}) => {
    const params = { skip, limit };
    if (status) params.status = status;
    const { data } = await apiClient.get('/api/v1/assessments', { params });
    return data;
  },

  getAssessment: async (assessmentId) => {
    const { data } = await apiClient.get(`/api/v1/assessments/${assessmentId}`);
    return data;
  },

  createAssessment: async (assessmentData) => {
    const { data } = await apiClient.post('/api/v1/assessments', assessmentData);
    return data;
  },

  updateAssessment: async (assessmentId, updateData) => {
    const { data } = await apiClient.patch(`/api/v1/assessments/${assessmentId}`, updateData);
    return data;
  },

  startAssessment: async (assessmentId) => {
    const { data } = await apiClient.post(`/api/v1/assessments/${assessmentId}/start`);
    return data;
  },

  completeAssessment: async (assessmentId) => {
    const { data } = await apiClient.post(`/api/v1/assessments/${assessmentId}/complete`);
    return data;
  },

  getAssessmentTasks: async (assessmentId) => {
    const { data } = await apiClient.get(`/api/v1/assessments/${assessmentId}/tasks`);
    return data;
  },

  createAssessmentTask: async (assessmentId, taskData) => {
    const { data } = await apiClient.post(`/api/v1/assessments/${assessmentId}/tasks`, taskData);
    return data;
  },

  submitTaskResult: async (assessmentId, taskId, resultData) => {
    const { data } = await apiClient.post(
      `/api/v1/assessments/${assessmentId}/tasks/${taskId}/result`,
      resultData
    );
    return data;
  },

  triggerAIAnalysis: async (assessmentId, params = {}) => {
    const { data } = await apiClient.post(
      `/api/v1/assessments/${assessmentId}/analyze`,
      params
    );
    return data;
  },

  getAIResults: async (assessmentId) => {
    const { data } = await apiClient.get(`/api/v1/assessments/${assessmentId}/ai-results`);
    return data;
  },

  recommendNextTask: async (assessmentId) => {
    const { data } = await apiClient.post(
      `/api/v1/assessments/${assessmentId}/recommend-next-task`
    );
    return data;
  },

  checkEvidenceSufficiency: async (assessmentId) => {
    const { data } = await apiClient.post(
      `/api/v1/assessments/${assessmentId}/check-evidence`
    );
    return data;
  },

  getLatestRecommendation: async (assessmentId) => {
    const { data } = await apiClient.get(`/api/v1/assessments/${assessmentId}/recommendation`);
    return data;
  },

  submitAssessorDecision: async (assessmentId, decisionData) => {
    const { data } = await apiClient.post(
      `/api/v1/assessments/${assessmentId}/decision`,
      decisionData
    );
    return data;
  },

  getAssessmentReport: async (assessmentId) => {
    const { data } = await apiClient.get(`/api/v1/assessments/${assessmentId}/report`);
    return data;
  },

  // Aliases for compatibility
  getAll: async (params) => assessmentsApi.getAssessments(params),
  getById: async (id) => assessmentsApi.getAssessment(id),
  create: async (data) => assessmentsApi.createAssessment(data),
  update: async (id, data) => assessmentsApi.updateAssessment(id, data),
  start: async (id) => assessmentsApi.startAssessment(id),
  complete: async (id) => assessmentsApi.completeAssessment(id),
  getTasks: async (id) => assessmentsApi.getAssessmentTasks(id),
  analyze: async (id, params) => assessmentsApi.triggerAIAnalysis(id, params),
  checkEvidence: async (id) => assessmentsApi.checkEvidenceSufficiency(id),
  recordDecision: async (id, data) => assessmentsApi.submitAssessorDecision(id, data),
  getReport: async (id) => assessmentsApi.getAssessmentReport(id),
};

export default assessmentsApi;
