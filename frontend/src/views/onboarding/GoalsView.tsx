/**
 * @fileoverview Goals View: Parameterized athletic goals configuration with strict 14-day adaptation horizon.
 * @module views/onboarding/GoalsView
 */

import React, { useState, useMemo } from 'react';
import { createAthleteGoal } from '../../api/goalsApi';
import { ApiError } from '../../api/apiClient';
import type { Discipline } from '../../types';

export const GoalsView: React.FC = () => {
  const [discipline, setDiscipline] = useState<Discipline>('ROAD_RUNNING');
  const [subgoalType, setSubgoalType] = useState<string>('HALF_MARATHON');
  const [customDistanceKm, setCustomDistanceKm] = useState<number>(21.097);
  const [targetElevationGainM, setTargetElevationGainM] = useState<number>(0);
  const [availableDays, setAvailableDays] = useState<number>(5);
  const [mountainAltitudeCategory, setMountainAltitudeCategory] = useState<string>('BAJA_MONTANA');

  // Calculate the strict minimum date: today + 14 days
  const minDateStr = useMemo(() => {
    const minDate = new Date();
    minDate.setDate(minDate.getDate() + 14);
    return minDate.toISOString().split('T')[0];
  }, []);

  // Default target date: today + 90 days (~13 weeks)
  const [targetDate, setTargetDate] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 90);
    return d.toISOString().split('T')[0];
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Check 14-day rule
  const isDateCompliant = useMemo(() => {
    if (!targetDate) return false;
    const selected = new Date(`${targetDate}T00:00:00`);
    const threshold = new Date(`${minDateStr}T00:00:00`);
    return selected >= threshold;
  }, [targetDate, minDateStr]);

  // Handle discipline change presets
  const handleDisciplineChange = (newDiscipline: Discipline) => {
    setDiscipline(newDiscipline);
    if (newDiscipline === 'ROAD_RUNNING') {
      setSubgoalType('HALF_MARATHON');
      setCustomDistanceKm(21.097);
      setTargetElevationGainM(0);
    } else if (newDiscipline === 'TRAIL_RUNNING') {
      setSubgoalType('TRAIL_MARATHON');
      setCustomDistanceKm(42.195);
      setTargetElevationGainM(2400);
    } else if (newDiscipline === 'TREKKING') {
      setSubgoalType('ALPINISMO_TREKKING');
      setCustomDistanceKm(18.0);
      setTargetElevationGainM(1600);
      setMountainAltitudeCategory('MEDIA_MONTANA');
    }
  };

  const handleSubgoalPreset = (presetKm: number, presetType: string, presetElevation = 0) => {
    setSubgoalType(presetType);
    setCustomDistanceKm(presetKm);
    if (presetElevation > 0) {
      setTargetElevationGainM(presetElevation);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Strict validation: target_date >= today + 14 days
    if (!isDateCompliant) {
      setErrorMessage(
        'La fecha objetivo debe programarse con al menos 14 días de antelación para permitir una adaptación biológica mínima.'
      );
      return;
    }

    if (customDistanceKm <= 0) {
      setErrorMessage('La distancia objetivo debe ser un valor positivo en kilómetros.');
      return;
    }

    if (discipline === 'TRAIL_RUNNING' && targetElevationGainM <= 0) {
      setErrorMessage('Para Trail Running el desnivel acumulado (+D) debe ser mayor a 0 metros.');
      return;
    }

    setIsSubmitting(true);

    try {
      await createAthleteGoal({
        discipline,
        subgoal_type: subgoalType,
        target_distance_km: customDistanceKm,
        target_elevation_gain_m: targetElevationGainM,
        target_date: targetDate,
        available_days_per_week: availableDays,
        mountain_altitude_category: discipline === 'TREKKING' ? mountainAltitudeCategory : null,
      });

      // Smooth navigation to planner
      window.location.hash = '#/planner';
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail || 'Error al persistir la meta deportiva.');
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
    <main className="main-content" id="main-content">
      <section style={{ maxWidth: '680px', margin: '0 auto' }}>
        <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', color: 'var(--text-primary)' }}>
            Configuración de Meta Deportiva
          </h1>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Periodización determinista ajustada a tu distancia, desnivel y ventana biológica de adaptación
          </p>
        </header>

        <form onSubmit={handleSubmit} className="card" data-testid="goals-form">
          {errorMessage && (
            <div
              className="alert-banner alert-banner-danger"
              role="alert"
              data-testid="goals-error-banner"
            >
              <span>⚠️ {errorMessage}</span>
            </div>
          )}

          {/* 1. Disciplina Selection */}
          <div className="form-group">
            <label htmlFor="discipline-select" className="form-label">
              1. Disciplina Deportiva *
            </label>
            <div className="tab-group" style={{ width: '100%' }}>
              <button
                type="button"
                className={`tab-btn ${discipline === 'ROAD_RUNNING' ? 'active' : ''}`}
                onClick={() => handleDisciplineChange('ROAD_RUNNING')}
                data-testid="disc-road-btn"
              >
                🏃 Asfalto (Ruta)
              </button>
              <button
                type="button"
                className={`tab-btn ${discipline === 'TRAIL_RUNNING' ? 'active' : ''}`}
                onClick={() => handleDisciplineChange('TRAIL_RUNNING')}
                data-testid="disc-trail-btn"
              >
                ⛰️ Trail Running (+D)
              </button>
              <button
                type="button"
                className={`tab-btn ${discipline === 'TREKKING' ? 'active' : ''}`}
                onClick={() => handleDisciplineChange('TREKKING')}
                data-testid="disc-trekking-btn"
              >
                🥾 Trekking / Pisos
              </button>
            </div>
          </div>

          {/* 2. Subgoals Presets for Road Running */}
          {discipline === 'ROAD_RUNNING' && (
            <div className="form-group">
              <span className="form-label">Submetas de Asfalto Populares</span>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.25rem' }}>
                <button
                  type="button"
                  className={`btn ${subgoalType === '5K' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                  onClick={() => handleSubgoalPreset(5.0, '5K')}
                >
                  5K
                </button>
                <button
                  type="button"
                  className={`btn ${subgoalType === '10K' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                  onClick={() => handleSubgoalPreset(10.0, '10K')}
                >
                  10K
                </button>
                <button
                  type="button"
                  className={`btn ${subgoalType === 'HALF_MARATHON' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                  onClick={() => handleSubgoalPreset(21.097, 'HALF_MARATHON')}
                >
                  21K (Media Maratón)
                </button>
                <button
                  type="button"
                  className={`btn ${subgoalType === 'MARATHON' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                  onClick={() => handleSubgoalPreset(42.195, 'MARATHON')}
                >
                  42K (Maratón)
                </button>
                <button
                  type="button"
                  className={`btn ${subgoalType === 'ULTRA_ROAD' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                  onClick={() => handleSubgoalPreset(50.0, 'ULTRA_ROAD')}
                >
                  Ultra Asfalto
                </button>
              </div>
            </div>
          )}

          {/* 3. Distance in km (all disciplines) */}
          <div className="form-group">
            <label htmlFor="goal-distance" className="form-label">
              Distancia exacta en Kilómetros *
            </label>
            <input
              id="goal-distance"
              type="number"
              step="0.1"
              min="1"
              max="250"
              className="form-input"
              value={customDistanceKm}
              onChange={(e) => setCustomDistanceKm(Number(e.target.value))}
              required
              data-testid="goal-distance-input"
            />
            <span className="form-hint">
              Ingresa el kilometraje exacto oficial de tu carrera o travesía.
            </span>
          </div>

          {/* 4. Trail Running: Mandatory +D */}
          {discipline === 'TRAIL_RUNNING' && (
            <div className="form-group">
              <label htmlFor="goal-elevation" className="form-label">
                Desnivel Positivo Acumulado (+D en metros) *
              </label>
              <input
                id="goal-elevation"
                type="number"
                min="50"
                max="12000"
                className="form-input"
                value={targetElevationGainM}
                onChange={(e) => setTargetElevationGainM(Number(e.target.value))}
                required
                placeholder="2400"
                data-testid="goal-elevation-input"
              />
              <span className="form-hint">
                Requerido para cuantificar la carga excéntrica en bajada y la velocidad vertical (VAM).
              </span>
            </div>
          )}

          {/* 5. Trekking: Altitudinal Floor Segmentation & Hypoxia Alert */}
          {discipline === 'TREKKING' && (
            <div className="form-group">
              <label htmlFor="altitude-category" className="form-label">
                Piso Térmico y Altitudinal *
              </label>
              <select
                id="altitude-category"
                className="form-select"
                value={mountainAltitudeCategory}
                onChange={(e) => setMountainAltitudeCategory(e.target.value)}
                data-testid="altitude-category-select"
              >
                <option value="BAJA_MONTANA">Baja Montaña (&lt; 3.500 msnm)</option>
                <option value="MEDIA_MONTANA">Media Montaña (3.500 - 4.800 msnm)</option>
                <option value="ALTA_MONTANA">Alta Montaña (&gt; 4.800 msnm / Glaciar)</option>
              </select>

              {mountainAltitudeCategory !== 'BAJA_MONTANA' && (
                <div
                  className="alert-banner alert-banner-warning"
                  style={{ marginTop: '0.85rem' }}
                  data-testid="hypoxia-warning"
                >
                  <span>⚠️</span>
                  <div>
                    <h5 style={{ fontWeight: 700, fontSize: '0.85rem', margin: 0 }}>
                      Advertencia Fisiológica de Hipoxia
                    </h5>
                    <p style={{ fontSize: '0.8rem', marginTop: '0.2rem' }}>
                      Por encima de los 3.500 metros, la presión parcial de oxígeno se reduce en un ~35%. El plan incorporará microciclos de aclimatación escalonada y control estricto de hidratación con sodio.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 6. Target Date: Strictly locked < 14 days */}
          <div className="form-group">
            <label htmlFor="target-date" className="form-label">
              Fecha Objetivo de la Competencia / Cumbre *
            </label>
            <input
              id="target-date"
              type="date"
              min={minDateStr}
              className="form-input"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              required
              data-testid="target-date-input"
            />
            <span className="form-hint">
              Horizonte mínimo de adaptación biológica: al menos 14 días a futuro (a partir de {minDateStr}).
            </span>
          </div>

          {/* 7. Available Days per Week */}
          <div className="form-group">
            <label htmlFor="available-days" className="form-label">
              Días de Entrenamiento Disponibles por Semana (1 a 7) *
            </label>
            <select
              id="available-days"
              className="form-select"
              value={availableDays}
              onChange={(e) => setAvailableDays(Number(e.target.value))}
            >
              <option value={3}>3 días / semana (Mínimo recomendado)</option>
              <option value={4}>4 días / semana</option>
              <option value={5}>5 días / semana (Estándar recomendado)</option>
              <option value={6}>6 días / semana (Alto rendimiento)</option>
            </select>
          </div>

          <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <a href="#/diagnostics" className="btn btn-secondary">
              Cancelar
            </a>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || !isDateCompliant}
              data-testid="submit-goal-btn"
            >
              {isSubmitting ? 'Inicializando Plan...' : 'Confirmar Meta y Generar Plan →'}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
};
