/**
 * @fileoverview Unit tests for DropzoneUpload component: in-memory SHA-256 and upload handling.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DropzoneUpload, computeFileSha256 } from '../src/components/upload/DropzoneUpload';
import * as activitiesApi from '../src/api/activitiesApi';
import { ApiError } from '../src/api/apiClient';

describe('DropzoneUpload Component (Web Crypto SHA-256 & Async Ingestion)', () => {
  it('computes valid SHA-256 hex string in memory using browser crypto API', async () => {
    const fileContent = 'sample telemetry binary content';
    const blob = new Blob([fileContent], { type: 'application/octet-stream' });
    const file = new File([blob], 'test_run.fit', { type: 'application/octet-stream' });

    const sha256 = await computeFileSha256(file);

    // SHA-256 should be a 64-character hex string
    expect(sha256).toMatch(/^[a-f0-9]{64}$/);
  });

  it('handles duplicate file rejection (HTTP 409) with friendly message', async () => {
    const uploadSpy = vi.spyOn(activitiesApi, 'uploadActivityFile').mockRejectedValue(
      new ApiError(409, 'Duplicate file detected', {
        title: 'Conflicto de Duplicidad',
        status: 409,
        detail: 'Archivo previamente procesado.',
        code: 'DUPLICATE_ACTIVITY',
      })
    );

    const onError = vi.fn();

    render(<DropzoneUpload onUploadError={onError} />);

    const input = document.getElementById('telemetry-file-input') as HTMLInputElement;

    const file = new File(['content'], 'duplicado.fit', { type: 'application/octet-stream' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(uploadSpy).toHaveBeenCalled();
      expect(screen.getByText(/Archivo duplicado/i)).toBeInTheDocument();
    });

    uploadSpy.mockRestore();
  });

  it('rejects files larger than 25 MB with an immediate validation error', async () => {
    const onError = vi.fn();
    render(<DropzoneUpload onUploadError={onError} />);

    const input = document.getElementById('telemetry-file-input') as HTMLInputElement;

    // Create a mock large file > 25MB
    const largeFile = new File(['x'], 'huge_activity.fit', { type: 'application/octet-stream' });
    Object.defineProperty(largeFile, 'size', { value: 26 * 1024 * 1024 });

    fireEvent.change(input, { target: { files: [largeFile] } });

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(
        expect.stringContaining('supera el límite máximo de 25 MB')
      );
    });
  });
});
