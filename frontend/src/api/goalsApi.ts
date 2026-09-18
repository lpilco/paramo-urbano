/**
 * @fileoverview Athlete Goals API service.
 * @module api/goalsApi
 */

import { apiFetch } from './apiClient';
import type { CreateGoalRequest, GoalResponse } from '../types';

/**
 * Configure parameterized athletic training/competition goal enforcing 14-day adaptation horizon.
 *
 * @async
 * @param {CreateGoalRequest} payload
 * @returns {Promise<GoalResponse>}
 */
export async function createAthleteGoal(
  payload: CreateGoalRequest
): Promise<GoalResponse> {
  return apiFetch<GoalResponse>('/profiles/me/goals', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
