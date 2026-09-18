/**
 * @fileoverview Periodized Training Plans API service.
 * @module api/plansApi
 */

import { apiFetch } from './apiClient';
import type { PeriodizedPlan, PlanViewGranularity } from '../types';

/**
 * Retrieve periodized training plan with daily, weekly, or monthly granularity.
 *
 * @async
 * @param {PlanViewGranularity} [view='WEEKLY']
 * @returns {Promise<PeriodizedPlan>}
 */
export async function getCurrentTrainingPlan(
  view: PlanViewGranularity = 'WEEKLY'
): Promise<PeriodizedPlan> {
  return apiFetch<PeriodizedPlan>(`/plans/current?view=${encodeURIComponent(view)}`);
}
