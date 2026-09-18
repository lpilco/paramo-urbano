/**
 * @fileoverview Banister Impulse-Response EWMA Chart component.
 * Visualizes Chronic Training Load (CTL), Acute Training Load (ATL) and Training Stress Balance (TSB).
 * @module components/charts/BanisterChart
 */

import React, { useState } from 'react';
import type { BanisterMetrics } from '../../types';

export interface BanisterChartProps {
  metrics: BanisterMetrics;
  historicalDays?: Array<{
    day: string;
    ctl: number;
    atl: number;
    tsb: number;
  }>;
}

export const BanisterChart: React.FC<BanisterChartProps> = ({
  metrics,
  historicalDays,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<{
    day: string;
    ctl: number;
    atl: number;
    tsb: number;
    x: number;
    y: number;
  } | null>(null);

  // Generate synthetic smooth 14-day historical series leading to current metrics if not provided
  const points =
    historicalDays && historicalDays.length > 0
      ? historicalDays
      : Array.from({ length: 14 }, (_, i) => {
          const daysAgo = 13 - i;
          const factor = (i + 1) / 14;
          const ctlVal = Math.round((metrics.ctl * 0.85 + metrics.ctl * 0.15 * factor) * 10) / 10;
          const atlVal = Math.round((metrics.atl * 0.75 + metrics.atl * 0.25 * factor) * 10) / 10;
          const tsbVal = Math.round((ctlVal - atlVal) * 10) / 10;

          const d = new Date();
          d.setDate(d.getDate() - daysAgo);
          const label = `${d.getDate()}/${d.getMonth() + 1}`;

          return {
            day: i === 13 ? 'Hoy' : label,
            ctl: i === 13 ? metrics.ctl : ctlVal,
            atl: i === 13 ? metrics.atl : atlVal,
            tsb: i === 13 ? metrics.tsb : tsbVal,
          };
        });

  // Dimensions
  const svgWidth = 600;
  const svgHeight = 220;
  const padding = { top: 20, right: 25, bottom: 35, left: 35 };
  const graphWidth = svgWidth - padding.left - padding.right;
  const graphHeight = svgHeight - padding.top - padding.bottom;

  // Scale bounds: Min value (considering TSB can be negative) to Max value
  const allValues = points.flatMap((p) => [p.ctl, p.atl, p.tsb]);
  const minVal = Math.min(-30, Math.floor(Math.min(...allValues) / 10) * 10);
  const maxVal = Math.max(80, Math.ceil(Math.max(...allValues) / 10) * 10);
  const valRange = maxVal - minVal || 1;

  const getY = (val: number) => {
    return padding.top + graphHeight - ((val - minVal) / valRange) * graphHeight;
  };

  const getX = (index: number) => {
    return padding.left + (index / (points.length - 1)) * graphWidth;
  };

  const zeroY = getY(0);

  // SVG Paths
  const ctlPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.ctl)}`).join(' ');
  const atlPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.atl)}`).join(' ');
  const tsbPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.tsb)}`).join(' ');

  return (
    <article
      className="card banister-chart-card"
      aria-labelledby="banister-chart-title"
      data-testid="banister-chart-card"
    >
      <header className="card-header">
        <div>
          <h3 id="banister-chart-title" className="card-title">
            Curvas de Carga y Fatiga (Banister EWMA)
          </h3>
          <p className="card-subtitle">
            Fitness (CTL, τ=42d) • Fatiga (ATL, τ=7d) • Forma (TSB = CTL - ATL)
          </p>
        </div>
      </header>

      <div className="chart-container" style={{ position: 'relative' }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="chart-svg"
          role="img"
          aria-label="Gráfica temporal interactiva del modelo Banister con curvas de CTL, ATL y TSB"
        >
          {/* Zero Line for TSB */}
          <line
            x1={padding.left}
            y1={zeroY}
            x2={svgWidth - padding.right}
            y2={zeroY}
            stroke="var(--border-strong)"
            strokeWidth="1"
            strokeDasharray="4 4"
          />
          <text
            x={svgWidth - padding.right + 4}
            y={zeroY + 3}
            fill="var(--text-muted)"
            fontSize="9"
          >
            TSB 0
          </text>

          {/* Grid lines */}
          {[-20, 20, 40, 60].map((val) => (
            <g key={val}>
              <line
                x1={padding.left}
                y1={getY(val)}
                x2={svgWidth - padding.right}
                y2={getY(val)}
                stroke="var(--border-subtle)"
                strokeWidth="0.5"
              />
              <text
                x={padding.left - 6}
                y={getY(val) + 3}
                fill="var(--text-muted)"
                fontSize="9"
                textAnchor="end"
              >
                {val}
              </text>
            </g>
          ))}

          {/* Lines */}
          <path d={ctlPath} fill="none" stroke="var(--accent-glacier)" strokeWidth="2.5" />
          <path d={atlPath} fill="none" stroke="var(--accent-summit)" strokeWidth="2.5" />
          <path d={tsbPath} fill="none" stroke="var(--accent-emerald)" strokeWidth="2" strokeDasharray="3 3" />

          {/* Interactive Data Points */}
          {points.map((p, idx) => {
            const x = getX(idx);
            return (
              <g key={p.day}>
                {/* Date Label on X axis for alternating days */}
                {idx % 2 === 1 || idx === points.length - 1 ? (
                  <text
                    x={x}
                    y={svgHeight - 10}
                    fill="var(--text-muted)"
                    fontSize="9"
                    textAnchor="middle"
                  >
                    {p.day}
                  </text>
                ) : null}

                {/* Point hit target */}
                <circle
                  cx={x}
                  cy={getY(p.ctl)}
                  r={idx === points.length - 1 ? 4.5 : 3}
                  fill="var(--accent-glacier)"
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoveredPoint({ ...p, x, y: getY(p.ctl) })}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
                <circle
                  cx={x}
                  cy={getY(p.atl)}
                  r={idx === points.length - 1 ? 4.5 : 3}
                  fill="var(--accent-summit)"
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoveredPoint({ ...p, x, y: getY(p.atl) })}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
                <circle
                  cx={x}
                  cy={getY(p.tsb)}
                  r={idx === points.length - 1 ? 4.5 : 3}
                  fill="var(--accent-emerald)"
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoveredPoint({ ...p, x, y: getY(p.tsb) })}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <aside
            style={{
              position: 'absolute',
              left: `${(hoveredPoint.x / svgWidth) * 100}%`,
              top: `${(hoveredPoint.y / svgHeight) * 100}%`,
              transform: 'translate(-50%, -115%)',
              background: 'rgba(9, 13, 18, 0.92)',
              backdropFilter: 'blur(8px)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.5rem 0.75rem',
              fontSize: '0.75rem',
              color: 'var(--text-primary)',
              pointerEvents: 'none',
              zIndex: 10,
              boxShadow: 'var(--shadow-md)',
              whiteSpace: 'nowrap',
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: '0.2rem' }}>{hoveredPoint.day}</div>
            <div style={{ color: 'var(--accent-glacier)' }}>CTL (Fitness): {hoveredPoint.ctl}</div>
            <div style={{ color: 'var(--accent-summit)' }}>ATL (Fatiga): {hoveredPoint.atl}</div>
            <div style={{ color: 'var(--accent-emerald)' }}>TSB (Forma): {hoveredPoint.tsb > 0 ? `+${hoveredPoint.tsb}` : hoveredPoint.tsb}</div>
          </aside>
        )}
      </div>

      {/* Legends */}
      <footer className="chart-legend">
        <span className="chart-legend-item">
          <span className="chart-legend-dot" style={{ background: 'var(--accent-glacier)' }} />
          <span>CTL (Fitness ~42d): <strong>{metrics.ctl}</strong></span>
        </span>
        <span className="chart-legend-item">
          <span className="chart-legend-dot" style={{ background: 'var(--accent-summit)' }} />
          <span>ATL (Fatiga ~7d): <strong>{metrics.atl}</strong></span>
        </span>
        <span className="chart-legend-item">
          <span className="chart-legend-dot" style={{ background: 'var(--accent-emerald)' }} />
          <span>TSB (Forma): <strong>{metrics.tsb > 0 ? `+${metrics.tsb}` : metrics.tsb}</strong></span>
        </span>
      </footer>
    </article>
  );
};
