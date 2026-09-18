/**
 * @fileoverview Semantic global navigation header with interactive User Chip and session dropdown.
 * Complies with WCAG 2.1 AA and ADR-006 aesthetics.
 * @module components/common/Navbar
 */

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../store/authStore';

interface NavbarProps {
  currentRoute: string;
}

export const Navbar: React.FC<NavbarProps> = ({ currentRoute }) => {
  const { profile, isAuthenticated, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [isDropdownOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsDropdownOpen(false);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  const handleLogout = () => {
    setIsDropdownOpen(false);
    logout();
    window.location.hash = '#/login';
  };

  const getInitials = (name?: string, email?: string): string => {
    if (name && name.trim()) {
      const parts = name.trim().split(/\s+/);
      if (parts.length >= 2) {
        return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      }
      return parts[0].slice(0, 2).toUpperCase();
    }
    if (email) {
      return email.slice(0, 2).toUpperCase();
    }
    return 'PU';
  };

  const mapExperienceLevel = (level?: string): { label: string; color: string; bg: string } => {
    const l = (level || '').toUpperCase();
    if (l === 'BEGINNER' || l === 'INICIAL') {
      return { label: 'INICIAL', color: 'var(--accent-glacier)', bg: 'rgba(56, 189, 248, 0.15)' };
    }
    if (l === 'ADVANCED' || l === 'AVANZADO') {
      return { label: 'AVANZADO', color: 'var(--accent-summit)', bg: 'rgba(239, 68, 68, 0.15)' };
    }
    return { label: 'MEDIO', color: 'var(--accent-amber)', bg: 'rgba(245, 158, 11, 0.15)' };
  };

  const expInfo = mapExperienceLevel(profile?.experience_level);
  const initials = getInitials(profile?.full_name, profile?.email);

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

        {/* User Chip and Session Control */}
        <div className="athlete-badge" style={{ position: 'relative' }} ref={dropdownRef}>
          {profile && isAuthenticated ? (
            <div>
              <button
                type="button"
                className="user-chip-btn"
                onClick={() => setIsDropdownOpen((prev) => !prev)}
                aria-expanded={isDropdownOpen}
                aria-haspopup="true"
                data-testid="user-chip-button"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.65rem',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-strong)',
                  borderRadius: 'var(--radius-pill)',
                  padding: '0.35rem 0.85rem 0.35rem 0.45rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  color: 'var(--text-primary)',
                }}
              >
                {/* Avatar Initials Circle */}
                <span
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, var(--accent-glacier), var(--accent-summit))',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: '0.8rem',
                    letterSpacing: '0.5px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.25)',
                  }}
                  aria-hidden="true"
                >
                  {initials}
                </span>

                {/* Name and Level */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', lineHeight: 1.2 }}>
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {profile.full_name || profile.email}
                  </span>
                  <span
                    style={{
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      color: expInfo.color,
                      background: expInfo.bg,
                      padding: '0.1rem 0.4rem',
                      borderRadius: '4px',
                      marginTop: '0.15rem',
                      textTransform: 'uppercase',
                    }}
                  >
                    {expInfo.label}
                  </span>
                </div>

                {/* Chevron */}
                <span
                  style={{
                    fontSize: '0.7rem',
                    color: 'var(--text-muted)',
                    marginLeft: '0.2rem',
                    transform: isDropdownOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.2s ease',
                  }}
                  aria-hidden="true"
                >
                  ▼
                </span>
              </button>

              {/* Interactive Dropdown Menu */}
              {isDropdownOpen && (
                <div
                  className="card user-dropdown-menu"
                  role="menu"
                  data-testid="user-dropdown-menu"
                  style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    right: 0,
                    width: '260px',
                    padding: '0.85rem',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-strong)',
                    borderRadius: 'var(--radius-md)',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.4)',
                    zIndex: 1000,
                  }}
                >
                  {/* Active User Header */}
                  <div style={{ paddingBottom: '0.65rem', borderBottom: '1px solid var(--border-subtle)', marginBottom: '0.65rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                      Atleta Activo
                    </div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.15rem' }}>
                      {profile.full_name || 'Atleta Páramo'}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', marginTop: '0.1rem' }}>
                      {profile.email}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'monospace', marginTop: '0.3rem' }}>
                      ID: {profile.id.slice(0, 12)}...
                    </div>
                  </div>

                  {/* Menu Links */}
                  <ul role="list" style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    <li>
                      <a
                        href="#/onboarding/goals"
                        role="menuitem"
                        onClick={() => setIsDropdownOpen(false)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          padding: '0.45rem 0.65rem',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.82rem',
                          color: 'var(--text-primary)',
                          textDecoration: 'none',
                          background: 'var(--bg-input)',
                        }}
                      >
                        <span>⛰️</span>
                        <span>Configurar Metas Deportivas</span>
                      </a>
                    </li>
                  </ul>

                  {/* Logout Button */}
                  <div style={{ borderTop: '1px solid var(--border-subtle)', marginTop: '0.65rem', paddingTop: '0.65rem' }}>
                    <button
                      type="button"
                      role="menuitem"
                      onClick={handleLogout}
                      data-testid="logout-btn"
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        padding: '0.45rem 0.75rem',
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        color: 'var(--acwr-danger)',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.25)',
                        borderRadius: 'var(--radius-sm)',
                        cursor: 'pointer',
                        transition: 'background 0.2s ease',
                      }}
                    >
                      <span>🚪</span>
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <a
                href="#/login"
                className="btn btn-secondary"
                style={{ padding: '0.3rem 0.75rem', fontSize: '0.8rem' }}
                data-testid="nav-login-btn"
              >
                Iniciar Sesión
              </a>
              <a
                href="#/register"
                className="btn btn-primary"
                style={{ padding: '0.3rem 0.75rem', fontSize: '0.8rem' }}
                data-testid="nav-register-btn"
              >
                + Registro
              </a>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
