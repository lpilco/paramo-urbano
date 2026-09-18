/**
 * @fileoverview Main Application component and hash-based SPA router.
 * Routes:
 * - /#/onboarding -> OnboardingView (Bifurcated screening: Profile A GPS vs Profile B Zero-GPS)
 * - /#/onboarding/goals -> GoalsView (Parameterized goals with strict 14-day adaptation horizon)
 * - /#/diagnostics -> DiagnosticsView (Centered 680px layout without rookie cards per ADR-006)
 * - /#/planner -> PlannerView (Periodized plan: Daily, Weekly, Monthly views)
 * @module App
 */

import React, { useState, useEffect } from 'react';
import { Navbar } from './components/common/Navbar';
import { OnboardingView } from './views/onboarding/OnboardingView';
import { GoalsView } from './views/onboarding/GoalsView';
import { DiagnosticsView } from './views/diagnostics/DiagnosticsView';
import { PlannerView } from './views/planner/PlannerView';

export const App: React.FC = () => {
  const getRouteFromHash = (): string => {
    const hash = window.location.hash || '#/diagnostics';
    return hash.replace(/^#/, '');
  };

  const [route, setRoute] = useState<string>(getRouteFromHash());

  useEffect(() => {
    const handleHashChange = () => {
      setRoute(getRouteFromHash());
      window.scrollTo(0, 0);
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const renderCurrentView = () => {
    if (route.startsWith('/onboarding/goals')) {
      return <GoalsView />;
    }
    if (route.startsWith('/onboarding')) {
      return <OnboardingView />;
    }
    if (route.startsWith('/planner')) {
      return <PlannerView />;
    }
    return <DiagnosticsView />;
  };

  return (
    <div className="app-shell" data-testid="app-shell">
      <Navbar currentRoute={route} />

      {renderCurrentView()}

      <footer role="contentinfo" className="site-footer">
        <p>
          © 2026 <strong>Páramo Urbano (v2.0.0 Core)</strong> — Donde el asfalto toca la cumbre. Todos los derechos reservados.
        </p>
        <p style={{ fontSize: '0.75rem', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
          Periodización determinista y telemetría fisiológica • Reglas científicas Banister, Gabbett y Foster.
        </p>
      </footer>
    </div>
  );
};

export default App;
