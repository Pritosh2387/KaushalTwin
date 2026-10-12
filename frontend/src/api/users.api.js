/**
 * KaushalTwin — Users API
 * Note: The backend doesn't expose a dedicated user-listing endpoint in v1.
 * This module provides safe stubs for future admin use.
 */

import apiClient from '../lib/api-client';

export const usersApi = {
  /**
   * Fetch all registered users (admin only).
   * Note: This endpoint may not exist yet in the backend — will return 404 gracefully.
   */
  getAll: async ({ skip = 0, limit = 50, role } = {}) => {
    const params = { skip, limit };
    if (role) params.role = role;
    const { data } = await apiClient.get('/api/v1/users', { params });
    return data;
  },

  /**
   * Get a user by ID.
   */
  getById: async (userId) => {
    const { data } = await apiClient.get(`/api/v1/users/${userId}`);
    return data;
  },

  /**
   * Get the currently authenticated user's profile.
   * Delegates to the auth endpoint which is always available.
   */
  getMe: async () => {
    const { data } = await apiClient.get('/api/v1/auth/me');
    return data;
  },
};

export default usersApi;
