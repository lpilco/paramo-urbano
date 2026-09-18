/**
 * @fileoverview Diagnostics API service: Banister EWMA workload curves and Gabbett ACWR.
 * @module api/diagnosticsApi
 */

import { apiFetch } from './apiClient';
import type { AthleteDiagnostics } from '../types';

/**
 * Fetch consolidated physiological diagnostics for the authenticated athlete.
 *
 * @async
 * @returns {Promise<AthleteDiagnostics>} Fitness (CTL), Fatigue (ATL), Form (TSB), and ACWR
 */
export async function getAthleteDiagnostics(): Promise<AthleteDiagnostics> {
  return apiFetch<AthleteDiagnostics>('/diagnostics');
}
