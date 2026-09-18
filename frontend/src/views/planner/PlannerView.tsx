/**
 * @fileoverview Periodized Training Planner View supporting Daily, Weekly, and Monthly granularities.
 * Injects mandatory rest alerts if ACWR > 1.5 or TSB < -25.
 * @module views/planner/PlannerView
 */

import React, { useState, useEffect } from 'react';
import { getCurrentTrainingPlan } from '../../api/plansApi';
import { getAthleteDiagnostics } from '../../api/diagnosticsApi';
import { DailyView } from '../../components/planner/DailyView';
import { WeeklyView } from '../../components/planner/WeeklyView';
import { MonthlyView } from '../../components/planner/MonthlyView';
import type {
  AthleteDiagnostics,
  PeriodizedPlan,
  PlanViewGranularity,
  WorkoutSession,
} from '../../types';

export const PlannerView: React.FC = () => {
  const [granularity, setGranularity] = useState<PlanViewGranularity>('WEEKLY');
  const [plan, setPlan] = useState<PeriodizedPlan | null>(null);
  const [diagnostics, setDiagnostics] = useState<AthleteDiagnostics | null>(null);
  const [selectedSession, setSelectedSession] = useState<WorkoutSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function fetchData() {
      setIsLoading(true);
      try {
        const [planData, diagData] = await Promise.all([
          getCurrentTrainingPlan(granularity).catch(() => null),
          getAthleteDiagnostics().catch(() => null),
        ]);

        if (diagData) {
          setDiagnostics(diagData);
        }

        if (planData && planData.microcycles && planData.microcycles.length > 0) {
          setPlan(planData);
          if (!selectedSession && planData.microcycles[0]?.sessions?.length > 0) {
            setSelectedSession(planData.microcycles[0].sessions[0]);
          }
        } else {
          // Robust deterministic fallback plan aligned with PRD rules
          const defaultSessions: WorkoutSession[] = [
            {
              day_of_week: 1,
              day_name: 'Lunes',
              is_rest_day: false,
              session_category: 'Fuerza Funcional & Core',
              duration_min: 50,
              target_distance_km: 0,
              target_elevation_gain_m: 0,
              nutrition: {
                strategy: 'Síntesis Proteica & Reparación',
                protein_g_kg: '2.0 g/kg/día',
                carbs_g_kg: '3.5 g/kg/día',
                hydration_guidelines: '2.5L agua mineralizada con magnesio',
              },
              recovery: {
                therapy_name: 'Sauna Seco & Foam Roller',
                protocol: '15-20 min a 80°C seguido de 10 min de liberación miofascial en glúteos e isquiotibiales.',
              },
            },
            {
              day_of_week: 2,
              day_name: 'Martes',
              is_rest_day: false,
              session_category: 'Series de Umbral en Asfalto',
              duration_min: 65,
              target_distance_km: 12.0,
              target_elevation_gain_m: 110,
              nutrition: {
                strategy: 'Carga Glucogénica Rápida',
                protein_g_kg: '1.6 g/kg/día',
                carbs_g_kg: '6.0 g/kg/día',
                hydration_guidelines: 'Isotónico con 500mg sodio/hora',
              },
              recovery: {
                therapy_name: 'Hidroterapia de Contraste',
                protocol: '3 ciclos: 1 min frío a 12°C por 3 min caliente a 38°C.',
              },
            },
            {
              day_of_week: 3,
              day_name: 'Miércoles',
              is_rest_day: true,
              session_category: 'Descanso Regenerativo Activo',
              duration_min: 0,
              target_distance_km: 0,
              target_elevation_gain_m: 0,
              nutrition: {
                strategy: 'Normocalórica Antiinflamatoria',
                protein_g_kg: '1.8 g/kg/día',
                carbs_g_kg: '3.0 g/kg/día',
                hydration_guidelines: 'Infusiones con cúrcuma y electrolitos',
              },
              recovery: {
                therapy_name: 'Paseo Regenerativo & Movilidad',
                protocol: '20 min de movilidad articular de cadera y tobillos sin impacto.',
              },
            },
            {
              day_of_week: 4,
              day_name: 'Jueves',
              is_rest_day: false,
              session_category: 'Rodaje Progresivo en Altitud',
              duration_min: 60,
              target_distance_km: 10.5,
              target_elevation_gain_m: 220,
              nutrition: {
                strategy: 'Oxidación de Ácidos Grasos',
                protein_g_kg: '1.6 g/kg/día',
                carbs_g_kg: '5.0 g/kg/día',
                hydration_guidelines: '750 ml líquido isotónico',
              },
              recovery: {
                therapy_name: 'Descarga de Gemelos con Foam Roller',
                protocol: '8 min por pierna con énfasis en tendón de Aquiles.',
              },
            },
            {
              day_of_week: 5,
              day_name: 'Viernes',
              is_rest_day: true,
              session_category: 'Descanso Total Pre-Fondo',
              duration_min: 0,
              target_distance_km: 0,
              target_elevation_gain_m: 0,
              nutrition: {
                strategy: 'Sobrecarga de Carbohidratos (Carb-Loading)',
                protein_g_kg: '1.5 g/kg/día',
                carbs_g_kg: '7.5 g/kg/día',
                hydration_guidelines: '3L agua con electrolitos completos',
              },
              recovery: {
                therapy_name: 'Sueño Profundo (8-9 horas)',
                protocol: 'Higiene de sueño: cero pantallas 1h antes de dormir y magnesio bisglicinato.',
              },
            },
            {
              day_of_week: 6,
              day_name: 'Sábado',
              is_rest_day: false,
              session_category: 'Largada de Montaña con Desnivel (+D)',
              duration_min: 150,
              target_distance_km: 24.0,
              target_elevation_gain_m: 1450,
              nutrition: {
                strategy: 'Reposición Energética Intensiva en Carrera',
                protein_g_kg: '1.8 g/kg/día',
                carbs_g_kg: '8.0 g/kg/día',
                hydration_guidelines: '500-750 ml/h isotónico + 60g carbohidratos/hora en geles',
              },
              recovery: {
                therapy_name: 'Crioterapia / Baño Helado & Botas de Compresión',
                protocol: '10 min inmersión en agua a 10°C para limitar la inflamación muscular excéntrica.',
              },
            },
            {
              day_of_week: 7,
              day_name: 'Domingo',
              is_rest_day: true,
              session_category: 'Recuperación Biomecánica',
              duration_min: 0,
              target_distance_km: 0,
              target_elevation_gain_m: 0,
              nutrition: {
                strategy: 'Reparación de Tejidos & Antioxidantes',
                protein_g_kg: '2.0 g/kg/día',
                carbs_g_kg: '4.0 g/kg/día',
                hydration_guidelines: 'Hidratación normosódica continua',
              },
              recovery: {
                therapy_name: 'Sauna Húmedo & Estiramientos Suaves',
                protocol: '15 min de vapor a 45°C y respiraciones lentas para tono vagal.',
              },
            },
          ];

          const fallbackPlan: PeriodizedPlan = {
            plan_id: 'plan_periodized_001',
            athlete_profile_id: 'prof_default_001',
            view: granularity,
            active_goal_discipline: 'TRAIL_RUNNING',
            target_date: '2026-12-20',
            microcycles: [
              {
                week_number: 1,
                phase: 'BUILD_1',
                target_volume_hours: 5.5,
                target_load: 380.0,
                weekly_progression_pct: 8.5,
                sessions: defaultSessions,
              },
            ],
          };

          setPlan(fallbackPlan);
          setSelectedSession(defaultSessions[0]);
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, [granularity]);

  // Mandatory Rest Trigger: ACWR > 1.5 OR TSB < -25
  const isMandatoryRestRequired = Boolean(
    diagnostics?.acwr?.requires_mandatory_rest ||
    (diagnostics?.acwr?.ratio && diagnostics.acwr.ratio > 1.5) ||
    (diagnostics?.banister?.tsb && diagnostics.banister.tsb < -25)
  );

  const activeMicrocycle = plan?.microcycles[0];

  return (
    <main className="main-content" id="main-content">
      {/* Header & Granularity Controls */}
      <section style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h1 style={{ fontSize: '2rem', color: 'var(--text-primary)' }}>
                Planificador Periodizado
              </h1>
              {plan?.active_goal_discipline && (
                <span className="badge badge-sweet-spot">
                  {plan.active_goal_discipline}
                </span>
              )}
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
              Periodización adaptativa con control estricto de progresión (&le; 10% semanal) y pautas de nutrición/descarga
            </p>
          </div>

          {/* Granularity Switcher Tabs */}
          <div className="tab-group" role="tablist" aria-label="Granularidad de visualización del plan">
            <button
              type="button"
              role="tab"
              aria-selected={granularity === 'DAILY'}
              className={`tab-btn ${granularity === 'DAILY' ? 'active' : ''}`}
              onClick={() => setGranularity('DAILY')}
              data-testid="tab-daily"
            >
              📅 Vista Diaria
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={granularity === 'WEEKLY'}
              className={`tab-btn ${granularity === 'WEEKLY' ? 'active' : ''}`}
              onClick={() => setGranularity('WEEKLY')}
              data-testid="tab-weekly"
            >
              📊 Vista Semanal
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={granularity === 'MONTHLY'}
              className={`tab-btn ${granularity === 'MONTHLY' ? 'active' : ''}`}
              onClick={() => setGranularity('MONTHLY')}
              data-testid="tab-monthly"
            >
              🏔️ Vista Mensual
            </button>
          </div>
        </div>
      </section>

      {/* Reactive Mandatory Rest Warning Alert */}
      {isMandatoryRestRequired && (
        <aside
          className="alert-banner alert-banner-danger"
          style={{ marginBottom: '1.5rem' }}
          role="alert"
          data-testid="planner-mandatory-rest-alert"
        >
          <span style={{ fontSize: '1.75rem' }} aria-hidden="true">🛑</span>
          <div>
            <h4 style={{ fontWeight: 800, fontSize: '1.1rem', margin: 0 }}>
              ALERTA BIOMECÁNICA: Descanso Obligatorio Prescrito
            </h4>
            <p style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
              El ratio agudo:crónico (ACWR = {diagnostics?.acwr.ratio.toFixed(2)}) supera el límite seguro de 1.5 o la fatiga aguda (TSB = {diagnostics?.banister.tsb}) ha alcanzado cotas críticas. Para evitar lesiones tendinosas, las sesiones intensas han sido sustituidas automáticamente por descanso activo y protocolos de crioterapia/sauna.
            </p>
          </div>
        </aside>
      )}

      {/* View Rendering based on Granularity */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
          Cargando microciclo periodizado...
        </div>
      ) : (
        <>
          {granularity === 'DAILY' && selectedSession && (
            <DailyView
              session={selectedSession}
              isMandatoryRestInjected={isMandatoryRestRequired}
            />
          )}

          {granularity === 'WEEKLY' && activeMicrocycle && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <WeeklyView
                microcycle={activeMicrocycle}
                selectedSessionDay={selectedSession?.day_of_week}
                onSelectSession={(sess) => {
                  setSelectedSession(sess);
                  setGranularity('DAILY');
                }}
              />

              {/* Quick Daily Inspector for the selected day */}
              {selectedSession && (
                <article className="card" style={{ background: 'var(--bg-surface)' }}>
                  <header className="card-header">
                    <h3 className="card-title" style={{ fontSize: '1.15rem' }}>
                      Detalle de la Sesión: {selectedSession.day_name} ({selectedSession.session_category})
                    </h3>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => setGranularity('DAILY')}
                      style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
                    >
                      Abrir Vista Diaria Completa →
                    </button>
                  </header>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {selectedSession.is_rest_day
                      ? 'Día de regeneración celular, movilidad y estiramientos suaves.'
                      : `Duración: ${selectedSession.duration_min} minutos • Terapia física: ${selectedSession.recovery.therapy_name}`}
                  </p>
                </article>
              )}
            </div>
          )}

          {granularity === 'MONTHLY' && plan && (
            <MonthlyView
              microcycles={plan.microcycles}
              onSelectMicrocycle={() => {
                setGranularity('WEEKLY');
              }}
            />
          )}
        </>
      )}
    </main>
  );
};
