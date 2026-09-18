/**
 * @fileoverview User Login View for Páramo Urbano (v2.0.0 Core).
 * Enables multi-user authentication, JWT issuance, and session state initialization.
 * @module views/auth/LoginView
 */

import React, { useState } from 'react';
import { loginAthlete, mapAuthToProfile } from '../../api/authApi';
import { setProfile } from '../../store/authStore';
import { ApiError } from '../../api/apiClient';

export const LoginView: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim() || !password) {
      setErrorMessage('Por favor, ingresa tu correo electrónico y contraseña.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await loginAthlete({
        email: email.trim().toLowerCase(),
        password,
      });

      const userProfile = mapAuthToProfile(response);
      setProfile(userProfile);

      // Smooth navigation to diagnostics
      window.location.hash = '#/diagnostics';
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail || 'Credenciales inválidas. Verifica tu correo y contraseña.');
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
      <section style={{ maxWidth: '460px', margin: '0 auto' }}>
        <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Iniciar Sesión
          </h1>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Accede a tu telemetría y periodización en <strong>Páramo Urbano</strong>
          </p>
        </header>

        <form onSubmit={handleSubmit} className="card" data-testid="login-form">
          {errorMessage && (
            <div
              className="alert-banner alert-banner-danger"
              role="alert"
              data-testid="login-error-banner"
              style={{ marginBottom: '1.25rem' }}
            >
              <span>⚠️ {errorMessage}</span>
            </div>
          )}

          {/* Correo Electrónico */}
          <div className="form-group">
            <label htmlFor="login-email" className="form-label">
              Correo Electrónico *
            </label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="atleta@paramourbano.app"
              required
              data-testid="login-email-input"
            />
          </div>

          {/* Contraseña */}
          <div className="form-group">
            <label htmlFor="login-password" className="form-label">
              Contraseña *
            </label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              data-testid="login-password-input"
            />
          </div>

          <footer style={{ marginTop: '1.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <a href="#/register" style={{ fontSize: '0.85rem', color: 'var(--accent-glacier)', textDecoration: 'none' }}>
              ¿Nuevo atleta? Crear cuenta →
            </a>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
              data-testid="submit-login-btn"
            >
              {isSubmitting ? 'Ingresando...' : 'Iniciar Sesión →'}
            </button>
          </footer>
        </form>
      </section>
    </main>
  );
};
