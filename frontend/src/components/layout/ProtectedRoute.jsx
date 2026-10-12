import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Skeleton } from '../ui/Skeleton';

export function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, isLoading: loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-navy-950 flex items-center justify-center shadow-lg border border-cyan-500/30">
          <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className="text-sm font-medium text-slate-500 animate-pulse">
          Authenticating RPL session...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = user?.role || 'ASSESSOR';
    if (!allowedRoles.includes(userRole)) {
      return <Navigate to="/" replace />;
    }
  }

  return children;
}
