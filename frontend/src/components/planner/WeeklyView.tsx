/**
 * @fileoverview Weekly View component showing 7-day microcycle with volume totals and progression rules.
 * @module components/planner/WeeklyView
 */

import React from 'react';
import type { Microcycle, WorkoutSession } from '../../types';

export interface WeeklyViewProps {
  microcycle: Microcycle;
  onSelectSession?: (session: WorkoutSession) => void;
  selectedSessionDay?: number;
}

export const WeeklyView: React.FC<WeeklyViewProps> = ({
  microcycle,
  onSelectSession,
  selectedSessionDay,
}) => {
  const isSafeProgression = microcycle.weekly_progression_pct <= 10.0;

  return (
    <section className="weekly-view" aria-labelledby="weekly-heading" data-testid="weekly-view">
      {/* Microcycle Header & Totals */}
      <div
        className="card"
        style={{
          marginBottom: '1.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <h3 id="weekly-heading" className="card-title">
              Microciclo Semana #{microcycle.week_number}
            </h3>
            <span
              className="badge"
              style={{
                background:
                  microcycle.phase === 'RECOVERY'
                    ? 'rgba(56, 189, 248, 0.15)'
                    : 'rgba(255, 107, 53, 0.15)',
                color:
                  microcycle.phase === 'RECOVERY'
                    ? 'var(--accent-glacier)'
                    : 'var(--accent-summit)',
              }}
            >
              Fase: {microcycle.phase}
            </span>
          </div>
          <p className="card-subtitle" style={{ marginTop: '0.2rem' }}>
            Distribución periodizada de sesiones de carga, fuerza y descanso programado
          </p>
        </div>

        {/* Totals Summary */}
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Volumen Semanal
            </span>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {microcycle.target_volume_hours} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>horas</span>
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Carga / TSS
            </span>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-summit)' }}>
              {microcycle.target_load} <span style={{ fontSize: '0.8rem', fontWeight: 400 }}>TSS</span>
            </div>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Progresión
            </span>
            <div
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.3rem',
                fontWeight: 700,
                color: isSafeProgression ? 'var(--acwr-sweet-spot)' : 'var(--acwr-danger)',
              }}
              title="Regla de oro: Incrementos semanales no deben exceder el 10%"
            >
              +{microcycle.weekly_progression_pct}%
            </div>
          </div>
        </div>
      </div>

      {/* 7-day Microcycle Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '0.85rem',
        }}
      >
        {microcycle.sessions.map((sess) => {
          const isSelected = selectedSessionDay === sess.day_of_week;
          const isRest = sess.is_rest_day;

          return (
            <article
              key={sess.day_of_week}
              className={`card ${isSelected ? 'selected' : ''}`}
              onClick={() => onSelectSession?.(sess)}
              style={{
                padding: '1rem 0.85rem',
                cursor: 'pointer',
                border: isSelected
                  ? '2px solid var(--accent-summit)'
                  : isRest
                  ? '1px dashed var(--border-subtle)'
                  : '1px solid var(--border-subtle)',
                background: isSelected
                  ? 'rgba(255, 107, 53, 0.08)'
                  : isRest
                  ? 'rgba(16, 23, 32, 0.5)'
                  : 'var(--bg-surface)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minHeight: '170px',
                transition: 'all var(--transition-fast)',
              }}
              role="button"
              tabIndex={0}
              aria-label={`Día ${sess.day_name}: ${sess.session_category}`}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectSession?.(sess);
                }
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    {sess.day_name}
                  </span>
                  {isRest ? (
                    <span style={{ fontSize: '0.9rem' }} aria-hidden="true">🛌</span>
                  ) : sess.session_category.includes('STRENGTH') ? (
                    <span style={{ fontSize: '0.9rem' }} aria-hidden="true">🏋️</span>
                  ) : sess.session_category.includes('TRAIL') ? (
                    <span style={{ fontSize: '0.9rem' }} aria-hidden="true">⛰️</span>
                  ) : (
                    <span style={{ fontSize: '0.9rem' }} aria-hidden="true">🏃</span>
                  )}
                </div>

                <h4
                  style={{
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    color: isRest ? 'var(--text-muted)' : 'var(--text-primary)',
                    marginTop: '0.5rem',
                    lineHeight: 1.2,
                  }}
                >
                  {isRest ? 'Descanso' : sess.session_category}
                </h4>
              </div>

              <div style={{ marginTop: '0.75rem' }}>
                {!isRest ? (
                  <>
                    <div style={{ fontSize: '0.8rem', color: 'var(--accent-glacier)', fontWeight: 600 }}>
                      {sess.duration_min} min
                    </div>
                    {sess.target_distance_km > 0 && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {sess.target_distance_km} km
                        {sess.target_elevation_gain_m > 0 ? ` (+${sess.target_elevation_gain_m}m)` : ''}
                      </div>
                    )}
                  </>
                ) : (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Recuperación activa
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};
