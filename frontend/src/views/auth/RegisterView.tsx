/**
 * @fileoverview User Registration View for Páramo Urbano (v2.0.0 Core).
 * Simplified registration with full_name, email, and password.
 * Physiological telemetry (HR rest/max) is calibrated via Gellish formula or file ingestion.
 * @module views/auth/RegisterView
 */

import React, { useState } from 'react';
import { registerAthlete, mapAuthToProfile } from '../../api/authApi';
import { setProfile } from '../../store/authStore';
import { ApiError } from '../../api/apiClient';

export const RegisterView: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (password.length < 8) {
      setErrorMessage('La contraseña debe tener al menos 8 caracteres.');
      return;
    }

    if (fullName.trim().length < 2) {
      setErrorMessage('Por favor, ingresa tu nombre completo.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await registerAthlete({
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        password,
        age: 30,
        weight_kg: 70.0,
        experience_level: 'BEGINNER',
      });

      const userProfile = mapAuthToProfile(response);
      setProfile(userProfile);

      setSuccessMessage('¡Registro exitoso! Redirigiendo a tu onboarding fisiológico...');
      setTimeout(() => {
        window.location.hash = '#/onboarding';
      }, 500);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.detail || 'Error al registrar atleta en la plataforma.');
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
      <section style={{ maxWidth: '520px', margin: '0 auto' }}>
        <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-primary)' }}>
            Registro de Atleta
          </h1>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Únete a <strong>Páramo Urbano</strong> y calibra tu telemetría fisiológica
          </p>
        </header>

        <form onSubmit={handleSubmit} className="card" data-testid="register-form">
          {errorMessage && (
            <div
              className="alert-banner alert-banner-danger"
              role="alert"
              data-testid="register-error-banner"
              style={{ marginBottom: '1.25rem' }}
            >
              <span>⚠️ {errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div
              className="alert-banner alert-banner-success"
              role="alert"
              data-testid="register-success-banner"
              style={{ marginBottom: '1.25rem' }}
            >
              <span>✅ {successMessage}</span>
            </div>
          )}

          {/* Nombre Completo */}
          <div className="form-group">
            <label htmlFor="reg-fullname" className="form-label">
              Nombre Completo *
            </label>
            <input
              id="reg-fullname"
              type="text"
              className="form-input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Ej. Mateo Chimborazo"
              required
              data-testid="reg-fullname-input"
            />
          </div>

          {/* Correo Electrónico */}
          <div className="form-group">
            <label htmlFor="reg-email" className="form-label">
              Correo Electrónico *
            </label>
            <input
              id="reg-email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="atleta@paramourbano.app"
              required
              data-testid="reg-email-input"
            />
          </div>

          {/* Contraseña */}
          <div className="form-group">
            <label htmlFor="reg-password" className="form-label">
              Contraseña (mínimo 8 caracteres) *
            </label>
            <input
              id="reg-password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
              data-testid="reg-password-input"
            />
          </div>

          <div
            style={{
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              lineHeight: 1.4,
              marginBottom: '1rem',
              background: 'var(--bg-input)',
              padding: '0.65rem 0.85rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            💡 Tu Frecuencia Cardíaca Máxima se calculará automáticamente mediante el modelo fisiológico Gellish (208 - 0.7 × edad) y se calibrará con tus cargas de telemetría.
          </div>

          <footer style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <a href="#/login" style={{ fontSize: '0.85rem', color: 'var(--accent-glacier)', textDecoration: 'none' }}>
              ¿Ya tienes cuenta? Iniciar Sesión →
            </a>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
              data-testid="submit-register-btn"
            >
              {isSubmitting ? 'Registrando...' : 'Crear Cuenta e Iniciar →'}
            </button>
          </footer>
        </form>
      </section>
    </main>
  );
};
