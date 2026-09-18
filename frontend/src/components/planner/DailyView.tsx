/**
 * @fileoverview Daily View component for periodized training session.
 * @module components/planner/DailyView
 */

import React from 'react';
import type { WorkoutSession } from '../../types';

export interface DailyViewProps {
  session: WorkoutSession;
  isMandatoryRestInjected?: boolean;
}

export const DailyView: React.FC<DailyViewProps> = ({
  session,
  isMandatoryRestInjected = false,
}) => {
  const isRest = session.is_rest_day || isMandatoryRestInjected;

  return (
    <div className="daily-view-container" data-testid="daily-view">
      {isMandatoryRestInjected && (
        <aside
          className="alert-banner alert-banner-danger"
          style={{ marginBottom: '1.25rem' }}
          role="alert"
          data-testid="mandatory-rest-banner"
        >
          <span style={{ fontSize: '1.5rem' }} aria-hidden="true">🛑</span>
          <div>
            <h4 style={{ fontWeight: 700, fontSize: '1rem', margin: 0 }}>
              DESCANSO OBLIGATORIO INYECTADO (Gabbett ACWR &gt; 1.5)
            </h4>
            <p style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
              El sistema ha sustituido la sesión habitual por un día de reposo absoluto y regeneración celular para mitigar el riesgo inminente de sobrecarga biomecánica.
            </p>
          </div>
        </aside>
      )}

      {/* Main Session Card */}
      <article className="card" style={{ marginBottom: '1.5rem' }}>
        <header className="card-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h3 className="card-title" style={{ fontSize: '1.4rem' }}>
                {session.day_name}: {isRest ? 'Día de Descanso & Recuperación' : session.session_category}
              </h3>
              {isRest ? (
                <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent-glacier)' }}>
                  Regeneración
                </span>
              ) : (
                <span className="badge badge-sweet-spot">
                  {session.duration_min} min programados
                </span>
              )}
            </div>
            <p className="card-subtitle" style={{ marginTop: '0.25rem' }}>
              {isRest
                ? 'Permite la supercompensación fisiológica y adaptación del tejido miofascial.'
                : `Objetivo: ${session.target_distance_km > 0 ? `${session.target_distance_km} km` : ''} ${
                    session.target_elevation_gain_m > 0 ? `• +${session.target_elevation_gain_m}m D+` : ''
                  }`}
            </p>
          </div>
        </header>

        {/* Workout Structure Breakdown */}
        {!isRest && (
          <section className="workout-breakdown" aria-label="Estructura de la sesión" style={{ marginTop: '1rem' }}>
            <h4 style={{ fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Estructura de la Sesión
            </h4>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div className="card" style={{ background: 'var(--bg-input)', padding: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-glacier)', fontWeight: 700, textTransform: 'uppercase' }}>
                  1. Calentamiento (15 min)
                </span>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                  Movilidad articular de tobillos, zancadas dinámicas y trote en Z1 progresivo.
                </p>
              </div>

              <div className="card" style={{ background: 'var(--bg-input)', padding: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-summit)', fontWeight: 700, textTransform: 'uppercase' }}>
                  2. Bloque Principal ({session.duration_min - 25} min)
                </span>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                  {session.session_category.includes('TRAIL')
                    ? 'Subidas rítmicas manteniendo potencia aeróbica, técnica de bastones y descenso reactivo.'
                    : session.session_category.includes('STRENGTH')
                    ? 'Circuito de fuerza funcional: Sentadilla goblet, desplantes búlgaros y puente de glúteos.'
                    : 'Rodaje controlado en Zona 2 aeróbica con enfoque en economía de zancada.'}
                </p>
              </div>

              <div className="card" style={{ background: 'var(--bg-input)', padding: '1rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: 700, textTransform: 'uppercase' }}>
                  3. Enfriamiento (10 min)
                </span>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                  Trote suave regenerativo en Z1, respiración diafragmática y descompresión lumbar.
                </p>
              </div>
            </div>
          </section>
        )}
      </article>

      {/* Dual Column: Contextual Nutrition & Physical Recovery Protocols */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {/* Nutrition Prescription */}
        <article className="card" aria-labelledby="nutrition-title" data-testid="nutrition-card">
          <header className="card-header">
            <div>
              <h3 id="nutrition-title" className="card-title">
                Pauta de Nutrición Contextual
              </h3>
              <p className="card-subtitle">Estrategia energética pre, intra y post-entrenamiento</p>
            </div>
            <span style={{ fontSize: '1.5rem' }} aria-hidden="true">🥑</span>
          </header>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Estrategia</span>
              <strong style={{ fontSize: '0.85rem', color: 'var(--accent-summit)' }}>
                {session.nutrition.strategy}
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Aporte Proteico</span>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                {session.nutrition.protein_g_kg}
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Aporte de Carbohidratos</span>
              <strong style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                {session.nutrition.carbs_g_kg}
              </strong>
            </div>

            <div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Hidratación & Electrolitos:</span>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                {session.nutrition.hydration_guidelines}
              </p>
            </div>
          </div>
        </article>

        {/* Physical Recovery Therapy */}
        <article className="card" aria-labelledby="recovery-title" data-testid="recovery-card">
          <header className="card-header">
            <div>
              <h3 id="recovery-title" className="card-title">
                Protocolo de Descarga Física
              </h3>
              <p className="card-subtitle">Regeneración celular y alivio miofascial</p>
            </div>
            <span style={{ fontSize: '1.5rem' }} aria-hidden="true">🧊</span>
          </header>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Terapia Prescrita</span>
              <strong style={{ fontSize: '0.85rem', color: 'var(--accent-glacier)' }}>
                {session.recovery.therapy_name}
              </strong>
            </div>

            <div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Protocolo Clínico / Deporte:</span>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.6 }}>
                {session.recovery.protocol}
              </p>
            </div>

            <div
              style={{
                background: 'var(--bg-input)',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                marginTop: '0.25rem',
              }}
            >
              <span style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                💡 Consejo del Fisioterapeuta:
              </span>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Combina la terapia con 8 horas de sueño profundo para optimizar la síntesis de hormona de crecimiento.
              </p>
            </div>
          </div>
        </article>
      </div>
    </div>
  );
};
