import { vi, describe, it, expect, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CompetencyMappingChart, wrapText, CustomYAxisTick } from '../components/competencies/CompetencyMappingChart';
import { normalizeCompetency } from '../lib/competencies';

// Mock Recharts ResponsiveContainer to provide explicit width/height in jsdom
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => (
      <div className="recharts-responsive-container" style={{ width: 800, height: 500 }}>
        {React.isValidElement(children)
          ? React.cloneElement(children, { width: 800, height: 500 })
          : typeof children === 'function'
            ? children({ width: 800, height: 500 })
            : children}
      </div>
    ),
  };
});

// Mock ResizeObserver for Recharts in jsdom
beforeEach(() => {
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
});

describe('wrapText helper', () => {
  it('returns empty array for empty, whitespace, or invalid inputs', () => {
    expect(wrapText('')).toEqual([]);
    expect(wrapText('   ')).toEqual([]);
    expect(wrapText(null)).toEqual([]);
    expect(wrapText(undefined)).toEqual([]);
    expect(wrapText(123)).toEqual([]);
  });

  it('keeps short titles on a single line', () => {
    const lines = wrapText('Inverter Setup', 26);
    expect(lines).toEqual(['Inverter Setup']);
  });

  it('splits long titles at word boundaries without breaking words mid-string', () => {
    const lines = wrapText('Residential Distribution & Circuit Wiring', 26);
    expect(lines).toHaveLength(2);
    expect(lines[0]).toBe('Residential Distribution &');
    expect(lines[1]).toBe('Circuit Wiring');
  });

  it('handles Earthing & Fault Protection Setup correctly', () => {
    const lines = wrapText('Earthing & Fault Protection Setup', 26);
    expect(lines).toHaveLength(2);
    expect(lines[0]).toBe('Earthing & Fault');
    expect(lines[1]).toBe('Protection Setup');
  });

  it('caps at 2 lines with ellipsis for excessively long descriptions', () => {
    const lines = wrapText('Industrial High Voltage Feeder Line Switchgear Operation and Arc Flash Protection Management', 26);
    expect(lines).toHaveLength(2);
    expect(lines[1]).toMatch(/\.\.\.$/);
  });
});

describe('normalizeCompetency helper', () => {
  it('normalizes valid decimal scores to 0-100 percentages', () => {
    const res = normalizeCompetency({
      nos_id: 'ELE/N5801',
      competency_name: 'Residential Distribution & Circuit Wiring',
      score: 0.82,
      benchmark: 0.70,
    });
    expect(res).not.toBeNull();
    expect(res.score).toBe(82);
    expect(res.benchmark).toBe(70);
    expect(res.isProficient).toBe(true);
    expect(res.variance).toBe(12);
  });

  it('normalizes already-percentage scores without doubling', () => {
    const res = normalizeCompetency({
      nos_id: 'ELE/N5802',
      competency_name: 'Earthing & Fault Protection Setup',
      score: 75,
      benchmark: 70,
    });
    expect(res).not.toBeNull();
    expect(res.score).toBe(75);
    expect(res.benchmark).toBe(70);
  });

  it('defaults missing benchmark to NSQF 70% threshold', () => {
    const res = normalizeCompetency({
      nos_id: 'ELE/N5803',
      competency_name: 'Inverter Installation',
      score: 0.65,
    });
    expect(res).not.toBeNull();
    expect(res.score).toBe(65);
    expect(res.benchmark).toBe(70);
    expect(res.isProficient).toBe(false);
    expect(res.variance).toBe(-5);
  });

  it('filters out invalid or missing scores without fabricating data', () => {
    expect(normalizeCompetency(null)).toBeNull();
    expect(normalizeCompetency({ nos_id: 'ELE/N5801' })).toBeNull();
    expect(normalizeCompetency({ nos_id: 'ELE/N5801', score: NaN })).toBeNull();
    expect(normalizeCompetency({ nos_id: 'ELE/N5801', score: 'not-a-number' })).toBeNull();
  });
});

describe('CompetencyMappingChart Component', () => {
  const comp1 = {
    nos_id: 'ELE/N5801',
    competency_name: 'Residential Distribution & Circuit Wiring',
    score: 0.82,
    benchmark: 0.70,
    evidence_count: 1,
  };

  const comp2 = {
    nos_id: 'ELE/N5802',
    competency_name: 'Earthing & Fault Protection Setup',
    score: 0.75,
    benchmark: 0.70,
    evidence_count: 1,
  };

  const comp3 = {
    nos_id: 'ELE/N5803',
    competency_name: 'Inverter & Backup Power Installation',
    score: 0.68,
    benchmark: 0.70,
    evidence_count: 0,
  };

  const comp4 = {
    nos_id: 'ELE/N5804',
    competency_name: 'Industrial Motor Feeder Maintenance',
    score: 0.55,
    benchmark: 0.70,
    evidence_count: 0,
  };

  it('1. Zero Competencies: renders empty state without fabricating scores', () => {
    render(<CompetencyMappingChart competencies={[]} isWorker />);

    expect(screen.getByTestId('competency-chart-empty')).toBeDefined();
    expect(screen.getByText(/no competency evaluations recorded/i)).toBeDefined();
    expect(screen.getByText(/0 standards mapped/i)).toBeDefined();
    expect(screen.getByText(/strict data integrity/i)).toBeDefined();

    // Ensures neither chart is rendered
    expect(screen.queryByTestId('competency-radar-chart')).toBeNull();
    expect(screen.queryByTestId('competency-grouped-bar-chart')).toBeNull();
  });

  it('2. One Competency: renders horizontal grouped bar chart, NOT radar chart', () => {
    render(<CompetencyMappingChart competencies={[comp1]} isWorker />);

    expect(screen.getByTestId('competency-mapping-chart')).toBeDefined();
    expect(screen.getByTestId('competency-grouped-bar-chart')).toBeDefined();
    expect(screen.queryByTestId('competency-radar-chart')).toBeNull();

    // Verifies badge and copy
    expect(screen.getByText(/1 Standard · Grouped Bar View/i)).toBeDefined();
    expect(screen.getByText(/COMPETENCY TWIN BENCHMARK COMPARISON/i)).toBeDefined();

    // Verifies full unclipped label
    expect(screen.getByText('Residential Distribution & Circuit Wiring')).toBeDefined();
    expect(screen.getAllByText('ELE/N5801').length).toBeGreaterThanOrEqual(2);

    // Verifies scores and advisory notice
    expect(screen.getByText('82%')).toBeDefined();
    expect(screen.getAllByText('70%').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/advisory rpl alignment notice/i)).toBeDefined();
  });

  it('3. Two Competencies: renders horizontal grouped bar chart to prevent radar line distortion', () => {
    render(<CompetencyMappingChart competencies={[comp1, comp2]} isWorker />);

    expect(screen.getByTestId('competency-mapping-chart')).toBeDefined();
    // Must render horizontal grouped bar chart
    expect(screen.getByTestId('competency-grouped-bar-chart')).toBeDefined();
    // Must NOT render radar chart (fixing the single vertical line defect!)
    expect(screen.queryByTestId('competency-radar-chart')).toBeNull();

    // Verifies 2 standards badge
    expect(screen.getByText(/2 Standards · Grouped Bar View/i)).toBeDefined();

    // Both full labels are present and unclipped
    expect(screen.getByText('Residential Distribution & Circuit Wiring')).toBeDefined();
    expect(screen.getByText('Earthing & Fault Protection Setup')).toBeDefined();
    expect(screen.getAllByText('ELE/N5801').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('ELE/N5802').length).toBeGreaterThanOrEqual(2);

    // Both scores and benchmarks are present
    expect(screen.getByText('82%')).toBeDefined();
    expect(screen.getAllByText('75%').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('70%').length).toBeGreaterThanOrEqual(2);

    // Advisory and legend elements
    expect(screen.getByText(/CANDIDATE \(ADVISORY\)/i)).toBeDefined();
    expect(screen.getByText(/BENCHMARK \(NSQF\)/i)).toBeDefined();
    expect(screen.getByText(/Advisory RPL Alignment Notice/i)).toBeDefined();
  });

  it('4. Three or More Competencies: renders radar chart by default and allows toggling to bar view', () => {
    render(<CompetencyMappingChart competencies={[comp1, comp2, comp3, comp4]} isWorker />);

    expect(screen.getByTestId('competency-mapping-chart')).toBeDefined();
    // Must render radar chart by default when >= 3 dimensions
    expect(screen.getByTestId('competency-radar-chart')).toBeDefined();
    expect(screen.queryByTestId('competency-grouped-bar-chart')).toBeNull();

    // Verifies 4 standards badge and title
    expect(screen.getByText(/4 Standards · Radar View/i)).toBeDefined();
    expect(screen.getByText(/COMPETENCY TWIN RADAR MAPPING/i)).toBeDefined();

    // View toggle is available
    expect(screen.getByTestId('chart-view-toggle')).toBeDefined();
    const barViewBtn = screen.getByRole('button', { name: /switch to horizontal bar view/i });
    expect(barViewBtn).toBeDefined();

    // Click toggle to switch to horizontal bar view
    fireEvent.click(barViewBtn);
    expect(screen.getByTestId('competency-grouped-bar-chart')).toBeDefined();
    expect(screen.queryByTestId('competency-radar-chart')).toBeNull();

    // Click toggle back to radar
    const radarViewBtn = screen.getByRole('button', { name: /switch to radar view/i });
    fireEvent.click(radarViewBtn);
    expect(screen.getByTestId('competency-radar-chart')).toBeDefined();
  });

  it('5. Loading State: renders skeleton loader', () => {
    render(<CompetencyMappingChart isLoading={true} />);
    expect(screen.getByTestId('competency-chart-loading')).toBeDefined();
    expect(screen.getByText(/loading competency twin dimensions/i)).toBeDefined();
  });

  it('6. Error State: renders error alert with message', () => {
    render(
      <CompetencyMappingChart
        isError={true}
        errorMessage="Network timeout connecting to evaluation engine."
      />
    );
    expect(screen.getByTestId('competency-chart-error')).toBeDefined();
    expect(screen.getByText(/unable to load competency twin/i)).toBeDefined();
    expect(screen.getByText(/network timeout connecting to evaluation engine/i)).toBeDefined();
  });

  it('7. Handles missing values gracefully without crashing or fabricating fake records', () => {
    // Array with some invalid items
    const dirtyData = [
      comp1,
      null,
      { nos_id: 'INVALID/01', score: null },
      { name: 'Missing Score Element' },
      comp2,
    ];

    render(<CompetencyMappingChart competencies={dirtyData} />);

    // Should only count the 2 valid dimensions (comp1 and comp2)
    expect(screen.getByTestId('competency-grouped-bar-chart')).toBeDefined();
    expect(screen.getByText(/2 Standards · Grouped Bar View/i)).toBeDefined();
    expect(screen.getAllByText('ELE/N5801').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('ELE/N5802').length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText('INVALID/01')).toBeNull();
  });

  it('8. Y-Axis Two-Line Labels: renders full competency names and secondary NOS codes on ticks', () => {
    render(<CompetencyMappingChart competencies={[comp1, comp2]} isWorker />);

    const tick1 = screen.getByTestId('y-axis-tick-ELE/N5801');
    const tick2 = screen.getByTestId('y-axis-tick-ELE/N5802');

    expect(tick1).toBeDefined();
    expect(tick2).toBeDefined();

    // Verify title wrapping inside tick 1
    expect(tick1.textContent).toContain('Residential Distribution');
    expect(tick1.textContent).toContain('& Circuit Wiring');
    expect(tick1.textContent).toContain('ELE/N5801');

    // Verify title wrapping inside tick 2
    expect(tick2.textContent).toContain('Earthing & Fault');
    expect(tick2.textContent).toContain('Protection Setup');
    expect(tick2.textContent).toContain('ELE/N5802');

    // Accessible aria-label and title check
    expect(tick1.getAttribute('aria-label')).toBe(
      'Residential Distribution & Circuit Wiring (ELE/N5801)'
    );
    expect(tick2.getAttribute('aria-label')).toBe(
      'Earthing & Fault Protection Setup (ELE/N5802)'
    );
  });

  it('9. Renders dynamically supplied competency titles and NOS codes without hardcoding', () => {
    const dynamicCompetencies = [
      {
        nos_id: 'PLM/N1001',
        competency_name: 'PPR Pipe Fusion & Pressure Testing',
        score: 0.88,
        benchmark: 0.70,
      },
      {
        nos_id: 'PLM/N1002',
        competency_name: 'Drainage Fixture & Vent Trap Installation',
        score: 0.72,
        benchmark: 0.70,
      },
    ];

    render(<CompetencyMappingChart competencies={dynamicCompetencies} isWorker />);

    const plumbingTick1 = screen.getByTestId('y-axis-tick-PLM/N1001');
    const plumbingTick2 = screen.getByTestId('y-axis-tick-PLM/N1002');

    expect(plumbingTick1).toBeDefined();
    expect(plumbingTick2).toBeDefined();

    expect(plumbingTick1.textContent).toContain('PPR Pipe Fusion');
    expect(plumbingTick1.textContent).toContain('PLM/N1001');

    expect(plumbingTick2.textContent).toContain('Drainage Fixture & Vent');
    expect(plumbingTick2.textContent).toContain('PLM/N1002');
  });

  it('10. Handles missing competency title or code gracefully without duplication', () => {
    const missingTitleComp = [
      {
        nos_id: 'AUTO/N101',
        // No competency_name or name
        score: 0.65,
        benchmark: 0.70,
      },
    ];

    render(<CompetencyMappingChart competencies={missingTitleComp} isWorker />);

    const tick = screen.getByTestId('y-axis-tick-AUTO/N101');
    expect(tick).toBeDefined();
    expect(tick.textContent).toContain('AUTO/N101');

    // Should not crash or produce awkward duplicate lines
    expect(screen.getByTestId('competency-grouped-bar-chart')).toBeDefined();
  });
});
