import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { DashboardPage } from './DashboardPage';
import { WorkerDashboard } from './WorkerDashboard';

export function RoleBasedDashboard() {
  const { isWorker } = useAuth();

  if (isWorker) {
    return <WorkerDashboard />;
  }

  return <DashboardPage />;
}

export default RoleBasedDashboard;