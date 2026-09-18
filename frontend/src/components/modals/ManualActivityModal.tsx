/**
 * @fileoverview Modal dialog for logging manual non-GPS training sessions (Foster sRPE).
 * @module components/modals/ManualActivityModal
 */

import React, { useState, useEffect } from 'react';
import { logManualActivity } from '../../api/activitiesApi';
import { ApiError } from '../../api/apiClient';
import type { ManualActivityResponse, SportCategory } from '../../types';

export interface ManualActivityModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (created: ManualActivityResponse) => void;
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

export const ManualActivityModal: React.FC<ManualActivityModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [sportCategory, setSportCategory] = useState<SportCategory>('STRENGTH');
  const [startedAt, setStartedAt] = useState(() => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  });
  const [durationMinutes, setDurationMinutes] = useState<number>(50);
  const [sessionRpe, setSessionRpe] = useState<number>(8);
  const [distanceKm, setDistanceKm] = useState<number>(0);
  const [elevationGainM, setElevationGainM] = useState<number>(0);
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Strict validation
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
      >
        <header className="modal-header">
          <h3 id="modal-manual-title" className="card-title">
            Registro Manual de Sesión (Foster sRPE)
          </h3>
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

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {errorMessage && (
              <div
                className="alert-banner alert-banner-danger"
                style={{ padding: '0.65rem 0.85rem', marginBottom: '1rem' }}
                role="alert"
                data-testid="manual-modal-error"
              >
                <span>⚠️ {errorMessage}</span>
              </div>
            )}

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
              >
              </input>
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
      </div>
    </div>
  );
};
