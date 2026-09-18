/**
 * @fileoverview Modal dialog for logging manual non-GPS training sessions (Foster sRPE),
 * supporting both single session entry and atomic batch entry.
 * @module components/modals/ManualActivityModal
 */

import React, { useState, useEffect, useCallback } from 'react';
import { logManualActivity, logBatchManualActivities } from '../../api/activitiesApi';
import { ApiError } from '../../api/apiClient';
import type {
  BatchManualActivitiesResponse,
  ManualActivityRequest,
  ManualActivityResponse,
  SportCategory,
} from '../../types';

export interface ManualActivityModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (created?: ManualActivityResponse | BatchManualActivitiesResponse) => void;
}

interface BatchRowItem {
  id: string;
  sport_category: SportCategory;
  started_at: string;
  duration_minutes: number;
  session_rpe: number;
  distance_km: number;
  elevation_gain_m: number;
  notes: string;
}

const RPE_DESCRIPTIONS: Record<number, string> = {
  1: '1 - Muy muy suave (Recuperación casi nula)',
  2: '2 - Muy suave (Conversación fluida sin esfuerzo)',
  3: '3 - Suave (Ritmo aeróbico cómodo)',
  4: '4 - Moderado (Respiración rítmica)',
  5: '5 - Algo duro (Inicio de fatiga muscular leve)',
  6: '6 - Duro (Requiere concentración)',
  7: '7 - Muy duro (Respiración agitada, frases cortas)',
  8: '8 - Muy duro + (Zona de umbral anaeróbico)',
  9: '9 - Extremadamente duro (Casi esfuerzo máximo)',
  10: '10 - Máximo absoluto (Agotamiento total)',
};

const getNowLocalDateTime = (offsetHours = 0): string => {
  const d = new Date();
  if (offsetHours !== 0) {
    d.setHours(d.getHours() - offsetHours);
  }
  const pad = (n: number) => n.toString().padStart(2, '0');
  const year = d.getFullYear();
  const month = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

export const ManualActivityModal: React.FC<ManualActivityModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single');

  // Single form state
  const [sportCategory, setSportCategory] = useState<SportCategory>('STRENGTH');
  const [startedAt, setStartedAt] = useState<string>(() => getNowLocalDateTime());
  const [durationMinutes, setDurationMinutes] = useState<number>(50);
  const [sessionRpe, setSessionRpe] = useState<number>(8);
  const [distanceKm, setDistanceKm] = useState<number>(0);
  const [elevationGainM, setElevationGainM] = useState<number>(0);
  const [notes, setNotes] = useState<string>('');

  // Batch form state
  const createDefaultBatchRow = useCallback((offsetDays = 0, sport: SportCategory = 'STRENGTH', rpe = 8): BatchRowItem => {
    const d = new Date();
    d.setDate(d.getDate() - offsetDays);
    const pad = (n: number) => n.toString().padStart(2, '0');
    const isoLocal = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T07:00`;
    return {
      id: `row_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      sport_category: sport,
      started_at: isoLocal,
      duration_minutes: 50,
      session_rpe: rpe,
      distance_km: 0,
      elevation_gain_m: 0,
      notes: '',
    };
  }, []);

  const [batchRows, setBatchRows] = useState<BatchRowItem[]>([]);

  // Submission & error handling
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Reset form whenever modal opens to prevent stale locks or reuse
  useEffect(() => {
    if (isOpen) {
      setIsSubmitting(false);
      setErrorMessage(null);
      setStartedAt(getNowLocalDateTime());
      setDurationMinutes(50);
      setSessionRpe(8);
      setDistanceKm(0);
      setElevationGainM(0);
      setNotes('');
      setSportCategory('STRENGTH');
      setBatchRows([
        createDefaultBatchRow(0, 'STRENGTH', 8),
        createDefaultBatchRow(1, 'ROAD_RUN', 7),
      ]);
    }
  }, [isOpen, createDefaultBatchRow]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Real-time deterministic Foster load calculation: minutes * RPE
  const calculatedLoad = durationMinutes > 0 && sessionRpe >= 1 && sessionRpe <= 10
    ? durationMinutes * sessionRpe
    : 0;

  const isRpeValid = Number.isInteger(sessionRpe) && sessionRpe >= 1 && sessionRpe <= 10;

  // Single submit handler
  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!isRpeValid) {
      setErrorMessage('El RPE debe ser un número entero comprendido entre 1 y 10.');
      return;
    }

    if (durationMinutes <= 0) {
      setErrorMessage('La duración debe ser mayor a 0 minutos.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await logManualActivity({
        sport_category: sportCategory,
        started_at: new Date(startedAt).toISOString(),
        duration_minutes: durationMinutes,
        session_rpe: sessionRpe,
        notes: notes.trim(),
        distance_km: distanceKm > 0 ? distanceKm : 0,
        elevation_gain_m: elevationGainM > 0 ? elevationGainM : 0,
      });

      onSuccess?.(response);
      onClose();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail || 'Error al registrar actividad manual.');
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Error de comunicación con el servidor.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Batch helpers
  const handleAddBatchRow = () => {
    setBatchRows((prev) => [
      ...prev,
      createDefaultBatchRow(prev.length, 'ROAD_RUN', 6),
    ]);
  };

  const handleRemoveBatchRow = (id: string) => {
    if (batchRows.length <= 1) return;
    setBatchRows((prev) => prev.filter((r) => r.id !== id));
  };

  const handleUpdateBatchRow = <K extends keyof BatchRowItem>(
    id: string,
    field: K,
    value: BatchRowItem[K]
  ) => {
    setBatchRows((prev) =>
      prev.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  const totalBatchLoad = batchRows.reduce(
    (sum, r) => sum + (r.duration_minutes > 0 && r.session_rpe >= 1 && r.session_rpe <= 10 ? r.duration_minutes * r.session_rpe : 0),
    0
  );

  // Batch submit handler
  const handleBatchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (batchRows.length === 0) {
      setErrorMessage('Agrega al menos una sesión para guardar.');
      return;
    }

    for (let i = 0; i < batchRows.length; i++) {
      const row = batchRows[i];
      if (row.duration_minutes <= 0) {
        setErrorMessage(`Fila ${i + 1}: La duración debe ser mayor a 0 minutos.`);
        return;
      }
      if (row.session_rpe < 1 || row.session_rpe > 10) {
        setErrorMessage(`Fila ${i + 1}: El RPE debe ser un entero entre 1 y 10.`);
        return;
      }
    }

    setIsSubmitting(true);

    try {
      const payloadItems: ManualActivityRequest[] = batchRows.map((r) => ({
        sport_category: r.sport_category,
        started_at: new Date(r.started_at).toISOString(),
        duration_minutes: r.duration_minutes,
        session_rpe: r.session_rpe,
        notes: r.notes.trim(),
        distance_km: r.distance_km > 0 ? r.distance_km : 0,
        elevation_gain_m: r.elevation_gain_m > 0 ? r.elevation_gain_m : 0,
      }));

      const res = await logBatchManualActivities(payloadItems);
      onSuccess?.(res);
      onClose();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail || 'Error al guardar sesiones en lote.');
      } else if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Error de comunicación con el servidor.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-manual-title"
        data-testid="manual-activity-modal"
        style={{ maxWidth: activeTab === 'batch' ? '820px' : '560px' }}
      >
        <header className="modal-header">
          <div>
            <h3 id="modal-manual-title" className="card-title">
              Registro Manual de Sesión (Foster sRPE)
            </h3>
            <p className="card-subtitle" style={{ fontSize: '0.8rem', marginTop: '0.2rem' }}>
              Carga determinista = Duración (min) × RPE (1-10)
            </p>
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
            aria-label="Cerrar modal"
            style={{ padding: '0.25rem 0.5rem', lineHeight: 1 }}
          >
            ✕
          </button>
        </header>

        {/* Tab switcher: Individual vs Batch */}
        <div style={{ padding: '0.5rem 1.5rem 0 1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="tab-group" style={{ width: '100%', marginBottom: 0 }}>
            <button
              type="button"
              className={`tab-btn ${activeTab === 'single' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('single');
                setErrorMessage(null);
              }}
              data-testid="tab-single-manual"
            >
              📝 Registro Individual (1 por 1)
            </button>
            <button
              type="button"
              className={`tab-btn ${activeTab === 'batch' ? 'active' : ''}`}
              onClick={() => {
                setActiveTab('batch');
                setErrorMessage(null);
              }}
              data-testid="tab-batch-manual"
            >
              📦 Ingreso Masivo (Batch)
            </button>
          </div>
        </div>

        {errorMessage && (
          <div style={{ padding: '0.75rem 1.5rem 0 1.5rem' }}>
            <div
              className="alert-banner alert-banner-danger"
              style={{ padding: '0.65rem 0.85rem', margin: 0 }}
              role="alert"
              data-testid="manual-modal-error"
            >
              <span>⚠️ {errorMessage}</span>
            </div>
          </div>
        )}

        {/* SINGLE REGISTRATION TAB */}
        {activeTab === 'single' && (
          <form onSubmit={handleSingleSubmit}>
            <div className="modal-body">
              {/* Sport Category */}
              <div className="form-group">
                <label htmlFor="manual-sport" className="form-label">
                  Disciplina Deportiva *
                </label>
                <select
                  id="manual-sport"
                  className="form-select"
                  value={sportCategory}
                  onChange={(e) => setSportCategory(e.target.value as SportCategory)}
                  required
                >
                  <option value="STRENGTH">Fuerza & Acondicionamiento (STRENGTH)</option>
                  <option value="ROAD_RUN">Carrera de Asfalto (ROAD_RUN)</option>
                  <option value="TRAIL_RUN">Trail Running (TRAIL_RUN)</option>
                  <option value="HIKE">Trekking / Senderismo (HIKE)</option>
                </select>
              </div>

              {/* Date and Time */}
              <div className="form-group">
                <label htmlFor="manual-date" className="form-label">
                  Fecha y Hora de Inicio *
                </label>
                <input
                  id="manual-date"
                  type="datetime-local"
                  className="form-input"
                  value={startedAt}
                  onChange={(e) => setStartedAt(e.target.value)}
                  required
                />
              </div>

              {/* Duration */}
              <div className="form-group">
                <label htmlFor="manual-duration" className="form-label">
                  Duración (minutos) *
                </label>
                <input
                  id="manual-duration"
                  type="number"
                  min="1"
                  max="1440"
                  className="form-input"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  required
                />
              </div>

              {/* Foster sRPE Slider & Number */}
              <div className="form-group">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label htmlFor="manual-rpe" className="form-label">
                    Esfuerzo Percibido (sRPE 1-10) *
                  </label>
                  <span
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '1.1rem',
                      fontWeight: 800,
                      color: sessionRpe >= 8 ? 'var(--acwr-danger)' : sessionRpe >= 5 ? 'var(--acwr-warning)' : 'var(--acwr-sweet-spot)',
                    }}
                    data-testid="rpe-display-value"
                  >
                    RPE {sessionRpe}
                  </span>
                </div>

                <input
                  id="manual-rpe"
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={sessionRpe}
                  onChange={(e) => setSessionRpe(Number(e.target.value))}
                  style={{ width: '100%', margin: '0.5rem 0' }}
                  aria-describedby="rpe-anchor-text"
                />

                <input
                  type="number"
                  id="manual-rpe-input"
                  min="1"
                  max="10"
                  className="form-input"
                  value={sessionRpe}
                  onChange={(e) => setSessionRpe(Number(e.target.value))}
                  style={{ width: '90px', alignSelf: 'flex-start' }}
                  aria-label="Entrada numérica de RPE"
                />

                <span id="rpe-anchor-text" className="form-hint" style={{ marginTop: '0.25rem' }}>
                  {RPE_DESCRIPTIONS[sessionRpe] || 'Escala Borg/Foster'}
                </span>
              </div>

              {/* Real-time Dynamic Load Preview */}
              <div
                className="card"
                style={{
                  background: 'var(--bg-input)',
                  padding: '0.85rem 1rem',
                  border: '1px solid var(--border-strong)',
                  marginBottom: '1rem',
                }}
                data-testid="foster-load-preview"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Carga Foster Determinista (min × RPE)
                    </span>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {durationMinutes} min × RPE {sessionRpe}
                    </div>
                  </div>
                  <div
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '1.75rem',
                      fontWeight: 800,
                      color: 'var(--accent-summit)',
                    }}
                    data-testid="calculated-foster-load"
                  >
                    {calculatedLoad} <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>u.a.</span>
                  </div>
                </div>
              </div>

              {/* Optional Distance & Elevation for Trail / Road */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div className="form-group">
                  <label htmlFor="manual-distance" className="form-label">
                    Distancia (km, opcional)
                  </label>
                  <input
                    id="manual-distance"
                    type="number"
                    step="0.1"
                    min="0"
                    className="form-input"
                    value={distanceKm || ''}
                    onChange={(e) => setDistanceKm(Number(e.target.value))}
                    placeholder="0.0"
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="manual-elevation" className="form-label">
                    Desnivel (+D m, opcional)
                  </label>
                  <input
                    id="manual-elevation"
                    type="number"
                    min="0"
                    className="form-input"
                    value={elevationGainM || ''}
                    onChange={(e) => setElevationGainM(Number(e.target.value))}
                    placeholder="0"
                  />
                </div>
              </div>

              {/* Notes */}
              <div className="form-group">
                <label htmlFor="manual-notes" className="form-label">
                  Notas de la sesión
                </label>
                <textarea
                  id="manual-notes"
                  className="form-textarea"
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Ej. Sentadillas goblet, desplantes y estiramiento de isquiotibiales"
                />
              </div>
            </div>

            <footer className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting || !isRpeValid || durationMinutes <= 0}
                data-testid="submit-manual-btn"
              >
                {isSubmitting ? 'Guardando...' : 'Guardar Entrenamiento'}
              </button>
            </footer>
          </form>
        )}

        {/* BATCH REGISTRATION TAB */}
        {activeTab === 'batch' && (
          <form onSubmit={handleBatchSubmit}>
            <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                Ingresa múltiples sesiones en una única transacción relacional. El sistema calculará la carga acumulada y actualizará tus baselines Banister (CTL/ATL).
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {batchRows.map((row, idx) => {
                  const rowLoad = row.duration_minutes * (row.session_rpe || 0);
                  return (
                    <div
                      key={row.id}
                      className="card"
                      style={{
                        padding: '0.75rem',
                        background: 'var(--bg-input)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--radius-sm)',
                      }}
                      data-testid={`batch-row-${idx}`}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                          Sesión #{idx + 1}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <span style={{ fontSize: '0.8rem', color: 'var(--accent-summit)', fontWeight: 700 }}>
                            {rowLoad} u.a.
                          </span>
                          {batchRows.length > 1 && (
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => handleRemoveBatchRow(row.id)}
                              style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', color: 'var(--acwr-danger)' }}
                              aria-label={`Eliminar fila ${idx + 1}`}
                            >
                              ✕ Quitar
                            </button>
                          )}
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem' }}>
                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Deporte</label>
                          <select
                            className="form-select"
                            style={{ fontSize: '0.8rem', padding: '0.35rem 0.5rem' }}
                            value={row.sport_category}
                            onChange={(e) => handleUpdateBatchRow(row.id, 'sport_category', e.target.value as SportCategory)}
                          >
                            <option value="STRENGTH">Fuerza</option>
                            <option value="ROAD_RUN">Asfalto</option>
                            <option value="TRAIL_RUN">Trail</option>
                            <option value="HIKE">Trekking</option>
                          </select>
                        </div>

                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Fecha y Hora</label>
                          <input
                            type="datetime-local"
                            className="form-input"
                            style={{ fontSize: '0.8rem', padding: '0.35rem 0.5rem' }}
                            value={row.started_at}
                            onChange={(e) => handleUpdateBatchRow(row.id, 'started_at', e.target.value)}
                            required
                          />
                        </div>

                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Duración (min)</label>
                          <input
                            type="number"
                            min="1"
                            max="1440"
                            className="form-input"
                            style={{ fontSize: '0.8rem', padding: '0.35rem 0.5rem' }}
                            value={row.duration_minutes}
                            onChange={(e) => handleUpdateBatchRow(row.id, 'duration_minutes', Number(e.target.value))}
                            required
                          />
                        </div>

                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>RPE (1-10)</label>
                          <input
                            type="number"
                            min="1"
                            max="10"
                            className="form-input"
                            style={{ fontSize: '0.8rem', padding: '0.35rem 0.5rem' }}
                            value={row.session_rpe}
                            onChange={(e) => handleUpdateBatchRow(row.id, 'session_rpe', Number(e.target.value))}
                            required
                          />
                        </div>

                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Distancia (km)</label>
                          <input
                            type="number"
                            step="0.1"
                            min="0"
                            className="form-input"
                            style={{ fontSize: '0.8rem', padding: '0.35rem 0.5rem' }}
                            value={row.distance_km || ''}
                            onChange={(e) => handleUpdateBatchRow(row.id, 'distance_km', Number(e.target.value))}
                            placeholder="0"
                          />
                        </div>

                        <div>
                          <label className="form-label" style={{ fontSize: '0.75rem' }}>Desnivel (+D m)</label>
                          <input
                            type="number"
                            min="0"
                            className="form-input"
                            style={{ fontSize: '0.8rem', padding: '0.35rem 0.5rem' }}
                            value={row.elevation_gain_m || ''}
                            onChange={(e) => handleUpdateBatchRow(row.id, 'elevation_gain_m', Number(e.target.value))}
                            placeholder="0"
                          />
                        </div>
                      </div>

                      <div style={{ marginTop: '0.4rem' }}>
                        <input
                          type="text"
                          className="form-input"
                          style={{ fontSize: '0.8rem', padding: '0.35rem 0.5rem' }}
                          value={row.notes}
                          onChange={(e) => handleUpdateBatchRow(row.id, 'notes', e.target.value)}
                          placeholder="Notas breves de la sesión (opcional)"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleAddBatchRow}
                  style={{ fontSize: '0.85rem' }}
                  data-testid="add-batch-row-btn"
                >
                  + Agregar otra fila
                </button>

                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Carga Acumulada del Lote: </span>
                  <strong style={{ fontSize: '1.1rem', color: 'var(--accent-summit)' }}>
                    {totalBatchLoad} u.a.
                  </strong>
                </div>
              </div>
            </div>

            <footer className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting || batchRows.length === 0}
                data-testid="submit-batch-btn"
              >
                {isSubmitting ? 'Guardando Lote...' : `Guardar Todas (${batchRows.length})`}
              </button>
            </footer>
          </form>
        )}
      </div>
    </div>
  );
};
