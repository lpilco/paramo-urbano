/**
 * @fileoverview Semantic global navigation header.
 * @module components/common/Navbar
 */

import React from 'react';
import { useAuth } from '../../store/authStore';

interface NavbarProps {
  currentRoute: string;
}

export const Navbar: React.FC<NavbarProps> = ({ currentRoute }) => {
  const { profile } = useAuth();

  return (
    <header role="banner" className="site-header">
      <div className="header-container">
        <a href="#/diagnostics" className="brand-link" aria-label="Páramo Urbano - Inicio">
          <div className="brand-symbol" aria-hidden="true">PU</div>
          <div className="brand-title-group">
            <span className="brand-name">Páramo Urbano</span>
            <span className="brand-tagline">Donde el asfalto toca la cumbre</span>
          </div>
        </a>

        <nav aria-label="Navegación principal">
          <ul className="nav-menu" role="list">
            <li>
              <a
                href="#/onboarding"
                className={`nav-menu-link ${currentRoute.startsWith('/onboarding') ? 'active' : ''}`}
                aria-current={currentRoute.startsWith('/onboarding') ? 'page' : undefined}
              >
                Onboarding & Metas
              </a>
            </li>
            <li>
              <a
                href="#/diagnostics"
                className={`nav-menu-link ${currentRoute === '/diagnostics' ? 'active' : ''}`}
                aria-current={currentRoute === '/diagnostics' ? 'page' : undefined}
              >
                Diagnóstico Fisiológico
              </a>
            </li>
            <li>
              <a
                href="#/planner"
                className={`nav-menu-link ${currentRoute === '/planner' ? 'active' : ''}`}
                aria-current={currentRoute === '/planner' ? 'page' : undefined}
              >
                Planificador Periodizado
              </a>
            </li>
          </ul>
        </nav>

        <div className="athlete-badge" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span
            style={{
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              background: 'var(--bg-card)',
              padding: '0.25rem 0.65rem',
              borderRadius: 'var(--radius-pill)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            {profile.full_name} ({profile.experience_level})
          </span>
        </div>
      </div>
    </header>
  );
};
