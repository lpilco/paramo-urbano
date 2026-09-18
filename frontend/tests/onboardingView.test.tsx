/**
 * @fileoverview Unit tests for OnboardingView component: bifurcated screening and Profile B Gellish calculation.
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { OnboardingView } from '../src/views/onboarding/OnboardingView';

describe('OnboardingView Component (US-01 Bifurcated Screening)', () => {
  it('renders Profile A by default with dropzone for telemetry files', () => {
    render(<OnboardingView />);

    expect(screen.getByTestId('profile-a-section')).toBeInTheDocument();
    expect(screen.getByText(/Ingesta de Historial y Calibración Basal/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Zona de arrastre para archivos de telemetría/i)).toBeInTheDocument();
  });

  it('switches to Profile B (Beginner / Zero-GPS) displaying CaCo method and Gellish calculator', () => {
    render(<OnboardingView />);

    const profileBTab = screen.getByTestId('profile-b-tab');
    fireEvent.click(profileBTab);

    expect(screen.getByTestId('profile-b-section')).toBeInTheDocument();
    expect(screen.getByText(/¿Comienzas desde cero\? Tu camino seguro hacia la cumbre/i)).toBeInTheDocument();
    expect(screen.getByText(/1\. El Método CaCo \(Caminar \/ Correr\)/i)).toBeInTheDocument();
    expect(screen.getByText(/2\. Cuantificación Determinista sin Reloj: Escala Foster sRPE/i)).toBeInTheDocument();
  });

  it('dynamically computes Gellish max HR when age is modified (208 - 0.7 * 40 = 180 bpm)', () => {
    render(<OnboardingView />);

    const profileBTab = screen.getByTestId('profile-b-tab');
    fireEvent.click(profileBTab);

    const ageInput = screen.getByLabelText(/Edad \(años\):/i);
    fireEvent.change(ageInput, { target: { value: '40' } });

    // 208 - (0.7 * 40) = 208 - 28 = 180 bpm
    const maxHrDisplay = screen.getByTestId('gellish-max-hr');
    expect(maxHrDisplay).toHaveTextContent('180 bpm');
  });
});
