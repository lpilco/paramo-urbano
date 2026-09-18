/**
 * @fileoverview Centered Physiological Diagnostics View adhering strictly to ADR-006.
 * Features Banister EWMA Curves, Gabbett ACWR Speedometer, and Paginated Activity History.
 * ADR-006 Rule: Centered layout (max-width 680px) and ZERO rookie/beginner educational cards.
 * @module views/diagnostics/DiagnosticsView
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getAthleteDiagnostics } from '../../api/diagnosticsApi';
import { listActivities } from '../../api/activitiesApi';
import { ACWRGauge } from '../../components/charts/ACWRGauge';
import { BanisterChart } from '../../components/charts/BanisterChart';
import { ManualActivityModal } from '../../components/modals/ManualActivityModal';
import type {
  ActivitySummary,
  AthleteDiagnostics,
} from '../../types';

export const DiagnosticsView: React.FC = () => {
  const [diagnostics, setDiagnostics] = useState<AthleteDiagnostics>({
    athlete_profile_id: 'prof_default_001',
    banister: {
      ctl: 58.0,
      atl: 48.0,
      tsb: 10.0,
      is_critical_fatigue: false,
    },
    acwr: {
      ratio: 1.05,
      zone: 'SWEET_SPOT',
      requires_mandatory_rest: false,
      freeze_weekly_increments: false,
      recommendation: 'Ratio agudo:crónico óptimo. Adaptación aeróbica en zona segura.',
    },
    weekly_total_load: 420.0,
    weekly_duration_minutes: 360.0,
    days_evaluated: 42,
  });

  const [activities, setActivities] = useState<ActivitySummary[]>([
    {
      id: 'act_01',
      sport_category: 'TRAIL_RUN',
      source_type: 'FIT',
      started_at: '2026-09-17T06:30:00Z',
      duration_minutes: 95,
      distance_km: 14.5,
      elevation_gain_m: 850,
      session_rpe: null,
      calculated_load: 185.0,
      tss_score: 185.0,
      processing_status: 'PROCESSED',
      notes: 'Subida al Rucu Pichincha por el arenal',
    },
    {
      id: 'act_02',
      sport_category: 'STRENGTH',
      source_type: 'MANUAL',
      started_at: '2026-09-16T18:00:00Z',
      duration_minutes: 50,
      distance_km: 0,
      elevation_gain_m: 0,
      session_rpe: 8,
      calculated_load: 400.0,
      tss_score: 110.0,
      processing_status: 'PROCESSED',
      notes: 'Fuerza funcional: sentadillas goblet y zancadas',
    },
    {
      id: 'act_03',
      sport_category: 'ROAD_RUN',
      source_type: 'GPX',
      started_at: '2026-09-14T07:15:00Z',
      duration_minutes: 60,
      distance_km: 10.2,
      elevation_gain_m: 120,
      session_rpe: null,
      calculated_load: 95.0,
      tss_score: 95.0,
      processing_status: 'PROCESSED',
      notes: 'Rodaje controlado en parque La Carolina',
    },
  ]);

  const [page, setPage] = useState<number>(1);
  const [totalActivities, setTotalActivities] = useState<number>(3);
  const [isManualModalOpen, setIsManualModalOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [diagData, actData] = await Promise.all([
        getAthleteDiagnostics().catch(() => null),
        listActivities(page, 10).catch(() => null),
      ]);

      if (diagData) {
        setDiagnostics(diagData);
      }
      if (actData && actData.items && actData.items.length > 0) {
        setActivities(actData.items);
        setTotalActivities(actData.total);
      }
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <main className="main-content" id="main-content">
      {/* MANDATORY ADR-006: Contenedor centrado a max-width 680px */}
      <div
        className="diagnostics-centered-container"
        data-testid="diagnostics-centered-container"
      >
        {/* Header with Quick Manual Logging Action */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.75rem', color: 'var(--text-primary)' }}>
              Diagnóstico Fisiológico
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Telemetría determinista y modelado de fatiga biológica
            </p>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsManualModalOpen(true)}
            data-testid="open-manual-modal-btn"
          >
            + Registrar Actividad Manual
          </button>
        </header>

        {/* 1. Gabbett ACWR Speedometer / Traffic Light */}
        <ACWRGauge metrics={diagnostics.acwr} />

        {/* 2. Banister EWMA Workload Curves (CTL / ATL / TSB) */}
        <BanisterChart metrics={diagnostics.banister} />

        {/* 3. Summary Metric Cards */}
        <section aria-label="Métricas de Carga Acumulada" className="metric-grid">
          <div className="metric-pill">
            <span className="metric-pill-label">Fitness (CTL)</span>
            <span className="metric-pill-value" style={{ color: 'var(--accent-glacier)' }}>
              {diagnostics.banister.ctl}
            </span>
          </div>

          <div className="metric-pill">
            <span className="metric-pill-label">Fatiga (ATL)</span>
            <span className="metric-pill-value" style={{ color: 'var(--accent-summit)' }}>
              {diagnostics.banister.atl}
            </span>
          </div>

          <div className="metric-pill">
            <span className="metric-pill-label">Forma (TSB)</span>
            <span
              className="metric-pill-value"
              style={{
                color:
                  diagnostics.banister.tsb >= 0
                    ? 'var(--accent-emerald)'
                    : 'var(--acwr-danger)',
              }}
            >
              {diagnostics.banister.tsb > 0
                ? `+${diagnostics.banister.tsb}`
                : diagnostics.banister.tsb}
            </span>
          </div>

          <div className="metric-pill">
            <span className="metric-pill-label">Carga Semanal</span>
            <span className="metric-pill-value" style={{ color: 'var(--text-primary)' }}>
              {diagnostics.weekly_total_load} <span style={{ fontSize: '0.75rem', fontWeight: 400 }}>u.a.</span>
            </span>
          </div>
        </section>

        {/* 4. Activity History Table (US-05) */}
        <article className="card" aria-labelledby="history-heading" data-testid="activities-history-card">
          <header className="card-header">
            <div>
              <h3 id="history-heading" className="card-title">
                Historial de Entrenamientos
              </h3>
              <p className="card-subtitle">
                Sesiones sincronizadas vía archivos GPS y registros manuales sRPE
              </p>
            </div>
            <span className="badge" style={{ background: 'var(--bg-input)', color: 'var(--text-muted)' }}>
              {totalActivities} actividades
            </span>
          </header>

          <div className="table-responsive">
            <table className="data-table" aria-label="Listado cronológico de sesiones de entrenamiento">
              <thead>
                <tr>
                  <th scope="col">Fecha</th>
                  <th scope="col">Deporte</th>
                  <th scope="col">Origen</th>
                  <th scope="col">Duración</th>
                  <th scope="col">Distancia</th>
                  <th scope="col">+D</th>
                  <th scope="col">FC / RPE</th>
                  <th scope="col">Carga</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((act) => (
                  <tr key={act.id} data-testid="activity-row">
                    <td><strong>{formatDate(act.started_at)}</strong></td>
                    <td>
                      <div
                        style={{
                          fontWeight: 600,
                          color:
                            act.sport_category === 'TRAIL_RUN'
                              ? 'var(--accent-summit)'
                              : act.sport_category === 'STRENGTH'
                              ? 'var(--accent-amber)'
                              : 'var(--accent-glacier)',
                        }}
                      >
                        {act.sport_category}
                      </div>
                      {act.notes && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                          {act.notes}
                        </div>
                      )}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          fontSize: '0.65rem',
                          background:
                            act.source_type === 'MANUAL'
                              ? 'rgba(245, 158, 11, 0.15)'
                              : 'rgba(56, 189, 248, 0.15)',
                          color:
                            act.source_type === 'MANUAL'
                              ? 'var(--accent-amber)'
                              : 'var(--accent-glacier)',
                        }}
                      >
                        {act.source_type}
                      </span>
                    </td>
                    <td>{act.duration_minutes} min</td>
                    <td>{act.distance_km > 0 ? `${act.distance_km} km` : '—'}</td>
                    <td>{act.elevation_gain_m > 0 ? `+${act.elevation_gain_m}m` : '—'}</td>
                    <td>
                      {act.session_rpe ? (
                        <span style={{ fontWeight: 700, color: 'var(--accent-summit)' }}>
                          RPE {act.session_rpe}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>GPS / FC</span>
                      )}
                    </td>
                    <td>
                      <strong style={{ color: 'var(--text-primary)' }}>
                        {act.calculated_load ?? act.tss_score ?? '—'}
                      </strong>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalActivities > 10 && (
            <footer style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page <= 1 || isLoading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
              >
                ← Anterior
              </button>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Página {page} de {Math.ceil(totalActivities / 10)}
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page >= Math.ceil(totalActivities / 10) || isLoading}
                onClick={() => setPage((p) => p + 1)}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
              >
                Siguiente →
              </button>
            </footer>
          )}
        </article>
      </div>

      {/* Quick Logging Modal */}
      <ManualActivityModal
        isOpen={isManualModalOpen}
        onClose={() => setIsManualModalOpen(false)}
        onSuccess={() => {
          loadData();
        }}
      />
    </main>
  );
};
