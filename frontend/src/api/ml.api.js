import apiClient from '../lib/api-client';

export const mlApi = {
  getHealth: async () => {
    const { data } = await apiClient.get('/api/v1/ml/health');
    return data;
  },

  preprocessText: async (text, language = 'en') => {
    const { data } = await apiClient.post('/api/v1/ml/preprocess/text', {
      text,
      language,
    });
    return data;
  },

  extractSkills: async (text, trade = 'electrician', language = 'en') => {
    const { data } = await apiClient.post('/api/v1/ml/skills/extract', {
      text,
      trade,
      language,
    });
    return data;
  },

  mapNOS: async (skills, top_k = 3) => {
    const { data } = await apiClient.post('/api/v1/ml/nos/map', {
      skills,
      top_k,
    });
    return data;
  },

  runFullPipeline: async (payload) => {
    const { data } = await apiClient.post(
      '/api/v1/ml/pipeline/worker-assessment',
      payload
    );
    return data;
  },
};

export default mlApi;
