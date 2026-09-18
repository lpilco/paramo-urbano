/**
 * @fileoverview Tim Gabbett Acute:Chronic Workload Ratio (ACWR) Speedometer / Gauge component.
 * @module components/charts/ACWRGauge
 */

import React from 'react';
import type { ACWRMetrics } from '../../types';

export interface ACWRGaugeProps {
  metrics: ACWRMetrics;
}

export const ACWRGauge: React.FC<ACWRGaugeProps> = ({ metrics }) => {
  const { ratio, zone, requires_mandatory_rest, freeze_weekly_increments, recommendation } = metrics;

  // Determine visual style based on Gabbett's zones
  const isDanger = zone === 'DANGER' || ratio > 1.5 || requires_mandatory_rest;
  const isWarning = !isDanger && (zone === 'WARNING' || (ratio > 1.3 && ratio <= 1.5) || freeze_weekly_increments);

  let zoneColor = 'var(--acwr-sweet-spot)';
  let zoneLabel = 'Sweet Spot (0.8 - 1.3)';
  let badgeClass = 'badge-sweet-spot';
  let statusHeadline = 'FRESCURA ÓPTIMA: Preparado para asimilar alta intensidad';

  if (isDanger) {
    zoneColor = 'var(--acwr-danger)';
    zoneLabel = 'Zona Crítica (> 1.5)';
    badgeClass = 'badge-danger';
    statusHeadline = 'PELIGRO BIOMECÁNICO: Descanso obligatorio prescrito';
  } else if (isWarning) {
    zoneColor = 'var(--acwr-warning)';
    zoneLabel = 'Zona de Precaución (1.3 - 1.5)';
    badgeClass = 'badge-warning';
    statusHeadline = 'ZONA DE PRECAUCIÓN: Incrementos de volumen congelados';
  }

  // Calculate angle for needle: range 0.0 to 2.2 maps to -90 deg to +90 deg
  const clampedRatio = Math.max(0, Math.min(ratio, 2.2));
  const angle = -90 + (clampedRatio / 2.2) * 180;

  return (
    <article
      className="card acwr-gauge-card"
      aria-labelledby="acwr-gauge-title"
      data-testid="acwr-gauge-card"
    >
      <header className="card-header">
        <div>
          <h3 id="acwr-gauge-title" className="card-title">
            Control Lesivo: Semáforo ACWR de Gabbett
          </h3>
          <p className="card-subtitle">
            Relación de Carga Aguda (7d) vs Crónica (28d)
          </p>
        </div>
        <span className={`badge ${badgeClass}`} data-testid="acwr-zone-badge">
          {zoneLabel}
        </span>
      </header>

      <div className="gauge-container" data-testid="acwr-gauge-container">
        {/* Semi-circular Speedometer SVG */}
        <svg
          viewBox="0 0 300 160"
          className="gauge-svg"
          role="img"
          aria-label={`Velocímetro ACWR con ratio actual de ${ratio.toFixed(2)}`}
        >
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="36%" stopColor="#10b981" />
              <stop offset="60%" stopColor="#10b981" />
              <stop offset="68%" stopColor="#f59e0b" />
              <stop offset="85%" stopColor="#ef4444" />
              <stop offset="100%" stopColor="#b91c1c" />
            </linearGradient>
          </defs>

          {/* Background Arc */}
          <path
            d="M 30 140 A 120 120 0 0 1 270 140"
            fill="none"
            stroke="var(--bg-input)"
            strokeWidth="22"
            strokeLinecap="round"
          />

          {/* Colored Gradient Arc */}
          <path
            d="M 30 140 A 120 120 0 0 1 270 140"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="18"
            strokeLinecap="round"
            opacity="0.9"
          />

          {/* Threshold markers */}
          {/* Sweet Spot 0.8: angle = -90 + (0.8/2.2)*180 = -24.5 deg */}
          {/* Warning 1.3: angle = -90 + (1.3/2.2)*180 = 16.3 deg */}
          {/* Danger 1.5: angle = -90 + (1.5/2.2)*180 = 32.7 deg */}

          {/* Center Pivot */}
          <circle cx="150" cy="140" r="10" fill="var(--border-strong)" />
          <circle cx="150" cy="140" r="6" fill={zoneColor} />

          {/* Dynamic Needle */}
          <g
            className="gauge-needle"
            style={{ transform: `rotate(${angle}deg)`, transformOrigin: '150px 140px' }}
            data-testid="gauge-needle"
          >
            <line
              x1="150"
              y1="140"
              x2="150"
              y2="38"
              stroke="#ffffff"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
          </g>

          {/* Scale Labels */}
          <text x="30" y="156" fill="var(--text-muted)" fontSize="10" textAnchor="middle">
            0.0
          </text>
          <text x="110" y="55" fill="var(--acwr-sweet-spot)" fontSize="10" textAnchor="middle" fontWeight="bold">
            0.8
          </text>
          <text x="185" y="55" fill="var(--acwr-warning)" fontSize="10" textAnchor="middle" fontWeight="bold">
            1.3
          </text>
          <text x="235" y="80" fill="var(--acwr-danger)" fontSize="10" textAnchor="middle" fontWeight="bold">
            1.5
          </text>
          <text x="270" y="156" fill="var(--text-muted)" fontSize="10" textAnchor="middle">
            2.2+
          </text>
        </svg>

        {/* Ratio Numerical Display */}
        <div style={{ textAlign: 'center', marginTop: '-10px' }}>
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '2.5rem',
              fontWeight: 800,
              color: zoneColor,
              lineHeight: 1,
            }}
            data-testid="acwr-ratio-number"
          >
            {ratio.toFixed(2)}
          </span>
          <p
            style={{
              fontSize: '0.85rem',
              fontWeight: 700,
              color: zoneColor,
              marginTop: '0.25rem',
            }}
            data-testid="acwr-headline"
          >
            {statusHeadline}
          </p>
          <p
            style={{
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
              marginTop: '0.4rem',
              maxWidth: '480px',
            }}
            data-testid="acwr-recommendation"
          >
            {recommendation}
          </p>
        </div>
      </div>
    </article>
  );
};
