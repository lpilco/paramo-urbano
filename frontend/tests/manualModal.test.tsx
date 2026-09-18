/**
 * @fileoverview Unit tests for ManualActivityModal component: Foster sRPE calculation and range validation.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ManualActivityModal } from '../src/components/modals/ManualActivityModal';
import * as activitiesApi from '../src/api/activitiesApi';

describe('ManualActivityModal Component (Foster sRPE Logging)', () => {
  it('calculates Foster training load dynamically in real time (50 min * 8 RPE = 400 u.a.)', () => {
    render(<ManualActivityModal isOpen={true} onClose={() => {}} />);

    const durationInput = screen.getByLabelText(/Duración \(minutos\)/i);
    const rpeInput = screen.getByLabelText(/Entrada numérica de RPE/i);

    fireEvent.change(durationInput, { target: { value: '50' } });
    fireEvent.change(rpeInput, { target: { value: '8' } });

    // Verify dynamic calculation
    const calculatedLoad = screen.getByTestId('calculated-foster-load');
    expect(calculatedLoad).toHaveTextContent('400 u.a.');
  });

  it('updates load dynamically when duration and RPE change (30 min * 4 RPE = 120 u.a.)', () => {
    render(<ManualActivityModal isOpen={true} onClose={() => {}} />);

    const durationInput = screen.getByLabelText(/Duración \(minutos\)/i);
    const rpeInput = screen.getByLabelText(/Entrada numérica de RPE/i);

    fireEvent.change(durationInput, { target: { value: '30' } });
    fireEvent.change(rpeInput, { target: { value: '4' } });

    const calculatedLoad = screen.getByTestId('calculated-foster-load');
    expect(calculatedLoad).toHaveTextContent('120 u.a.');
  });

  it('blocks submission and shows error if RPE is outside the 1 to 10 range', async () => {
    const logManualSpy = vi.spyOn(activitiesApi, 'logManualActivity');

    render(<ManualActivityModal isOpen={true} onClose={() => {}} />);

    const rpeInput = screen.getByLabelText(/Entrada numérica de RPE/i);
    const submitBtn = screen.getByTestId('submit-manual-btn');

    // Enter out of bound RPE
    fireEvent.change(rpeInput, { target: { value: '12' } });

    // Submit button should be disabled
    expect(submitBtn).toBeDisabled();

    // Directly trigger form submit
    const form = submitBtn.closest('form')!;
    fireEvent.submit(form);

    expect(
      screen.getByText(/El RPE debe ser un número entero comprendido entre 1 y 10/i)
    ).toBeInTheDocument();
    expect(logManualSpy).not.toHaveBeenCalled();

    logManualSpy.mockRestore();
  });

  it('submits valid data successfully to the activities API and invokes callback', async () => {
    const mockCreated = {
      activity_id: 'act_test_999',
      sport_category: 'STRENGTH',
      started_at: '2026-09-17T07:00:00.000Z',
      duration_minutes: 50,
      session_rpe: 8,
      calculated_load: 400.0,
      notes: 'Test session',
    };

    const logManualSpy = vi.spyOn(activitiesApi, 'logManualActivity').mockResolvedValue(mockCreated);
    const onSuccess = vi.fn();
    const onClose = vi.fn();

    render(
      <ManualActivityModal
        isOpen={true}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    const submitBtn = screen.getByTestId('submit-manual-btn');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(logManualSpy).toHaveBeenCalled();
      expect(onSuccess).toHaveBeenCalledWith(mockCreated);
      expect(onClose).toHaveBeenCalled();
    });

    logManualSpy.mockRestore();
  });
});
