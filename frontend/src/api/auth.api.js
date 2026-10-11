import apiClient from '../lib/api-client';

export const authApi = {
  login: async ({ email, password }) => {
    const { data } = await apiClient.post('/api/v1/auth/login', {
      email,
      password,
    });
    return data;
  },

  register: async ({ name, email, password, role }) => {
    const { data } = await apiClient.post('/api/v1/auth/register', {
      name,
      email,
      password,
      role,
    });
    return data;
  },

  getMe: async () => {
    const { data } = await apiClient.get('/api/v1/auth/me');
    return data;
  },
};

export default authApi;
