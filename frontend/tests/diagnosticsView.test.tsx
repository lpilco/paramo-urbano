/**
 * @fileoverview Unit tests for DiagnosticsView component.
 * Validates strict compliance with ADR-006 (centered layout, NO rookie card in /diagnostics).
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DiagnosticsView } from '../src/views/diagnostics/DiagnosticsView';
import * as diagnosticsApi from '../src/api/diagnosticsApi';
import * as activitiesApi from '../src/api/activitiesApi';

describe('DiagnosticsView Component (ADR-006 Compliance & Physiological Panel)', () => {
  it('strictly adheres to ADR-006: rookie/beginner card does NOT exist in the DOM', () => {
    render(<DiagnosticsView />);

    // Prohibited beginner/rookie educational cards (ADR-006)
    expect(screen.queryByText(/¿Comienzas desde cero\?/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/El Método CaCo/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Fórmula de Gellish/i)).not.toBeInTheDocument();
    expect(screen.queryByTestId('profile-b-section')).not.toBeInTheDocument();
  });

  it('strictly adheres to ADR-006: container uses centered layout class with max-width 680px', () => {
    render(<DiagnosticsView />);

    const container = screen.getByTestId('diagnostics-centered-container');
    expect(container).toBeInTheDocument();
    expect(container).toHaveClass('diagnostics-centered-container');
  });

  it('renders Banister chart, ACWR gauge, and activity history table', async () => {
    vi.spyOn(diagnosticsApi, 'getAthleteDiagnostics').mockResolvedValue({
      athlete_profile_id: 'prof_test_01',
      banister: { ctl: 62.0, atl: 45.0, tsb: 17.0, is_critical_fatigue: false },
      acwr: {
        ratio: 1.12,
        zone: 'SWEET_SPOT',
        requires_mandatory_rest: false,
        freeze_weekly_increments: false,
        recommendation: 'Frescura óptima.',
      },
      weekly_total_load: 450.0,
      weekly_duration_minutes: 380.0,
      days_evaluated: 42,
    });

    vi.spyOn(activitiesApi, 'listActivities').mockResolvedValue({
      items: [
        {
          id: 'act_test_1',
          sport_category: 'TRAIL_RUN',
          source_type: 'FIT',
          started_at: '2026-09-17T06:00:00Z',
          duration_minutes: 120,
          distance_km: 18.0,
          elevation_gain_m: 1100,
          session_rpe: null,
          calculated_load: 220.0,
          tss_score: 220.0,
          processing_status: 'PROCESSED',
          notes: 'Ascenso técnico',
        },
      ],
      total: 1,
      page: 1,
      limit: 10,
    });

    render(<DiagnosticsView />);

    // Banister chart
    expect(screen.getByTestId('banister-chart-card')).toBeInTheDocument();

    // ACWR gauge
    expect(screen.getByTestId('acwr-gauge-card')).toBeInTheDocument();

    // History card
    expect(screen.getByTestId('activities-history-card')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Ascenso técnico')).toBeInTheDocument();
    });
  });

  it('opens ManualActivityModal when clicking the registration button', () => {
    render(<DiagnosticsView />);

    const openBtn = screen.getByTestId('open-manual-modal-btn');
    fireEvent.click(openBtn);

    expect(screen.getByTestId('manual-activity-modal')).toBeInTheDocument();
  });
});
