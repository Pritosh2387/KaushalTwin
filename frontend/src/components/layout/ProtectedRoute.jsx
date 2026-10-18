import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, isLoading: loading, user } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#000000] flex flex-col items-center justify-center p-6 space-y-4">
        <div className="w-10 h-10 border border-white/20 bg-[#050505] flex items-center justify-center rotate-45 shadow-[0_0_20px_rgba(255,255,255,0.1)]">
          <div className="w-4 h-4 border border-white border-t-transparent animate-spin -rotate-45" />
        </div>
        <p className="text-xs font-mono text-zinc-500 uppercase tracking-widest animate-pulse">
          AUTHENTICATING RPL SESSION...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/?login=true" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = user?.role || 'ASSESSOR';
    if (!allowedRoles.includes(userRole)) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
}

export default ProtectedRoute;
