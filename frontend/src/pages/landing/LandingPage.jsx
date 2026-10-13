import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowUpRight,
  ChevronDown,
  Layers,
  Cpu,
  FileCheck2,
  ShieldCheck,
  Activity,
  Sparkles,
  Terminal,
  Compass,
  CheckCircle,
  ExternalLink,
  Users,
  ClipboardList
} from 'lucide-react';
import { ObsidianCrystalHero } from '../../components/3d/ObsidianCrystalHero';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { useAuth } from '../../context/AuthContext';

export function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [activeFacet, setActiveFacet] = useState(0);

  const capabilities = [
    { id: '01', title: 'Evidence Verification', subtitle: 'Multi-modal portfolio verification & tampering detection' },
    { id: '02', title: 'Competency Twin', subtitle: 'Dynamic skill profile mapped to National Occupational Standards' },
    { id: '03', title: 'Standards Alignment', subtitle: 'Semantic alignment against NSQF and NCVET benchmarks' },
    { id: '04', title: 'Assessor Governance', subtitle: 'AI provides advisory insights; certified assessors decide' },
  ];

  const mlArchitectureModules = [
    { code: '01', name: 'Multilingual Voice & Trade Dialogue', desc: 'Dialect translation & informal trade vernacular parsing' },
    { code: '02', name: 'Skill Extraction & Standard Mapping', desc: 'Semantic matching against NSDC & NCVET job roles' },
    { code: '03', name: 'Competency Twin Engine', desc: 'Dynamic mastery scoring & probabilistic skill vectors' },
    { code: '04', name: 'Evidence Portfolio Verification', desc: 'Authenticity scoring for work samples, photos & logbooks' },
    { code: '05', name: 'Adaptive Skill Assessments', desc: 'Targeted practical exercises and real-world trade tasks' },
    { code: '06', name: 'Skill Gap & Learning Pathways', desc: 'Transparent gap identification & bridge learning plans' },
    { code: '07', name: 'Evidence Sufficiency Safeguards', desc: 'Requires sufficient evidence before suggesting certification' },
    { code: '08', name: 'Assessor Calibration & Consistency', desc: 'Quality assurance to ensure fairness across testing centers' },
    { code: '09', name: 'Human-Governed Advisory Engine', desc: 'Actionable advisory recommendations with assessor control' },
    { code: '10', name: 'Verifiable Audit & Transparency', desc: 'Tamper-evident activity logs and explainable reasoning' },
  ];

  const handleEnterPlatform = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  const scrollToExplore = () => {
    const el = document.getElementById('explore-system');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#000000] text-white selection:bg-white selection:text-black font-sans relative overflow-x-hidden">
      {/* Subtle background ambient grid & light sweep */}
      <div className="absolute inset-0 obsidian-grid opacity-30 pointer-events-none" />

      {/* Top Editorial Monochromatic Navigation */}
      <header className="relative z-30 h-20 px-6 lg:px-16 flex items-center justify-between border-b border-white/10 bg-black/80 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 border border-white/40 bg-[#050505] flex items-center justify-center rotate-45">
            <div className="w-3.5 h-3.5 bg-white -rotate-45" />
          </div>
          <div className="flex flex-col">
            <span className="font-mono text-sm tracking-widest font-bold uppercase text-white">
              KAUSHALTWIN
            </span>
            <span className="font-mono text-[9px] text-zinc-500 tracking-ultra-wide uppercase">
              SKILL INTELLIGENCE • RPL CERTIFICATION
            </span>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-8 font-mono text-xs tracking-widest text-zinc-400">
          <a href="#explore-system" className="hover:text-white transition-colors">
            ARCHITECTURE
          </a>
          <a href="#competency-twin" className="hover:text-white transition-colors">
            COMPETENCY TWIN
          </a>
          <a href="#assessor-governance" className="hover:text-white transition-colors">
            ASSESSOR ETHICS
          </a>
        </nav>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <Button
              onClick={() => navigate('/dashboard')}
              variant="primary"
              size="sm"
            >
              GO TO DASHBOARD ↗
            </Button>
          ) : (
            <div className="flex items-center gap-3">
              <Button
                onClick={() => navigate('/login')}
                variant="secondary"
                size="sm"
              >
                Sign In
              </Button>
              <Button
                onClick={handleEnterPlatform}
                variant="primary"
                size="sm"
              >
                Get Started ↗
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* =========================================
          SECTION 1: HERO VIEWPORT (EXACT COMPOSITION)
          ========================================= */}
      <section className="relative min-h-[calc(100vh-5rem)] flex flex-col justify-between px-6 lg:px-16 pt-12 pb-6 z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-4 items-center flex-1 my-auto">
          {/* Left Side: Editorial Typography & Actions */}
          <div className="lg:col-span-7 flex flex-col justify-center space-y-8 z-20 max-w-2xl">
            {/* Small uppercase label */}
            <div className="flex items-center gap-3 font-mono text-xs uppercase tracking-mega-wide text-zinc-400">
              <span className="w-2 h-2 bg-white" />
              <span>KAUSHALTWIN • SKILL INTELLIGENCE</span>
            </div>

            {/* Main Heading: Oversized White Geometric Typography */}
            <h1 className="text-5xl sm:text-7xl xl:text-8xl font-black text-white tracking-tighter leading-[0.92] select-none uppercase">
              Every Skill.
              <br />
              <span className="text-zinc-200">A New</span>{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-zinc-300 to-zinc-500">
                Dimension.
              </span>
            </h1>

            {/* Supporting Copy */}
            <p className="text-base sm:text-lg text-zinc-400 font-light max-w-xl leading-relaxed tracking-wide">
              Discover, assess, and recognize skills through intelligent evidence-driven assessment.
              Engineered for National Occupational Standards with human-governed certification.
            </p>

            {/* Actions: Primary & Secondary */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-3">
              <Button
                onClick={handleEnterPlatform}
                variant="primary"
                size="lg"
                className="text-xs sm:text-sm font-semibold tracking-wider px-8 py-3.5 uppercase"
              >
                Get Started ↗
              </Button>

              <button
                type="button"
                onClick={scrollToExplore}
                className="inline-flex items-center justify-center font-mono text-xs tracking-wider uppercase text-zinc-300 hover:text-white px-6 py-3.5 border border-white/20 hover:border-white/50 bg-[#050505] transition-all cursor-pointer"
              >
                Explore System
              </button>
            </div>

            {/* Subtle Scroll Indicator & Reassuring Standards Annotation */}
            <div className="pt-8 flex flex-col sm:flex-row sm:items-center gap-6 text-[11px] font-sans text-zinc-400 border-t border-white/10">
              <div className="flex items-center gap-2 text-zinc-300 font-mono text-[10px] tracking-wider uppercase">
                <ChevronDown className="w-3.5 h-3.5 animate-bounce text-white" />
                <span>Scroll to explore capabilities</span>
              </div>
              <div className="hidden sm:block text-zinc-700">|</div>
              <div>NSQF &amp; NCVET Aligned</div>
              <div className="hidden xl:block text-zinc-700">|</div>
              <div className="hidden xl:block text-zinc-300 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-white inline-block animate-pulse" />
                <span>Evaluation Engine Active</span>
              </div>
            </div>
          </div>

          {/* Right Side: 3D Obsidian Crystal Hero (40-50% width) */}
          <div className="lg:col-span-5 h-[480px] lg:h-[640px] xl:h-[720px] relative w-full flex items-center justify-center">
            {/* Fine Geometric Orbit Background Overlay */}
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              <div className="w-[85%] h-[85%] border border-white/5 rounded-full" />
              <div className="absolute w-[105%] h-[105%] border border-white/[0.03] rounded-full rotate-45" />
            </div>

            {/* Realistic 3D Obsidian Crystal */}
            <ObsidianCrystalHero />
          </div>
        </div>

        {/* Bottom Edge: Thin silver divider & restrained monochromatic capabilities strip */}
        <div className="mt-8 pt-6 border-t border-white/10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {capabilities.map((cap) => (
              <div
                key={cap.id}
                className="group p-4 bg-[#050505] border border-white/10 hover:border-white/30 transition-all cursor-pointer specular-top-edge"
                onClick={scrollToExplore}
              >
                <div className="font-mono text-[10px] text-zinc-500 tracking-widest mb-1 group-hover:text-white transition-colors">
                  {cap.id}
                </div>
                <div className="font-sans text-xs font-bold text-white tracking-wide uppercase mb-1">
                  {cap.title}
                </div>
                <p className="text-[11px] text-zinc-400 font-light line-clamp-2 leading-relaxed">
                  {cap.subtitle}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =========================================
          SECTION 2: SYSTEM ARCHITECTURE (10 ML MODULES)
          ========================================= */}
      <section id="explore-system" className="relative py-24 px-6 lg:px-16 border-t border-white/10 bg-[#020202]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-8">
            <div className="space-y-2">
              <div className="font-mono text-xs text-zinc-500 uppercase tracking-mega-wide">
                SYSTEM ARCHITECTURE
              </div>
              <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-white">
                INTEGRATED EVALUATION PIPELINE
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-zinc-400 font-light max-w-md leading-relaxed">
              Every stage of the assessment pipeline is transparent, deterministic, and calibrated against National Occupational Standards.
            </p>
          </div>

          {/* Grid of the 10 Embedded ML Modules */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {mlArchitectureModules.map((mod, idx) => (
              <div
                key={mod.code}
                className="bg-[#050505] p-5 border border-white/10 hover:border-white/30 transition-all specular-top-edge flex flex-col justify-between min-h-[170px]"
              >
                <div>
                  <div className="flex items-center justify-between font-mono text-[10px] text-zinc-500 tracking-widest mb-2">
                    <span>MODULE {mod.code}</span>
                    <span className="w-1.5 h-1.5 bg-white/20" />
                  </div>
                  <h3 className="font-sans text-xs font-bold text-white tracking-wide uppercase leading-tight mb-2">
                    {mod.name}
                  </h3>
                </div>
                <p className="text-[11px] text-zinc-400 font-light leading-relaxed">
                  {mod.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =========================================
          SECTION 3: LIVE COMPETENCY TWIN VISUALIZATION PREVIEW
          ========================================= */}
      <section id="competency-twin" className="relative py-24 px-6 lg:px-16 border-t border-white/10 bg-[#000000]">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-5 space-y-6">
            <div className="font-mono text-xs text-zinc-500 uppercase tracking-mega-wide">
              REAL-TIME REPRESENTATION
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-white leading-tight">
              THE DIGITAL COMPETENCY TWIN
            </h2>
            <p className="text-sm text-zinc-400 font-light leading-relaxed">
              Informal trade experience is transformed into structured competency profiles. Each dimension reflects evaluated skills mapped directly to National Occupational Standards (NOS).
            </p>

            <div className="space-y-3 pt-2 font-mono text-xs">
              <div className="p-3 bg-[#050505] border border-white/10 flex items-center justify-between">
                <span className="text-zinc-400">Benchmark Standard:</span>
                <span className="text-white font-bold">NSDC CSC/Q0204 (Welder)</span>
              </div>
              <div className="p-3 bg-[#050505] border border-white/10 flex items-center justify-between">
                <span className="text-zinc-400">Evidence Sufficiency:</span>
                <span className="text-white font-bold">3 Core Criteria Satisfied</span>
              </div>
              <div className="p-3 bg-[#050505] border border-white/10 flex items-center justify-between">
                <span className="text-zinc-400">Certification Authority:</span>
                <span className="text-zinc-300 font-bold">Accredited Assessor Sign-Off</span>
              </div>
            </div>

            <Button
              onClick={() => navigate('/competencies')}
              variant="outline"
              size="md"
              className="mt-4"
            >
              Explore Competency Matrix ↗
            </Button>
          </div>

          {/* Interactive SVG Monochromatic Node Graph Preview */}
          <div className="lg:col-span-7 bg-[#050505] border border-white/15 p-6 sm:p-8 relative specular-top-edge">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-6 font-mono text-xs text-zinc-400">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-white" />
                <span className="text-white font-bold">Candidate Competency Twin: Ramesh Kumar</span>
              </div>
              <span className="text-[10px] text-zinc-400">Skill Coverage: 86.4%</span>
            </div>

            <div className="relative h-72 sm:h-96 w-full flex items-center justify-center">
              {/* Monochromatic Radar Graph / Node Structure */}
              <svg viewBox="0 0 500 500" className="w-full h-full max-h-96">
                {/* Background Concentric Radar Rings */}
                {[50, 100, 150, 200].map((r, i) => (
                  <circle
                    key={i}
                    cx="250"
                    cy="250"
                    r={r}
                    fill="none"
                    stroke="rgba(255,255,255,0.08)"
                    strokeWidth="1"
                    strokeDasharray={i === 3 ? "4 4" : "none"}
                  />
                ))}

                {/* Axes */}
                {[0, 72, 144, 216, 288].map((angle, idx) => {
                  const rad = (angle * Math.PI) / 180;
                  const x = 250 + 200 * Math.sin(rad);
                  const y = 250 - 200 * Math.cos(rad);
                  return (
                    <line
                      key={idx}
                      x1="250"
                      y1="250"
                      x2={x}
                      y2={y}
                      stroke="rgba(255,255,255,0.12)"
                      strokeWidth="1"
                    />
                  );
                })}

                {/* Benchmark Polygon */}
                <polygon
                  points="250,110 376,195 328,358 172,358 124,195"
                  fill="none"
                  stroke="rgba(255,255,255,0.3)"
                  strokeWidth="1.5"
                  strokeDasharray="6 4"
                />

                {/* Candidate Competency Score Polygon */}
                <polygon
                  points="250,85 395,200 310,340 190,345 110,210"
                  fill="rgba(255,255,255,0.06)"
                  stroke="#ffffff"
                  strokeWidth="2"
                />

                {/* Vertices & Nodes */}
                {[
                  { x: 250, y: 85, label: 'CSC/N0204 ARC WELD (92%)' },
                  { x: 395, y: 200, label: 'CSC/N1335 SAFETY (88%)' },
                  { x: 310, y: 340, label: 'CSC/N0205 DRAWINGS (70%)' },
                  { x: 190, y: 345, label: 'CSC/N0203 CUTTING (84%)' },
                  { x: 110, y: 210, label: 'CSC/N0206 TESTING (62%)' },
                ].map((node, i) => (
                  <g key={i}>
                    <circle cx={node.x} cy={node.y} r="4" fill="#ffffff" stroke="#000000" strokeWidth="1.5" />
                    <text
                      x={node.x + (node.x > 250 ? 8 : -8)}
                      y={node.y + (node.y > 250 ? 12 : -8)}
                      fill="#d4d4d8"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor={node.x > 250 ? "start" : "end"}
                    >
                      {node.label}
                    </text>
                  </g>
                ))}
              </svg>
            </div>

            <div className="flex items-center justify-between text-[11px] font-mono text-zinc-500 pt-4 border-t border-white/10">
              <span className="flex items-center gap-2">
                <span className="w-3 h-[2px] bg-white inline-block" /> CANDIDATE PROFILE
              </span>
              <span className="flex items-center gap-2">
                <span className="w-3 h-[1px] border-b border-dashed border-zinc-400 inline-block" /> NOS BENCHMARK
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================
          SECTION 4: ASSESSOR GOVERNANCE & ETHICS
          ========================================= */}
      <section id="assessor-governance" className="relative py-24 px-6 lg:px-16 border-t border-white/10 bg-[#050505]">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <div className="font-mono text-xs text-zinc-500 uppercase tracking-mega-wide">
              ETHICAL RPL GOVERNANCE
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-white">
              HUMAN-IN-THE-LOOP INTEGRITY
            </h2>
            <p className="text-sm text-zinc-400 font-light leading-relaxed">
              Artificial intelligence assists assessors by organizing evidence and highlighting gaps. Every certification decision is reviewed and confirmed by an accredited assessor.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-8 bg-[#000000] border border-white/10 specular-top-edge space-y-4">
              <div className="w-10 h-10 border border-white/20 flex items-center justify-center font-mono text-xs text-white">
                01
              </div>
              <h3 className="font-sans text-sm font-bold text-white uppercase tracking-wider">
                Evidence Sufficiency Safeguards
              </h3>
              <p className="text-xs text-zinc-400 font-light leading-relaxed">
                When candidate evidence is incomplete or inconsistent, the platform flags gaps and prompts assessors for hands-on practical verification.
              </p>
            </div>

            <div className="p-8 bg-[#000000] border border-white/10 specular-top-edge space-y-4">
              <div className="w-10 h-10 border border-white/20 flex items-center justify-center font-mono text-xs text-white">
                02
              </div>
              <h3 className="font-sans text-sm font-bold text-white uppercase tracking-wider">
                Verifiable Audit Trail
              </h3>
              <p className="text-xs text-zinc-400 font-light leading-relaxed">
                Every evaluation score, assessor note, and candidate artifact is securely logged for institutional transparency and regulatory compliance.
              </p>
            </div>

            <div className="p-8 bg-[#000000] border border-white/10 specular-top-edge space-y-4">
              <div className="w-10 h-10 border border-white/20 flex items-center justify-center font-mono text-xs text-white">
                03
              </div>
              <h3 className="font-sans text-sm font-bold text-white uppercase tracking-wider">
                Assessor Consistency
              </h3>
              <p className="text-xs text-zinc-400 font-light leading-relaxed">
                Continuous calibration tracking ensures uniform assessment standards and fair evaluation across all test centers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================
          SECTION 5: ENTER PLATFORM PORTAL CTA
          ========================================= */}
      <section className="relative py-24 px-6 lg:px-16 border-t border-white/10 bg-[#000000]">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="font-mono text-xs text-zinc-500 uppercase tracking-mega-wide">
            PRIOR LEARNING RECOGNITION
          </div>
          <h2 className="text-4xl sm:text-6xl font-black uppercase tracking-tight text-white leading-tight">
            EMPOWER SKILLED WORKERS
          </h2>
          <p className="text-base text-zinc-400 font-light max-w-xl mx-auto leading-relaxed">
            Enter the workspace to review candidate portfolios, verify hands-on trade skills, and award certified credentials.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Button
              onClick={handleEnterPlatform}
              variant="primary"
              size="lg"
              className="text-xs sm:text-sm font-semibold tracking-wider px-10 py-4 uppercase"
            >
              Get Started ↗
            </Button>
            <Button
              onClick={() => navigate('/login')}
              variant="secondary"
              size="lg"
              className="text-xs sm:text-sm tracking-wider px-8 py-4 uppercase"
            >
              Sign In as Assessor
            </Button>
          </div>
        </div>
      </section>

      {/* Editorial Footer */}
      <footer className="h-20 px-6 lg:px-16 border-t border-white/10 bg-[#020202] flex flex-col sm:flex-row items-center justify-between text-[11px] font-sans text-zinc-500 gap-4">
        <div>KaushalTwin • Skill Intelligence Platform</div>
        <div className="flex items-center gap-6">
          <span>Aligned with National Skill Standards</span>
          <span className="text-zinc-400">RPL Prior Learning Recognition</span>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
