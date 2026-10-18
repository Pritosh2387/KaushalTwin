import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authApi from '../api/auth.api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('kaushaltwin_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('kaushaltwin_token'));
  const [isLoading, setIsLoading] = useState(true);

  // Sync / verify user session on mount
  useEffect(() => {
    async function verifySession() {
      const storedToken = localStorage.getItem('kaushaltwin_token');
      if (!storedToken) {
        setUser(null);
        setIsLoading(false);
        return;
      }

      try {
        const userData = await authApi.getMe();
        if (userData && !userData.full_name && userData.name) {
          userData.full_name = userData.name;
        }
        setUser(userData);
        localStorage.setItem('kaushaltwin_user', JSON.stringify(userData));
      } catch (err) {
        console.warn('Session verification failed:', err.message);
        localStorage.removeItem('kaushaltwin_token');
        localStorage.removeItem('kaushaltwin_user');
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    }

    verifySession();
  }, []);

  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    try {
      const data = await authApi.login({ email, password });
      const accessToken = data.access_token;
      localStorage.setItem('kaushaltwin_token', accessToken);
      setToken(accessToken);

      const userData = await authApi.getMe();
      if (userData && !userData.full_name && userData.name) {
        userData.full_name = userData.name;
      }
      setUser(userData);
      localStorage.setItem('kaushaltwin_user', JSON.stringify(userData));
      return { success: true, user: userData };
    } catch (error) {
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async ({ name, email, password, role }) => {
    setIsLoading(true);
    try {
      await authApi.register({ name, email, password, role });
      // Automatically log in after registration
      return await login(email, password);
    } catch (error) {
      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  }, [login]);

  const logout = useCallback((options = {}) => {
    localStorage.removeItem('kaushaltwin_token');
    localStorage.removeItem('kaushaltwin_user');
    setToken(null);
    setUser(null);
    if (options && options.redirect !== false) {
      const target = options.to || '/?login=true&signed_out=true';
      window.location.href = target;
    }
  }, []);

  const value = {
    user,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    isAssessor: user?.role === 'ASSESSOR',
    isAdmin: user?.role === 'ADMIN',
    isWorker: user?.role === 'WORKER',
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
