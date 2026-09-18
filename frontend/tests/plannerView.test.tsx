/**
 * @fileoverview Unit tests for PlannerView component: Daily/Weekly/Monthly granularities and mandatory rest injection.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PlannerView } from '../src/views/planner/PlannerView';
import * as diagnosticsApi from '../src/api/diagnosticsApi';

describe('PlannerView Component (US-06 / FR-04 Periodized Planner)', () => {
  it('renders weekly view by default with microcycle totals and 7-day grid', async () => {
    render(<PlannerView />);

    await waitFor(() => {
      expect(screen.getByTestId('weekly-view')).toBeInTheDocument();
    });

    expect(screen.getByText(/Microciclo Semana #1/i)).toBeInTheDocument();
    expect(screen.getByText(/Volumen Semanal/i)).toBeInTheDocument();
  });

  it('switches between Daily, Weekly, and Monthly tabs smoothly', async () => {
    render(<PlannerView />);

    await waitFor(() => {
      expect(screen.getByTestId('weekly-view')).toBeInTheDocument();
    });

    // Switch to Daily view
    const dailyTab = screen.getByTestId('tab-daily');
    fireEvent.click(dailyTab);

    await waitFor(() => {
      expect(screen.getByTestId('daily-view')).toBeInTheDocument();
    });
    expect(screen.getByTestId('nutrition-card')).toBeInTheDocument();
    expect(screen.getByTestId('recovery-card')).toBeInTheDocument();

    // Switch to Monthly view
    const monthlyTab = screen.getByTestId('tab-monthly');
    fireEvent.click(monthlyTab);

    await waitFor(() => {
      expect(screen.getByTestId('monthly-view')).toBeInTheDocument();
    });
    expect(screen.getByText(/Mesociclo Periodizado/i)).toBeInTheDocument();
  });

  it('injects reactive mandatory rest banner when ACWR > 1.5 or TSB is critical', async () => {
    vi.spyOn(diagnosticsApi, 'getAthleteDiagnostics').mockResolvedValue({
      athlete_profile_id: 'prof_test_danger',
      banister: { ctl: 60.0, atl: 88.0, tsb: -28.0, is_critical_fatigue: true },
      acwr: {
        ratio: 1.62,
        zone: 'DANGER',
        requires_mandatory_rest: true,
        freeze_weekly_increments: true,
        recommendation: 'Peligro biomecánico crítico.',
      },
      weekly_total_load: 620.0,
      weekly_duration_minutes: 510.0,
      days_evaluated: 42,
    });

    render(<PlannerView />);

    await waitFor(() => {
      expect(screen.getByTestId('planner-mandatory-rest-alert')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/ALERTA BIOMECÁNICA: Descanso Obligatorio Prescrito/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/supera el límite seguro de 1.5/i)).toBeInTheDocument();
  });
});
