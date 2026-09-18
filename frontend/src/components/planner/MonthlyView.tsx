/**
 * @fileoverview Monthly View component structuring the mesocycle in Base, Build, Peak, and Tapering phases.
 * @module components/planner/MonthlyView
 */

import React from 'react';
import type { Microcycle } from '../../types';

export interface MonthlyViewProps {
  microcycles: Microcycle[];
  onSelectMicrocycle?: (microcycle: Microcycle) => void;
}

export const MonthlyView: React.FC<MonthlyViewProps> = ({
  microcycles,
  onSelectMicrocycle,
}) => {
  // If only 1 microcycle is returned, create a 4-week mesocycle visualization
  const weeks = microcycles.length >= 4 ? microcycles : [
    microcycles[0] || {
      week_number: 1,
      phase: 'BASE',
      target_volume_hours: 6.0,
      target_load: 350.0,
      weekly_progression_pct: 0.0,
      sessions: [],
    },
    {
      week_number: 2,
      phase: 'BUILD_1',
      target_volume_hours: 6.6,
      target_load: 385.0,
      weekly_progression_pct: 10.0,
      sessions: [],
    },
    {
      week_number: 3,
      phase: 'BUILD_2',
      target_volume_hours: 7.2,
      target_load: 420.0,
      weekly_progression_pct: 9.1,
      sessions: [],
    },
    {
      week_number: 4,
      phase: 'RECOVERY',
      target_volume_hours: 4.5,
      target_load: 260.0,
      weekly_progression_pct: -37.5,
      sessions: [],
    },
  ];

  return (
    <section className="monthly-view" aria-labelledby="monthly-heading" data-testid="monthly-view">
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <header className="card-header">
          <div>
            <h3 id="monthly-heading" className="card-title">
              Mesociclo Periodizado (Estructura de Fases & Descarga)
            </h3>
            <p className="card-subtitle">
              Sobrecarga progresiva determinista (&le; 10%) con semanas de descarga estructurada (-30% a -40%)
            </p>
          </div>
        </header>

        {/* 4-Week Mesocycle Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
          {weeks.map((week) => {
            const isDeload = week.phase.includes('RECOVERY') || week.weekly_progression_pct < 0;

            return (
              <article
                key={week.week_number}
                className="card"
                onClick={() => onSelectMicrocycle?.(week)}
                style={{
                  background: isDeload ? 'rgba(16, 185, 129, 0.08)' : 'var(--bg-input)',
                  border: isDeload ? '1px solid rgba(16, 185, 129, 0.35)' : '1px solid var(--border-strong)',
                  padding: '1.25rem',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                    SEMANA #{week.week_number}
                  </span>
                  <span
                    className="badge"
                    style={{
                      background: isDeload ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 107, 53, 0.15)',
                      color: isDeload ? 'var(--accent-emerald)' : 'var(--accent-summit)',
                    }}
                  >
                    {week.phase}
                  </span>
                </div>

                <div style={{ marginTop: '1rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Volumen: <strong style={{ color: 'var(--text-primary)' }}>{week.target_volume_hours} h</strong>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                    Carga prevista: <strong style={{ color: 'var(--accent-summit)' }}>{week.target_load} TSS</strong>
                  </div>
                  <div
                    style={{
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      marginTop: '0.4rem',
                      color: isDeload ? 'var(--accent-emerald)' : 'var(--accent-glacier)',
                    }}
                  >
                    Variación: {week.weekly_progression_pct > 0 ? `+${week.weekly_progression_pct}%` : `${week.weekly_progression_pct}%`}
                  </div>
                </div>

                {isDeload && (
                  <div
                    style={{
                      marginTop: '0.85rem',
                      padding: '0.4rem 0.6rem',
                      background: 'rgba(16, 185, 129, 0.12)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.75rem',
                      color: 'var(--accent-emerald)',
                    }}
                  >
                    ✓ Semana de regeneración celular (-30% a -40% de volumen)
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </div>

      {/* Tapering Guide */}
      <article className="card" style={{ background: 'var(--bg-card)' }}>
        <header className="card-header">
          <div>
            <h4 className="card-title" style={{ fontSize: '1.1rem' }}>
              Puesta a Punto (Fase de Tapering Previo a Cumbre)
            </h4>
            <p className="card-subtitle">
              Estrategia determinista para alcanzar TSB positivo (+5 a +15) en el evento
            </p>
          </div>
          <span style={{ fontSize: '1.5rem' }} aria-hidden="true">🎯</span>
        </header>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          Durante los 10 a 14 días previos a la fecha objetivo, el sistema aplica una reducción no lineal del volumen total del 40-60%, conservando la intensidad neuromuscular de carrera. Esto permite disipar rápidamente la fatiga acumulada ($ATL$) manteniendo el fitness crónico ($CTL$), transformando el $TSB$ en un valor positivo para un rendimiento pico el día de competencia.
        </p>
      </article>
    </section>
  );
};
