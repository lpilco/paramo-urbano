/**
 * @fileoverview Unit tests for GoalsView component: strict 14-day date validation and disciplines.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GoalsView } from '../src/views/onboarding/GoalsView';
import * as goalsApi from '../src/api/goalsApi';

describe('GoalsView Component (FR-05: Strict 14-Day Adaptation Horizon)', () => {
  it('enforces min attribute on date picker to be at least 14 days into the future', () => {
    render(<GoalsView />);

    const dateInput = screen.getByTestId('target-date-input') as HTMLInputElement;

    // Minimum expected date is today + 14 days
    const minExpected = new Date();
    minExpected.setDate(minExpected.getDate() + 14);
    const minExpectedStr = minExpected.toISOString().split('T')[0];

    expect(dateInput.getAttribute('min')).toBe(minExpectedStr);
  });

  it('blocks submission and displays canonical error if target date is within 14 days', async () => {
    const createGoalSpy = vi.spyOn(goalsApi, 'createAthleteGoal').mockResolvedValue({
      goal_id: 'goal_test_123',
      athlete_profile_id: 'prof_123',
      discipline: 'ROAD_RUNNING',
      subgoal_type: 'HALF_MARATHON',
      target_distance_km: 21.097,
      target_elevation_gain_m: 0,
      target_date: '2026-09-20',
      available_days_per_week: 5,
      days_to_target: 3,
      weeks_to_target: 0,
      created_at: new Date().toISOString(),
    });

    render(<GoalsView />);

    const dateInput = screen.getByTestId('target-date-input');
    const submitBtn = screen.getByTestId('submit-goal-btn');

    // Attempt to set a date only 5 days in the future
    const tooSoonDate = new Date();
    tooSoonDate.setDate(tooSoonDate.getDate() + 5);
    const tooSoonStr = tooSoonDate.toISOString().split('T')[0];

    fireEvent.change(dateInput, { target: { value: tooSoonStr } });

    // Submit button should be disabled because isDateCompliant is false
    expect(submitBtn).toBeDisabled();

    // Even if form submit event is triggered directly
    const form = screen.getByTestId('goals-form');
    fireEvent.submit(form);

    // Should display canonical FR-05 error message
    expect(
      screen.getByText(
        /La fecha objetivo debe programarse con al menos 14 días de antelación para permitir una adaptación biológica mínima/i
      )
    ).toBeInTheDocument();

    expect(createGoalSpy).not.toHaveBeenCalled();
    createGoalSpy.mockRestore();
  });

  it('requires positive elevation gain (+D) when Trail Running is selected', () => {
    render(<GoalsView />);

    const trailBtn = screen.getByTestId('disc-trail-btn');
    fireEvent.click(trailBtn);

    // Check that elevation input is displayed and has required attribute
    const elevationInput = screen.getByTestId('goal-elevation-input');
    expect(elevationInput).toBeInTheDocument();
    expect(elevationInput).toBeRequired();
  });

  it('displays hypoxia warning when selecting Media or Alta Montaña in Trekking', () => {
    render(<GoalsView />);

    const trekkingBtn = screen.getByTestId('disc-trekking-btn');
    fireEvent.click(trekkingBtn);

    const select = screen.getByTestId('altitude-category-select');
    fireEvent.change(select, { target: { value: 'ALTA_MONTANA' } });

    expect(screen.getByTestId('hypoxia-warning')).toBeInTheDocument();
    expect(
      screen.getByText(/Por encima de los 3.500 metros, la presión parcial de oxígeno se reduce/i)
    ).toBeInTheDocument();
  });
});
