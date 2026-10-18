import axios from 'axios';

// Read backend base URL from Vite environment, falling back to local backend port 8000
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Sanitize URL: strip trailing slashes and remove accidental duplicate /api/v1 suffix
const cleanBaseUrl = rawBaseUrl.replace(/\/+$/, '').replace(/\/api\/v1$/, '');

export const apiClient = axios.create({
  baseURL: cleanBaseUrl,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  timeout: 30000,
});

// Request interceptor: attach bearer token if present in localStorage
apiClient.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('kaushaltwin_token');
      if (token && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // Ignore localStorage access restrictions if running in SSR/sandboxed environment
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401, normalize error details, prevent redirect loops
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;

      // Handle 401 Unauthorized — clear token and redirect safely
      if (status === 401) {
        try {
          localStorage.removeItem('kaushaltwin_token');
          localStorage.removeItem('kaushaltwin_user');
        } catch {
          // Ignore storage errors
        }

        // Avoid redirect loops: do not redirect if already on login query
        if (typeof window !== 'undefined' && !window.location.search.includes('login=true')) {
          window.location.href = '/?login=true&session_expired=true';
        }
      }

      // Extract user-friendly error message from FastAPI or custom backend responses
      if (data) {
        if (typeof data.detail === 'string') {
          error.message = data.detail;
        } else if (Array.isArray(data.detail)) {
          // FastAPI pydantic validation errors
          error.message = data.detail.map((err) => err.msg || JSON.stringify(err)).join(', ');
        } else if (typeof data.message === 'string') {
          error.message = data.message;
        } else if (data.error && typeof data.error.message === 'string') {
          error.message = data.error.message;
        }
      }
    } else if (error.request) {
      // Network error or server unreachable
      error.message = 'Unable to connect to Kaushaltwin backend server. Please verify the server is running.';
    }

    return Promise.reject(error);
  }
);

export default apiClient;