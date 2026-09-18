/**
 * @fileoverview Unit tests for ACWRGauge component across all 3 Gabbett risk zones.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ACWRGauge } from '../src/components/charts/ACWRGauge';
import type { ACWRMetrics } from '../src/types';

describe('ACWRGauge Component (Gabbett Risk Semaphor)', () => {
  it('renders correctly in Sweet Spot (0.8 <= ACWR <= 1.3) with green styling', () => {
    const sweetSpotMetrics: ACWRMetrics = {
      ratio: 1.05,
      zone: 'SWEET_SPOT',
      requires_mandatory_rest: false,
      freeze_weekly_increments: false,
      recommendation: 'Adaptación aeróbica óptima. Progresión segura dentro del rango.',
    };

    render(<ACWRGauge metrics={sweetSpotMetrics} />);

    // Check numerical display
    expect(screen.getByTestId('acwr-ratio-number')).toHaveTextContent('1.05');

    // Check zone badge
    const badge = screen.getByTestId('acwr-zone-badge');
    expect(badge).toHaveTextContent('Sweet Spot (0.8 - 1.3)');
    expect(badge).toHaveClass('badge-sweet-spot');

    // Check headline
    const headline = screen.getByTestId('acwr-headline');
    expect(headline).toHaveTextContent('FRESCURA ÓPTIMA: Preparado para asimilar alta intensidad');

    // Check recommendation
    expect(screen.getByTestId('acwr-recommendation')).toHaveTextContent(
      'Adaptación aeróbica óptima. Progresión segura dentro del rango.'
    );
  });

  it('renders correctly in Caution Zone (1.3 < ACWR <= 1.5) with warning amber styling', () => {
    const cautionMetrics: ACWRMetrics = {
      ratio: 1.42,
      zone: 'WARNING',
      requires_mandatory_rest: false,
      freeze_weekly_increments: true,
      recommendation: 'Alerta de sobrecarga. Se congelan los incrementos de volumen para la próxima semana.',
    };

    render(<ACWRGauge metrics={cautionMetrics} />);

    expect(screen.getByTestId('acwr-ratio-number')).toHaveTextContent('1.42');

    const badge = screen.getByTestId('acwr-zone-badge');
    expect(badge).toHaveTextContent('Zona de Precaución (1.3 - 1.5)');
    expect(badge).toHaveClass('badge-warning');

    const headline = screen.getByTestId('acwr-headline');
    expect(headline).toHaveTextContent('ZONA DE PRECAUCIÓN: Incrementos de volumen congelados');
  });

  it('renders correctly in Critical Danger Zone (ACWR > 1.5) with danger red styling and mandatory rest', () => {
    const dangerMetrics: ACWRMetrics = {
      ratio: 1.65,
      zone: 'DANGER',
      requires_mandatory_rest: true,
      freeze_weekly_increments: true,
      recommendation: 'Peligro biomecánico crítico. Descanso obligatorio prescrito inmediatamente.',
    };

    render(<ACWRGauge metrics={dangerMetrics} />);

    expect(screen.getByTestId('acwr-ratio-number')).toHaveTextContent('1.65');

    const badge = screen.getByTestId('acwr-zone-badge');
    expect(badge).toHaveTextContent('Zona Crítica (> 1.5)');
    expect(badge).toHaveClass('badge-danger');

    const headline = screen.getByTestId('acwr-headline');
    expect(headline).toHaveTextContent('PELIGRO BIOMECÁNICO: Descanso obligatorio prescrito');
  });
});
