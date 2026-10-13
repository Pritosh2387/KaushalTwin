import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';

// Pages
import { LandingPage } from './pages/landing/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { WorkersPage } from './pages/workers/WorkersPage';
import { WorkerDetailPage } from './pages/workers/WorkerDetailPage';
import { AssessmentsPage } from './pages/assessments/AssessmentsPage';
import { AssessmentWorkspacePage } from './pages/assessments/AssessmentWorkspacePage';
import { EvidencePage } from './pages/evidence/EvidencePage';
import { CompetenciesPage } from './pages/competencies/CompetenciesPage';
import { ReportsPage } from './pages/reports/ReportsPage';
import { AuditPage } from './pages/audit/AuditPage';
import { SettingsPage } from './pages/settings/SettingsPage';

// Configure TanStack Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Cinematic Hero Landing Page */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/hero" element={<LandingPage />} />

            {/* Public Auth Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Authenticated Application Shell */}
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/overview" element={<Navigate to="/dashboard" replace />} />
              <Route path="/app" element={<Navigate to="/dashboard" replace />} />
              <Route path="/workers" element={<WorkersPage />} />
              <Route path="/workers/:id" element={<WorkerDetailPage />} />
              <Route path="/assessments" element={<AssessmentsPage />} />
              <Route path="/assessments/:id" element={<AssessmentWorkspacePage />} />
              <Route path="/evidence" element={<EvidencePage />} />
              <Route path="/competencies" element={<CompetenciesPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/audit" element={<AuditPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
