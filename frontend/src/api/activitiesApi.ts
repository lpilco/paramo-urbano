/**
 * @fileoverview Activities API service: multipart upload, manual sRPE logging and paginated listing.
 * @module api/activitiesApi
 */

import { apiFetch } from './apiClient';
import type {
  ManualActivityRequest,
  ManualActivityResponse,
  PaginatedActivitiesResponse,
  UploadActivityResponse,
} from '../types';

/**
 * Upload raw telemetry file (.FIT, .GPX, .CSV) asynchronously.
 *
 * @async
 * @param {File} file - Telemetry file to upload (max 25MB)
 * @returns {Promise<UploadActivityResponse>} Enqueued job details (HTTP 202)
 */
export async function uploadActivityFile(file: File): Promise<UploadActivityResponse> {
  const formData = new FormData();
  formData.append('file', file, file.name);

  return apiFetch<UploadActivityResponse>('/activities/upload', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Log manual workout session using deterministic Foster sRPE.
 *
 * @async
 * @param {ManualActivityRequest} data
 * @returns {Promise<ManualActivityResponse>} Persisted manual activity (HTTP 201)
 */
export async function logManualActivity(
  data: ManualActivityRequest
): Promise<ManualActivityResponse> {
  return apiFetch<ManualActivityResponse>('/activities/manual', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Query paginated chronological activities for authenticated athlete.
 *
 * @async
 * @param {number} [page=1] - Page number (1-indexed)
 * @param {number} [limit=20] - Number of items per page
 * @returns {Promise<PaginatedActivitiesResponse>}
 */
export async function listActivities(
  page = 1,
  limit = 20
): Promise<PaginatedActivitiesResponse> {
  return apiFetch<PaginatedActivitiesResponse>(
    `/activities?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(limit)}`
  );
}
