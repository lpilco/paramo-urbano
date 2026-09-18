/**
 * @fileoverview Centered Physiological Diagnostics View adhering strictly to ADR-006.
 * Features Banister EWMA Curves, Gabbett ACWR Speedometer, and Paginated Activity History (20 items/page).
 * ADR-006 Rule: Centered layout (max-width 680px) and ZERO rookie/beginner educational cards.
 * @module views/diagnostics/DiagnosticsView
 */

import React, { useState, useEffect, useCallback } from 'react';
import { getAthleteDiagnostics } from '../../api/diagnosticsApi';
import { listActivities } from '../../api/activitiesApi';
import { ACWRGauge } from '../../components/charts/ACWRGauge';
import { BanisterChart } from '../../components/charts/BanisterChart';
import { ManualActivityModal } from '../../components/modals/ManualActivityModal';
import { DropzoneUpload } from '../../components/upload/DropzoneUpload';
import type {
  ActivitySummary,
  AthleteDiagnostics,
} from '../../types';

export const DiagnosticsView: React.FC = () => {
  const [diagnostics, setDiagnostics] = useState<AthleteDiagnostics>({
    athlete_profile_id: '',
    banister: {
      ctl: 0.0,
      atl: 0.0,
      tsb: 0.0,
      is_critical_fatigue: false,
    },
    acwr: {
      ratio: 0.0,
      zone: 'SWEET_SPOT',
      requires_mandatory_rest: false,
      freeze_weekly_increments: false,
      recommendation: 'Carga actividades o sincroniza archivos GPS para modelar tu fatiga y fitness.',
    },
    weekly_total_load: 0.0,
    weekly_duration_minutes: 0.0,
    days_evaluated: 0,
  });

  const [activities, setActivities] = useState<ActivitySummary[]>([]);
  const [page, setPage] = useState<number>(1);
  const [totalActivities, setTotalActivities] = useState<number>(0);
  const [isManualModalOpen, setIsManualModalOpen] = useState<boolean>(false);
  const [showUploadDropzone, setShowUploadDropzone] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [diagData, actData] = await Promise.all([
        getAthleteDiagnostics().catch(() => null),
        listActivities(page, 20).catch(() => null),
      ]);

      if (diagData) {
        setDiagnostics(diagData);
      }
      if (actData && Array.isArray(actData.items)) {
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

  // Formatters adhering to canonical UX specifications
  const formatDateTime = (isoStr: string): string => {
    try {
      const d = new Date(isoStr);
      const pad = (n: number) => n.toString().padStart(2, '0');
      const year = d.getFullYear();
      const month = pad(d.getMonth() + 1);
      const day = pad(d.getDate());
      const hours = pad(d.getHours());
      const minutes = pad(d.getMinutes());
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    } catch {
      return isoStr;
    }
  };

  const formatSport = (sport: string): string => {
    switch (sport.toUpperCase()) {
      case 'STRENGTH':
        return 'FUERZA';
      case 'TRAIL_RUN':
        return 'TRAIL RUN';
      case 'ROAD_RUN':
        return 'ASFALTO';
      case 'HIKE':
      case 'TREKKING':
        return 'TREKKING';
      default:
        return sport.replace('_', ' ').toUpperCase();
    }
  };

  const formatOrigin = (source: string): string => {
    switch (source.toUpperCase()) {
      case 'MANUAL':
        return 'Manual';
      case 'FIT':
        return 'Archivo FIT';
      case 'GPX':
        return 'Archivo GPX';
      case 'CSV':
        return 'Archivo CSV';
      default:
        return source;
    }
  };

  const formatDuration = (totalMinutes: number): string => {
    if (!totalMinutes || totalMinutes <= 0) return '0 min';
    const hours = Math.floor(totalMinutes / 60);
    const minutes = Math.round(totalMinutes % 60);
    if (hours > 0 && minutes > 0) {
      return `${hours}h ${minutes}m`;
    }
    if (hours > 0) {
      return `${hours}h`;
    }
    return `${minutes} min`;
  };

  const formatDistance = (km?: number): string => {
    if (!km || km <= 0) return '—';
    return `${Number(km).toFixed(1)} km`;
  };

  const formatElevation = (m?: number): string => {
    if (!m || m <= 0) return '—';
    return `+${Math.round(m).toLocaleString('es-ES')} m`;
  };

  const formatHeartRateRPE = (avgHr?: number | null, rpe?: number | null): string => {
    const parts: string[] = [];
    if (avgHr && avgHr > 0) {
      parts.push(`${avgHr} bpm`);
    }
    if (rpe && rpe > 0) {
      parts.push(`RPE ${rpe}/10`);
    }
    return parts.length > 0 ? parts.join(' / ') : '—';
  };

  const formatCalculatedLoad = (act: ActivitySummary): string => {
    if (act.source_type === 'MANUAL' || act.session_rpe) {
      const load = act.calculated_load ?? (act.duration_minutes * (act.session_rpe || 1));
      return `${Math.round(load)} u.a. (Foster)`;
    }
    if (act.tss_score !== null && act.tss_score !== undefined) {
      return `${Number(act.tss_score).toFixed(1)} TSS`;
    }
    if (act.calculated_load !== null && act.calculated_load !== undefined) {
      return `${Number(act.calculated_load).toFixed(1)} TSS`;
    }
    return '—';
  };

  return (
    <main className="main-content" id="main-content">
      {/* MANDATORY ADR-006: Contenedor centrado a max-width 680px */}
      <div
        className="diagnostics-centered-container"
        data-testid="diagnostics-centered-container"
      >
        {/* Header with Quick Actions */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h1 style={{ fontSize: '1.75rem', color: 'var(--text-primary)' }}>
              Diagnóstico Fisiológico
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
              Telemetría determinista y modelado de fatiga biológica
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowUploadDropzone((prev) => !prev)}
              data-testid="toggle-upload-btn"
            >
              {showUploadDropzone ? '✕ Ocultar Carga' : '📁 Cargar Archivo'}
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setIsManualModalOpen(true)}
              data-testid="open-manual-modal-btn"
            >
              + Registrar Actividad
            </button>
          </div>
        </header>

        {/* Collapsible Upload Dropzone for Direct FIT/GPX/CSV Telemetry Upload */}
        {showUploadDropzone && (
          <section
            className="card"
            style={{ marginTop: '1rem', border: '1px dashed var(--accent-glacier)' }}
            data-testid="diagnostics-upload-section"
          >
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              Carga de Telemetría (.FIT, .GPX, .CSV)
            </h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Los archivos binarios .FIT son procesados segundo a segundo a 1 Hz. Los .CSV canónicos se integran de inmediato.
            </p>
            <DropzoneUpload
              onUploadSuccess={() => {
                loadData();
              }}
            />
          </section>
        )}

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

        {/* 4. Activity History Table (Canonical 8 Columns) */}
        <article className="card" aria-labelledby="history-heading" data-testid="activities-history-card">
          <header className="card-header">
            <div>
              <h3 id="history-heading" className="card-title">
                Historial de Entrenamientos Cargados
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
                  <th scope="col">Fecha y Hora</th>
                  <th scope="col">Deporte</th>
                  <th scope="col">Origen</th>
                  <th scope="col">Duración</th>
                  <th scope="col">Distancia</th>
                  <th scope="col">Desnivel (+D)</th>
                  <th scope="col">FC Media / RPE</th>
                  <th scope="col">Carga Calculada</th>
                </tr>
              </thead>
              <tbody>
                {activities.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
                      {isLoading ? 'Cargando actividades...' : 'No hay entrenamientos registrados aún. Carga un archivo GPS (.FIT/.GPX/.CSV) o registra una sesión manual con Foster sRPE.'}
                    </td>
                  </tr>
                ) : (
                  activities.map((act) => (
                    <tr key={act.id} data-testid="activity-row">
                      <td style={{ whiteSpace: 'nowrap', fontSize: '0.85rem' }}>
                        <strong>{formatDateTime(act.started_at)}</strong>
                      </td>
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
                          {formatSport(act.sport_category)}
                        </div>
                        {act.notes && (
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.15rem', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
                          {formatOrigin(act.source_type)}
                        </span>
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>{formatDuration(act.duration_minutes)}</td>
                      <td>{formatDistance(act.distance_km)}</td>
                      <td>{formatElevation(act.elevation_gain_m)}</td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        {formatHeartRateRPE(act.avg_hr, act.session_rpe)}
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <strong style={{ color: 'var(--text-primary)' }}>
                          {formatCalculatedLoad(act)}
                        </strong>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalActivities > 20 && (
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
                Página {page} de {Math.ceil(totalActivities / 20)}
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page >= Math.ceil(totalActivities / 20) || isLoading}
                onClick={() => setPage((p) => p + 1)}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
              >
                Siguiente →
              </button>
            </footer>
          )}
        </article>
      </div>

      {/* Quick Logging Modal (Single and Batch) */}
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
