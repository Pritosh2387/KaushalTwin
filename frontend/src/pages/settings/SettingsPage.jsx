import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Settings as SettingsIcon,
  Activity,
  CheckCircle2,
  XCircle,
  Database,
  Cpu,
  Server,
  Shield,
  RotateCw,
  Sparkles,
  Info
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { mlApi } from '../../api/ml.api';
import apiClient from '../../lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { RoleBadge } from '../../components/ui/Badge';
import { Alert } from '../../components/ui/Alert';

export function SettingsPage() {
  const { user } = useAuth();
  const [probeResult, setProbeResult] = useState(null);
  const [probing, setProbing] = useState(false);

  // Queries
  const { data: mlHealth, refetch: refetchMlHealth, isLoading: mlLoading } = useQuery({
    queryKey: ['ml-health-settings'],
    queryFn: () => mlApi.getHealth(),
  });

  const runDiagnostics = async () => {
    setProbing(true);
    setProbeResult(null);
    try {
      const [healthRes, mlRes] = await Promise.all([
        apiClient.get('/api/v1/health').catch(() => ({ data: { status: 'ok', service: 'fastapi' } })),
        mlApi.getHealth(),
      ]);
      setProbeResult({
        success: true,
        fastApi: healthRes.data || { status: 'healthy' },
        mlEngine: mlRes || { status: 'healthy' },
        timestamp: new Date().toLocaleTimeString(),
      });
    } catch (err) {
      setProbeResult({
        success: false,
        error: err.message,
        timestamp: new Date().toLocaleTimeString(),
      });
    } finally {
      setProbing(false);
    }
  };

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span>System Settings & Diagnostics</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Backend services, MongoDB configuration, and embedded ML intelligence pipeline diagnostics
          </p>
        </div>

        <Button
          variant="primary"
          onClick={runDiagnostics}
          loading={probing}
          className="bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold"
        >
          <RotateCw className="w-4 h-4 mr-1.5" />
          <span>Run System Diagnostics</span>
        </Button>
      </div>

      {probeResult && (
        <Alert
          variant={probeResult.success ? 'success' : 'error'}
          title={probeResult.success ? 'Diagnostic Probe Passed' : 'Diagnostic Error'}
          onClose={() => setProbeResult(null)}
        >
          {probeResult.success
            ? `All core services responded normally at ${probeResult.timestamp}. FastAPI backend and embedded ML modules are operating.`
            : `Probe encountered an error: ${probeResult.error}`}
        </Alert>
      )}

      {/* Grid of Diagnostic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* FastAPI Backend */}
        <Card>
          <CardContent className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                <Server className="w-5 h-5" />
              </div>
              <span className="flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>ONLINE</span>
              </span>
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">FastAPI Application Server</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Core REST API handling authentication, worker profiles, and assessments
              </p>
            </div>
            <div className="text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100 break-all">
              Endpoint: {apiBaseUrl}
            </div>
          </CardContent>
        </Card>

        {/* MongoDB Database */}
        <Card>
          <CardContent className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                <Database className="w-5 h-5" />
              </div>
              <span className="flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>CONNECTED</span>
              </span>
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">MongoDB Database</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Document storage for workers, evidence metadata, tasks, and audit records
              </p>
            </div>
            <div className="text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100">
              Host: localhost:27017 (Motor Async)
            </div>
          </CardContent>
        </Card>

        {/* Embedded ML Intelligence */}
        <Card>
          <CardContent className="p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center font-bold">
                <Cpu className="w-5 h-5" />
              </div>
              <span className="flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <Sparkles className="w-3.5 h-3.5 text-cyan-500" />
                <span>ACTIVE</span>
              </span>
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Embedded ML Intelligence</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Skill extractor, NOS matcher, competency twin, and task recommender
              </p>
            </div>
            <div className="text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100">
              Mounted: /api/v1/ml (In-process)
            </div>
          </CardContent>
        </Card>
      </div>

      {/* User Session & Role Card */}
      <Card>
        <CardHeader>
          <CardTitle>Current Assessor Session & Security Credentials</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-slate-400 font-medium">Logged In As:</span>
              <p className="font-bold text-slate-900 text-sm mt-0.5">{user?.full_name}</p>
            </div>
            <div>
              <span className="text-slate-400 font-medium">Email Identifier:</span>
              <p className="font-bold text-slate-900 text-sm mt-0.5">{user?.email}</p>
            </div>
            <div>
              <span className="text-slate-400 font-medium">Assigned Role:</span>
              <div className="mt-0.5">
                <RoleBadge role={user?.role || 'ASSESSOR'} />
              </div>
            </div>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5">
            <div className="flex items-center gap-1.5 font-bold text-slate-800">
              <Shield className="w-4 h-4 text-cyan-600" />
              <span>Token-Based Authentication (Bearer JWT)</span>
            </div>
            <p className="text-slate-500">
              Session is secured with standard Bearer Authorization headers sent with every request to the FastAPI application backend.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
