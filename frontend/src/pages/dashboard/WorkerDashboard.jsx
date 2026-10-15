import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import {
  Users,
  ClipboardCheck,
  FileCheck2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Cpu,
  FileText,
  Briefcase,
  Award,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Plus
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { workersApi } from '../../api/workers.api';
import { evidenceApi } from '../../api/evidence.api';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/Badge';
import { Skeleton } from '../../components/ui/Skeleton';
import { formatDate } from '../../lib/date';

export function WorkerDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Fetch current worker profile
  const {
    data: workerData,
    isLoading: workerLoading,
  } = useQuery({
    queryKey: ['worker-profile-me'],
    queryFn: async () => {
      try {
        return await workersApi.getMyProfile();
      } catch (err) {
        // Fallback to getById with user ID
        if (user?.id) {
          return await workersApi.getById(user.id);
        }
        throw err;
      }
    },
    enabled: !!user?.id,
  });

  const worker = workerData || {};
  const workerId = worker.id || user?.id;

  // Fetch worker-specific assessments
  const {
    data: assessmentsData,
    isLoading: assessmentsLoading,
  } = useQuery({
    queryKey: ['worker-assessments', workerId],
    queryFn: () => workersApi.getWorkerAssessments(workerId),
    enabled: !!workerId,
  });

  // Fetch worker-specific evidence
  const {
    data: evidenceData,
    isLoading: evidenceLoading,
  } = useQuery({
    queryKey: ['worker-evidence', workerId],
    queryFn: async () => {
      try {
        return await workersApi.getWorkerEvidence(workerId);
      } catch (err) {
        const res = await evidenceApi.getAll({ limit: 100 });
        return res?.items || res || [];
      }
    },
    enabled: !!workerId,
  });

  // Fetch worker competency profile
  const {
    data: competencyProfile,
    isLoading: competencyLoading,
  } = useQuery({
    queryKey: ['worker-competency-profile', workerId],
    queryFn: () => workersApi.getWorkerCompetencyProfile(workerId),
    enabled: !!workerId,
  });

  const assessments = Array.isArray(assessmentsData) ? assessmentsData : (assessmentsData?.items || []);
  const evidenceList = Array.isArray(evidenceData) ? evidenceData : (evidenceData?.items || []);
  const competencies = competencyProfile?.competencies || [];
  const declaredSkills = worker.declared_skills || [];
  const totalSkills = competencies.length > 0 ? competencies.length : declaredSkills.length;

  // Calculate metrics
  const totalAssessments = assessments.length;
  const verifiedEvidence = evidenceList.filter((e) => e.verification_status === 'VERIFIED').length;
  const pendingEvidence = evidenceList.filter((e) => e.verification_status === 'PENDING' || e.verification_status === 'UNVERIFIED').length;
  const reviewedAssessments = assessments.filter((a) => ['READY_FOR_REVIEW', 'REVIEWED', 'COMPLETED', 'CERTIFIED'].includes(a.status)).length;
  const certifiedAssessments = assessments.filter((a) => a.status === 'CERTIFIED' || a.status === 'COMPLETED').length;

  // RPL Journey Stages
  const stages = [
    {
      id: 'profile',
      number: 1,
      title: 'Personal Profile',
      desc: 'Contact details & trade',
      status: (worker.full_name && worker.trade) ? 'COMPLETED' : 'IN_PROGRESS',
      link: '/workers/profile',
    },
    {
      id: 'experience',
      number: 2,
      title: 'Work Experience',
      desc: `${worker.years_of_experience || 0} yrs documented`,
      status: (worker.years_of_experience > 0) ? 'COMPLETED' : (worker.full_name ? 'IN_PROGRESS' : 'PENDING'),
      link: '/workers/experience',
    },
    {
      id: 'evidence',
      number: 3,
      title: 'Evidence Submission',
      desc: `${evidenceList.length} items submitted`,
      status: evidenceList.length > 0 ? (verifiedEvidence > 0 ? 'COMPLETED' : 'IN_PROGRESS') : 'PENDING',
      link: '/evidence',
    },
    {
      id: 'assessment',
      number: 4,
      title: 'Skill Assessment',
      desc: `${totalAssessments} active assessments`,
      status: totalAssessments > 0 ? 'IN_PROGRESS' : 'PENDING',
      link: '/assessments',
    },
    {
      id: 'review',
      number: 5,
      title: 'Assessor Review',
      desc: reviewedAssessments > 0 ? 'Under review' : 'Awaiting assessment',
      status: reviewedAssessments > 0 ? 'IN_PROGRESS' : 'PENDING',
      link: '/assessments',
    },
    {
      id: 'recognition',
      number: 6,
      title: 'Formal Recognition',
      desc: certifiedAssessments > 0 ? 'Certified' : 'Final decision',
      status: certifiedAssessments > 0 ? 'COMPLETED' : 'PENDING',
      link: '/reports',
    },
  ];

  // Determine Next Best Action
  let nextAction = {
    title: 'Complete Your Personal Profile',
    desc: 'Provide your primary trade, contact information, and educational background to begin your RPL journey.',
    cta: 'Edit Profile',
    link: '/workers/profile',
    icon: Users,
    urgency: 'high',
  };

  if (!worker.full_name || !worker.trade || worker.trade === 'General') {
    nextAction = {
      title: 'Specify Your Primary Trade',
      desc: 'Set your trade (e.g. Electrical Installation, Welding & Fabrication) to map your skills to National Occupational Standards.',
      cta: 'Update Trade Standard',
      link: '/workers/profile',
      icon: Briefcase,
      urgency: 'high',
    };
  } else if (!worker.years_of_experience || worker.years_of_experience === 0) {
    nextAction = {
      title: 'Document Your Work Experience',
      desc: 'Add your years of on-the-job experience, informal apprenticeships, and previous workshop background.',
      cta: 'Add Work Experience',
      link: '/workers/experience',
      icon: Briefcase,
      urgency: 'high',
    };
  } else if (evidenceList.length === 0) {
    nextAction = {
      title: 'Submit Supporting Work Evidence',
      desc: 'Upload photographs of your practical work, reference letters, or workshop certificates to prove your skills.',
      cta: 'Upload First Evidence',
      link: '/evidence',
      icon: FileCheck2,
      urgency: 'high',
    };
  } else if (pendingEvidence > 0 && verifiedEvidence === 0) {
    nextAction = {
      title: 'Evidence Under Assessor Review',
      desc: `You have ${pendingEvidence} evidence item(s) awaiting verification by your qualified assessor.`,
      cta: 'Track Evidence Queue',
      link: '/evidence',
      icon: Clock,
      urgency: 'medium',
    };
  } else if (assessments.length === 0) {
    nextAction = {
      title: 'Track Your RPL Assessment',
      desc: 'Your evidence has been received. Your assessor will schedule your practical evaluation tasks.',
      cta: 'View Assessment Status',
      link: '/assessments',
      icon: ClipboardCheck,
      urgency: 'medium',
    };
  } else {
    nextAction = {
      title: 'Review Competency Twin Profile',
      desc: 'Review how your verified evidence matches against National Occupational Standards (NOS).',
      cta: 'Explore My Skills',
      link: '/competencies',
      icon: Cpu,
      urgency: 'low',
    };
  }

  // Real activity events
  const activityList = [
    ...assessments.map((a) => ({
      id: `a-${a.id}`,
      type: 'assessment',
      title: `Assessment for ${a.trade}`,
      subtitle: `Status: ${a.status.replace(/_/g, ' ')}`,
      status: a.status,
      timestamp: a.updated_at || a.created_at,
    })),
    ...evidenceList.map((e) => ({
      id: `e-${e.id}`,
      type: 'evidence',
      title: e.description || 'Evidence Document',
      subtitle: `Type: ${e.evidence_type} • Status: ${e.verification_status}`,
      status: e.verification_status,
      timestamp: e.updated_at || e.created_at,
    })),
  ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 5);

  return (
    <div className="space-y-8 select-none">
      {/* 1. Welcome & Primary Banner */}
      <div className="bg-[#050505] border border-white/10 p-6 sm:p-8 relative overflow-hidden specular-top-edge">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 relative z-10">
          <div className="space-y-3 max-w-2xl">
            <div className="flex items-center gap-2 font-mono text-xs text-zinc-400 uppercase tracking-widest">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
              <span>KaushalTwin • Worker RPL Portal</span>
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight">
                Welcome, {worker.full_name || user?.name || 'Worker'}
              </h1>
              <p className="text-zinc-400 text-xs sm:text-sm font-sans mt-1">
                Primary Trade: <span className="text-white font-medium">{worker.trade || 'Candidate'}</span>
                {worker.years_of_experience > 0 && (
                  <span className="text-zinc-500"> • {worker.years_of_experience} Years Practical Experience</span>
                )}
              </p>
            </div>
            <div className="bg-[#080808] border border-white/5 p-4 rounded-none">
              <p className="text-zinc-300 text-xs sm:text-sm leading-relaxed font-sans">
                "Your skills deserve recognition. Turn the experience you've gained through work into a structured skills profile, supported by evidence and reviewed by a qualified assessor."
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/workers/profile')}
              className="font-mono text-xs"
            >
              My Profile
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate(nextAction.link)}
              className="font-mono text-xs"
            >
              <nextAction.icon className="w-3.5 h-3.5 mr-1.5" />
              <span>{nextAction.cta}</span>
            </Button>
          </div>
        </div>

        {/* Reassurance Footer */}
        <div className="mt-6 pt-4 border-t border-white/10 flex flex-wrap items-center justify-between text-[11px] font-sans text-zinc-400 gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-zinc-300">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
              <span className="font-medium">NCVET Guidelines Standard</span>
            </div>
            <span>•</span>
            <span>Evidence-Based Skill Recognition</span>
          </div>
          <div className="flex items-center gap-1.5 text-zinc-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Certified Assessor Governance</span>
          </div>
        </div>
      </div>

      {/* 2. RPL Journey Tracker */}
      <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wider font-mono uppercase flex items-center gap-2">
              <Award className="w-4 h-4 text-emerald-400" />
              <span>Recognition of Prior Learning (RPL) Journey</span>
            </h2>
            <p className="text-xs text-zinc-400 font-sans mt-0.5">
              Transparent, step-by-step path from practical experience to certified competency
            </p>
          </div>
          <span className="text-[10px] font-mono text-zinc-500 uppercase">
            Phase {stages.filter((s) => s.status === 'COMPLETED').length} of {stages.length} Completed
          </span>
        </div>

        {/* Stage Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 pt-2">
          {stages.map((stage) => {
            const isCompleted = stage.status === 'COMPLETED';
            const isInProgress = stage.status === 'IN_PROGRESS';
            return (
              <Link
                key={stage.id}
                to={stage.link}
                className={`p-3.5 border transition-all relative block ${
                  isCompleted
                    ? 'bg-emerald-950/20 border-emerald-700/40 hover:border-emerald-500/60'
                    : isInProgress
                    ? 'bg-amber-950/20 border-amber-600/40 hover:border-amber-400/60'
                    : 'bg-[#080808] border-white/10 hover:border-white/25 opacity-70'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] text-zinc-400 font-bold">
                    STEP 0{stage.number}
                  </span>
                  {isCompleted ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : isInProgress ? (
                    <Clock className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-zinc-700" />
                  )}
                </div>
                <div className="font-mono text-xs font-semibold text-white truncate">
                  {stage.title}
                </div>
                <div className="text-[10px] text-zinc-400 font-sans mt-0.5 truncate">
                  {stage.desc}
                </div>
                <div className="mt-2.5">
                  <span
                    className={`inline-block text-[9px] font-mono px-1.5 py-0.5 uppercase tracking-wider ${
                      isCompleted
                        ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50'
                        : isInProgress
                        ? 'bg-amber-900/50 text-amber-300 border border-amber-700/50'
                        : 'bg-zinc-900 text-zinc-500 border border-zinc-800'
                    }`}
                  >
                    {isCompleted ? 'Completed' : isInProgress ? 'In Progress' : 'Pending'}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* 3. Next Best Action Prompt */}
      <div className="bg-[#050505] border border-white/10 p-5 sm:p-6 specular-top-edge">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 border border-white/20 bg-[#0a0a0a] flex items-center justify-center flex-shrink-0 mt-0.5">
              <nextAction.icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-1.5 py-0.5 bg-amber-950/40 text-amber-300 border border-amber-700/40 uppercase">
                  Recommended Action
                </span>
                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  {nextAction.title}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-zinc-400 font-sans mt-1 leading-relaxed max-w-2xl">
                {nextAction.desc}
              </p>
            </div>
          </div>
          <Button
            variant="primary"
            onClick={() => navigate(nextAction.link)}
            className="font-mono text-xs self-start md:self-center flex-shrink-0"
          >
            <span>{nextAction.cta}</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Button>
        </div>
      </div>

      {/* 4. Personal Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Work Experience */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Years Experience
            </span>
            <Briefcase className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {workerLoading ? <Skeleton className="h-9 w-16" /> : `${worker.years_of_experience || 0} Yrs`}
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>Trade background</span>
            <span className="text-zinc-300 font-mono text-[10px]">{worker.trade || 'General'}</span>
          </div>
        </div>

        {/* Metric 2: Skills Identified */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Skills Identified
            </span>
            <Cpu className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {competencyLoading ? <Skeleton className="h-9 w-16" /> : totalSkills}
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>Mapped to standards</span>
            <Link to="/competencies" className="text-white hover:underline text-[10px] font-mono">
              View Skills →
            </Link>
          </div>
        </div>

        {/* Metric 3: Evidence Submitted */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Evidence Items
            </span>
            <FileCheck2 className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {evidenceLoading ? <Skeleton className="h-9 w-16" /> : evidenceList.length}
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>Verified: <strong className="text-emerald-400">{verifiedEvidence}</strong></span>
            <span>Pending: <strong className="text-amber-400">{pendingEvidence}</strong></span>
          </div>
        </div>

        {/* Metric 4: Assessments */}
        <div className="bg-[#050505] border border-white/10 p-5 specular-top-edge transition-all hover:border-white/30">
          <div className="flex items-center justify-between text-zinc-500 mb-2">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
              Assessments
            </span>
            <ClipboardCheck className="w-4 h-4 text-zinc-400" />
          </div>
          <div className="text-3xl sm:text-4xl font-mono font-bold text-white tracking-tight">
            {assessmentsLoading ? <Skeleton className="h-9 w-16" /> : totalAssessments}
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] font-sans text-zinc-400 border-t border-white/5 pt-2">
            <span>Reviewed: <strong className="text-white">{reviewedAssessments}</strong></span>
            <Link to="/assessments" className="text-white hover:underline text-[10px] font-mono">
              Track →
            </Link>
          </div>
        </div>
      </div>

      {/* 5. Two-column Section: Recent Activity & Quick Navigation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Activity (2 cols) */}
        <div className="lg:col-span-2 bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h2 className="text-xs font-bold text-white tracking-wider font-mono uppercase flex items-center gap-2">
              <Clock className="w-4 h-4 text-zinc-400" />
              <span>Recent Activity &amp; Status Updates</span>
            </h2>
            <span className="text-[10px] font-mono text-zinc-500">Live API updates</span>
          </div>

          {activityList.length === 0 ? (
            <div className="py-8 text-center space-y-2">
              <p className="text-xs font-mono text-zinc-500">No recent activity recorded yet.</p>
              <p className="text-xs text-zinc-400 font-sans max-w-sm mx-auto">
                Submit work evidence or complete your profile to start generating activity updates.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/evidence')}
                className="mt-3 text-xs font-mono"
              >
                Submit Evidence Now
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              {activityList.map((item) => (
                <div key={item.id} className="py-3 flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 bg-[#0a0a0a] border border-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      {item.type === 'assessment' ? (
                        <ClipboardCheck className="w-3.5 h-3.5 text-zinc-300" />
                      ) : (
                        <FileCheck2 className="w-3.5 h-3.5 text-zinc-300" />
                      )}
                    </div>
                    <div>
                      <div className="text-xs font-mono font-medium text-white">
                        {item.title}
                      </div>
                      <div className="text-[11px] text-zinc-400 font-sans mt-0.5">
                        {item.subtitle}
                      </div>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <StatusBadge status={item.status} size="sm" />
                    <div className="text-[10px] text-zinc-500 font-mono mt-1">
                      {formatDate(item.timestamp)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: How RPL Works Quick Help */}
        <div className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4">
          <div className="border-b border-white/10 pb-3">
            <h2 className="text-xs font-bold text-white tracking-wider font-mono uppercase flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-emerald-400" />
              <span>How RPL Works</span>
            </h2>
            <p className="text-[11px] text-zinc-400 font-sans mt-0.5">
              Guidance for skilled workers
            </p>
          </div>

          <div className="space-y-3.5 text-xs text-zinc-300 font-sans">
            <div className="space-y-1">
              <div className="font-mono text-[11px] text-white font-semibold flex items-center gap-1.5">
                <span className="text-emerald-400">01.</span> Document Work
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Add your years of practical experience and upload photos of your real projects or tools.
              </p>
            </div>

            <div className="space-y-1">
              <div className="font-mono text-[11px] text-white font-semibold flex items-center gap-1.5">
                <span className="text-emerald-400">02.</span> AI Maps Skills
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Our system compares your evidence against National Occupational Standards (NOS).
              </p>
            </div>

            <div className="space-y-1">
              <div className="font-mono text-[11px] text-white font-semibold flex items-center gap-1.5">
                <span className="text-emerald-400">03.</span> Assessor Evaluates
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                A qualified human assessor reviews your portfolio and conducts practical skill checks.
              </p>
            </div>

            <div className="space-y-1">
              <div className="font-mono text-[11px] text-white font-semibold flex items-center gap-1.5">
                <span className="text-emerald-400">04.</span> Receive Recognition
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                Earn government-recognized certification for the skills you already practice daily.
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-white/10">
            <Link
              to="/"
              className="text-xs font-mono text-zinc-300 hover:text-white flex items-center gap-1 transition-colors"
            >
              <span>Read Full RPL Guidelines</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WorkerDashboard;