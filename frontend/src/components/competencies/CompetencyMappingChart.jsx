import React, { useState, useEffect, useMemo } from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import {
  Cpu,
  ShieldCheck,
  AlertCircle,
  Compass,
} from 'lucide-react';
import { Skeleton } from '../ui/Skeleton';
import { normalizeCompetency, wrapText } from '../../lib/competencies';

// Re-export for test/consumer compatibility
export { normalizeCompetency, wrapText, CustomYAxisTick };

/**
 * Custom Y-Axis Category Tick Component
 * Displays:
 * Line 1 (and 2 if wrapped): High-contrast full competency title
 * Secondary line: Muted, smaller monospace NOS code
 * Includes native SVG <title> for full accessibility and zero-truncation guarantee.
 */
function CustomYAxisTick({ x, y, payload, index, dataMap, isMobile }) {
  if (!payload) return null;

  const item = dataMap?.get(payload.value) || dataMap?.get(index) || {};
  const fullName = item.fullName || item.competency_name || payload.value || '';
  const nosId = item.nos_id || item.id || '';

  const maxChars = isMobile ? 18 : 26;
  const lines = wrapText(fullName, maxChars);
  // If no lines (e.g. empty name), fallback to nosId
  const displayLines = lines.length > 0 ? lines : [nosId || 'Standard'];
  const showNosId = Boolean(nosId && (!fullName || !fullName.includes(nosId)));

  const fontSizeTitle = isMobile ? 10 : 11;
  const fontSizeCode = isMobile ? 9 : 9.5;
  const tickX = Math.max(10, (x || 0) - 12);

  return (
    <g
      className="custom-y-axis-tick"
      data-testid={`y-axis-tick-${nosId || index}`}
      aria-label={`${fullName}${nosId ? ` (${nosId})` : ''}`}
    >
      <title>{`${fullName}${nosId ? ` (${nosId})` : ''}`}</title>
      <text
        x={tickX}
        y={y}
        textAnchor="end"
      >
        {displayLines.length === 1 ? (
          <>
            <tspan
              x={tickX}
              dy={showNosId ? '-0.35em' : '0.35em'}
              fill="#f4f4f5"
              fontSize={fontSizeTitle}
              fontWeight="600"
              fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
            >
              {displayLines[0]}
            </tspan>
            {showNosId && (
              <tspan
                x={tickX}
                dy="1.4em"
                fill="#71717a"
                fontSize={fontSizeCode}
                fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
              >
                {nosId}
              </tspan>
            )}
          </>
        ) : (
          <>
            <tspan
              x={tickX}
              dy={showNosId ? '-0.95em' : '-0.55em'}
              fill="#f4f4f5"
              fontSize={fontSizeTitle}
              fontWeight="600"
              fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
            >
              {displayLines[0]}
            </tspan>
            <tspan
              x={tickX}
              dy="1.25em"
              fill="#f4f4f5"
              fontSize={fontSizeTitle}
              fontWeight="600"
              fontFamily="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
            >
              {displayLines[1]}
            </tspan>
            {showNosId && (
              <tspan
                x={tickX}
                dy="1.35em"
                fill="#71717a"
                fontSize={fontSizeCode}
                fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
              >
                {nosId}
              </tspan>
            )}
          </>
        )}
      </text>
    </g>
  );
}

/**
 * Custom High-Contrast Tooltip for Obsidian Noir
 */
function CustomChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0]?.payload;
  if (!data) return null;

  const candidateScore = data.candidateScore ?? data.Score ?? 0;
  const benchmarkScore = data.benchmarkScore ?? data.Benchmark ?? 70;
  const variance = candidateScore - benchmarkScore;
  const isProficient = candidateScore >= benchmarkScore;

  return (
    <div className="bg-[#0a0a0a] border border-white/20 p-3 shadow-2xl font-mono text-xs max-w-xs space-y-2 pointer-events-none specular-top-edge">
      <div className="border-b border-white/10 pb-1.5">
        <div className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
          {data.nos_id || data.id || 'NOS Standard'}
        </div>
        <div className="text-white font-sans text-xs font-semibold leading-snug">
          {data.fullName || data.competency_name || data.subject || label}
        </div>
      </div>

      <div className="space-y-1 text-[11px]">
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
            <span>Candidate Score:</span>
          </span>
          <span className="font-bold text-white">{candidateScore}%</span>
        </div>

        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-zinc-400">
            <span className="w-2 h-2 rounded-full bg-zinc-500 inline-block" />
            <span>Required Benchmark:</span>
          </span>
          <span className="font-bold text-zinc-300">{benchmarkScore}%</span>
        </div>

        <div className="flex items-center justify-between gap-4 pt-1 border-t border-white/10">
          <span className="text-zinc-500">Alignment Status:</span>
          <span className={isProficient ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
            {isProficient ? `+${variance}% (Benchmark Met)` : `${variance}% (Evidence Deficit)`}
          </span>
        </div>
      </div>

      <div className="text-[9px] font-sans text-zinc-500 pt-1 border-t border-white/5 leading-tight">
        Advisory RPL alignment score • Requires accredited assessor verification
      </div>
    </div>
  );
}

/**
 * Main Visualizer Component
 */
export function CompetencyMappingChart({
  competencies = [],
  isLoading = false,
  isError = false,
  errorMessage = null,
  isWorker = false,
  _trade = 'General',
  _onNavigateEvidence = null,
}) {
  const [userViewMode, setUserViewMode] = useState(null); // 'radar' | 'bar' | null
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth < 640;
    }
    return false;
  });

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 640);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Data Sanitization
  const validCompetencies = useMemo(() => {
    return (Array.isArray(competencies) ? competencies : [])
      .map(normalizeCompetency)
      .filter(Boolean);
  }, [competencies]);

  const dimensionsCount = validCompetencies.length;
  const canUseRadar = dimensionsCount >= 3;
  // If fewer than 3 dimensions, STRICTLY use 'bar'. Only allow radar when dimensions >= 3
  const activeView = canUseRadar ? (userViewMode || 'radar') : 'bar';

  // Data for Bar Chart
  const barChartData = useMemo(() => {
    return validCompetencies.map((c, idx) => ({
      id: c.nos_id || `comp-${idx}`,
      nos_id: c.nos_id || '',
      name: c.nos_id || c.shortName,
      fullName: c.competency_name || c.name || c.nos_id || `Competency ${idx + 1}`,
      displayName: c.displayName,
      candidateScore: c.score,
      benchmarkScore: c.benchmark,
      isProficient: c.isProficient,
      variance: c.variance,
    }));
  }, [validCompetencies]);

  const dataMap = useMemo(() => {
    const map = new Map();
    barChartData.forEach((item, index) => {
      map.set(item.id, item);
      map.set(index, item);
    });
    return map;
  }, [barChartData]);

  // 1. Loading State
  if (isLoading) {
    return (
      <div
        data-testid="competency-chart-loading"
        className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-4"
      >
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="space-y-1.5">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-64" />
          </div>
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="h-80 sm:h-96 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border border-white/20 bg-[#080808] flex items-center justify-center rotate-45 animate-spin">
            <div className="w-2 h-2 bg-emerald-400 -rotate-45" />
          </div>
          <p className="font-mono text-xs text-zinc-400 uppercase tracking-widest animate-pulse">
            Loading Competency Twin Dimensions...
          </p>
        </div>
      </div>
    );
  }

  // 2. Error State
  if (isError) {
    return (
      <div
        data-testid="competency-chart-error"
        className="bg-[#050505] border border-red-500/30 p-6 sm:p-8 specular-top-edge space-y-4"
      >
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 border border-red-500/40 bg-red-950/30 flex items-center justify-center flex-shrink-0">
            <AlertCircle className="w-5 h-5 text-red-400" />
          </div>
          <div className="space-y-1">
            <div className="font-mono text-xs font-bold text-red-400 uppercase tracking-wider">
              Unable to Load Competency Twin
            </div>
            <p className="text-xs text-zinc-400 font-sans leading-relaxed">
              {errorMessage || 'Failed to retrieve competency standard scores from the evaluation server.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 4. Empty State (Requirement 6: Handle empty data gracefully)
  if (dimensionsCount === 0) {
    return (
      <div
        data-testid="competency-chart-empty"
        className="bg-[#050505] border border-white/10 p-6 sm:p-8 specular-top-edge space-y-6"
      >
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <h2 className="font-mono text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-zinc-400" />
              <span>Competency Twin Visualizer</span>
            </h2>
            <p className="text-[11px] text-zinc-400 font-light mt-0.5">
              Comparison between candidate evaluated mastery and NSQF benchmarks
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 bg-zinc-900 border border-zinc-700 text-zinc-400 uppercase">
            0 Standards Mapped
          </span>
        </div>

        <div className="py-12 px-4 text-center max-w-md mx-auto space-y-4">
          <div className="w-12 h-12 border border-white/15 bg-[#080808] flex items-center justify-center mx-auto text-zinc-400 rotate-45 shadow-[0_0_20px_rgba(255,255,255,0.03)]">
            <Compass className="w-6 h-6 -rotate-45 text-zinc-300" />
          </div>
          <div className="space-y-1.5">
            <h3 className="font-mono text-sm font-bold text-white uppercase tracking-wide">
              No Competency Evaluations Recorded
            </h3>
            <p className="text-xs text-zinc-400 font-sans leading-relaxed">
              {isWorker
                ? 'You do not have any evaluated competency dimensions yet. Speak or type your experience in "Tell Us About Your Work" or submit practical evidence to initiate AI skill mapping.'
                : 'This candidate has not yet undergone AI evidence analysis or practical assessment evaluation. No fabricated scores are displayed.'}
            </p>
          </div>

          <div className="p-3 bg-[#080808] border border-white/10 text-left text-[11px] font-sans text-zinc-400 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong>Strict Data Integrity:</strong> KaushalTwin does not fabricate placeholder scores. The competency twin visualization activates as soon as verified evidence or narrative standards are extracted.
            </div>
          </div>
        </div>
      </div>
    );
  }

  const barChartHeight = Math.max(260, dimensionsCount * (isMobile ? 95 : 85) + 60);
  const yAxisWidth = isMobile ? 150 : 220;

  // 6. Data for Radar Chart (>= 3 items)
  const radarChartData = validCompetencies.map((c) => ({
    id: c.nos_id,
    subject: c.shortName || c.nos_id,
    fullName: c.competency_name,
    Score: c.score,
    Benchmark: c.benchmark,
    variance: c.variance,
    isProficient: c.isProficient,
  }));

  return (
    <div
      data-testid="competency-mapping-chart"
      className="bg-[#050505] border border-white/10 p-6 specular-top-edge space-y-6"
    >
      {/* Visualizer Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-mono text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-400" />
              <span>
                {activeView === 'radar'
                  ? 'COMPETENCY TWIN RADAR MAPPING'
                  : 'COMPETENCY TWIN BENCHMARK COMPARISON'}
              </span>
            </h2>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 uppercase tracking-wider border ${
                dimensionsCount < 3
                  ? 'bg-amber-950/40 text-amber-300 border-amber-600/40'
                  : 'bg-emerald-950/40 text-emerald-300 border-emerald-600/40'
              }`}
            >
              {dimensionsCount < 3
                ? `${dimensionsCount} Standard${dimensionsCount === 1 ? '' : 's'} · Grouped Bar View`
                : `${dimensionsCount} Standards · ${activeView === 'radar' ? 'Radar View' : 'Horizontal Bar View'}`}
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 font-light mt-0.5">
            {dimensionsCount < 3
              ? 'Grouped horizontal comparison rendered to ensure geometric precision without radar distortion.'
              : 'Direct comparison between candidate evaluated mastery and NSQF benchmark thresholds.'}
          </p>
        </div>

        {/* View Controls & Legend */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Toggle between Radar and Bar when >= 3 dimensions */}
          {canUseRadar && (
            <div
              data-testid="chart-view-toggle"
              className="flex items-center bg-[#0a0a0a] border border-white/15 p-0.5 font-mono text-[10px]"
            >
              <button
                type="button"
                onClick={() => setUserViewMode('radar')}
                className={`px-2.5 py-1 uppercase tracking-wider transition-colors cursor-pointer ${
                  activeView === 'radar'
                    ? 'bg-white text-black font-bold'
                    : 'text-zinc-400 hover:text-white'
                }`}
                aria-label="Switch to Radar View"
              >
                Radar
              </button>
              <button
                type="button"
                onClick={() => setUserViewMode('bar')}
                className={`px-2.5 py-1 uppercase tracking-wider transition-colors cursor-pointer ${
                  activeView === 'bar'
                    ? 'bg-white text-black font-bold'
                    : 'text-zinc-400 hover:text-white'
                }`}
                aria-label="Switch to Horizontal Bar View"
              >
                Grouped Bars
              </button>
            </div>
          )}

          {/* Legend */}
          <div className="flex items-center gap-3 text-[10px] font-mono">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2 bg-emerald-400 inline-block rounded-none" />
              <span>CANDIDATE (ADVISORY)</span>
            </span>
            <span className="flex items-center gap-1.5 text-zinc-400">
              <span className="w-2.5 h-0.5 border-b border-dashed border-zinc-400 inline-block" />
              <span>BENCHMARK (NSQF)</span>
            </span>
          </div>
        </div>
      </div>

      {/* Main Chart Surface */}
      <div className="min-h-[300px] w-full flex items-center justify-center">
        {activeView === 'radar' ? (
          /* RADAR CHART (Used when >= 3 dimensions) */
          <div
            data-testid="competency-radar-chart"
            className="h-80 sm:h-96 w-full flex items-center justify-center relative"
          >
            <ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={280}>
              <RadarChart data={radarChartData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="rgba(255, 255, 255, 0.12)" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fill: '#d4d4d8', fontSize: 10, fontFamily: 'monospace' }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  stroke="rgba(255, 255, 255, 0.2)"
                  tick={{ fill: '#71717a', fontSize: 9, fontFamily: 'monospace' }}
                />
                <Tooltip content={<CustomChartTooltip />} />
                <Radar
                  name="Candidate Score"
                  dataKey="Score"
                  stroke="#34d399"
                  strokeWidth={2}
                  fill="#10b981"
                  fillOpacity={0.16}
                />
                <Radar
                  name="NOS Benchmark"
                  dataKey="Benchmark"
                  stroke="rgba(255, 255, 255, 0.55)"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  fill="none"
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          /* HORIZONTAL GROUPED BAR CHART (Used when < 3 dimensions, or toggled) */
          <div
            data-testid="competency-grouped-bar-chart"
            className="w-full space-y-4 py-2"
          >
            <div
              className="w-full transition-all duration-200"
              style={{ height: `${barChartHeight}px` }}
            >
              <ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={220}>
                <BarChart
                  data={barChartData}
                  layout="vertical"
                  margin={{
                    top: 15,
                    right: 30,
                    left: isMobile ? 8 : 14,
                    bottom: 15,
                  }}
                  barGap={6}
                  barCategoryGap={isMobile ? 16 : 24}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255, 255, 255, 0.08)"
                    horizontal={false}
                  />
                  <XAxis
                    type="number"
                    domain={[0, 100]}
                    ticks={[0, 25, 50, 70, 75, 100]}
                    unit="%"
                    tick={{ fill: '#71717a', fontSize: 10, fontFamily: 'monospace' }}
                    stroke="rgba(255, 255, 255, 0.15)"
                  />
                  <YAxis
                    type="category"
                    dataKey="id"
                    width={yAxisWidth}
                    interval={0}
                    tick={<CustomYAxisTick dataMap={dataMap} isMobile={isMobile} />}
                    stroke="rgba(255, 255, 255, 0.15)"
                  />
                  <Tooltip
                    content={<CustomChartTooltip />}
                    cursor={{ fill: 'rgba(255, 255, 255, 0.04)' }}
                  />
                  <ReferenceLine
                    x={70}
                    stroke="rgba(255, 255, 255, 0.3)"
                    strokeDasharray="3 3"
                    label={{
                      value: 'Benchmark 70%',
                      fill: '#a1a1aa',
                      fontSize: 9,
                      position: 'insideTopRight',
                    }}
                  />
                  <Bar
                    dataKey="candidateScore"
                    name="Candidate Score"
                    fill="#10b981"
                    radius={[0, 2, 2, 0]}
                    barSize={16}
                  />
                  <Bar
                    dataKey="benchmarkScore"
                    name="Required Benchmark"
                    fill="#52525b"
                    radius={[0, 2, 2, 0]}
                    barSize={16}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Comprehensive Full-Label Dimension Breakdown List (Zero Truncation) */}
      <div className="space-y-3 pt-4 border-t border-white/10">
        <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
          <span>Evaluated Competency Dimensions ({dimensionsCount})</span>
          <span className="text-zinc-500">Unclipped Standards Registry</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {validCompetencies.map((comp, idx) => {
            const isProficient = comp.isProficient;
            return (
              <div
                key={comp.nos_id || idx}
                data-testid={`competency-row-${comp.nos_id || idx}`}
                className="p-3.5 bg-[#080808] border border-white/10 space-y-2 relative"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <span className="font-mono text-[10px] text-zinc-500 font-bold block">
                      {comp.nos_id}
                    </span>
                    <h4 className="text-xs font-semibold text-white font-sans leading-snug">
                      {comp.competency_name}
                    </h4>
                  </div>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 uppercase tracking-wider flex-shrink-0 ${
                      isProficient
                        ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-600/40'
                        : 'bg-amber-950/60 text-amber-300 border border-amber-600/40'
                    }`}
                  >
                    {isProficient ? 'Proficient' : 'Needs Evidence'}
                  </span>
                </div>

                {/* Score vs Benchmark bar */}
                <div className="space-y-1 font-mono text-[10px]">
                  <div className="flex items-center justify-between text-zinc-400">
                    <span>Candidate: <strong className="text-emerald-400">{comp.score}%</strong></span>
                    <span>Benchmark: <strong className="text-zinc-300">{comp.benchmark}%</strong></span>
                    <span className={comp.variance >= 0 ? 'text-emerald-400' : 'text-amber-400'}>
                      {comp.variance >= 0 ? `+${comp.variance}%` : `${comp.variance}%`}
                    </span>
                  </div>

                  <div className="h-1.5 w-full bg-[#141416] relative overflow-hidden">
                    <div
                      className={`h-full ${isProficient ? 'bg-emerald-400' : 'bg-amber-400'} transition-all`}
                      style={{ width: `${comp.score}%` }}
                    />
                    <div
                      className="absolute top-0 bottom-0 w-[2px] bg-white"
                      style={{ left: `${comp.benchmark}%` }}
                      title={`Benchmark: ${comp.benchmark}%`}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-[10px] font-sans text-zinc-500 pt-1 border-t border-white/5">
                  <span>Evidence: {comp.evidence_count} submitted</span>
                  <span className="text-zinc-400">Status: {comp.status}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Advisory & Governance Disclaimer (Requirement 7) */}
      <div className="p-3.5 bg-[#080808] border border-white/10 flex items-start gap-2.5 text-[11px] font-sans text-zinc-400 leading-normal">
        <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-white font-mono uppercase text-[10px] block mb-0.5">
            Advisory RPL Alignment Notice:
          </strong>
          Calculated scores represent algorithmic semantic matching against National Occupational Standards (NOS). These metrics are strictly advisory recommendations for the candidate and assessor, and do not constitute verified mastery, qualification, or government certification until validated by a certified assessor.
        </div>
      </div>
    </div>
  );
}

export default CompetencyMappingChart;
