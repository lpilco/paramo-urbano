/**
 * @fileoverview Activities API service: multipart upload, manual sRPE logging and paginated listing.
 * @module api/activitiesApi
 */

import { apiFetch } from './apiClient';
import type {
  BatchManualActivitiesRequest,
  BatchManualActivitiesResponse,
  JobStatusResponse,
  ManualActivityRequest,
  ManualActivityResponse,
  PaginatedActivitiesResponse,
  UploadActivityResponse,
} from '../types';

/**
 * Upload raw telemetry file (.FIT, .GPX, .CSV, .JSON) asynchronously.
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
 * Query status of an asynchronous telemetry ingestion job.
 *
 * @async
 * @param {string} jobId - Unique job identifier
 * @returns {Promise<JobStatusResponse>} Current ingestion status and progress
 */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  return apiFetch<JobStatusResponse>(`/activities/jobs/${encodeURIComponent(jobId)}`);
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
 * Log a batch of manual workout sessions atomically.
 *
 * @async
 * @param {ManualActivityRequest[]} items
 * @returns {Promise<BatchManualActivitiesResponse>}
 */
export async function logBatchManualActivities(
  items: ManualActivityRequest[]
): Promise<BatchManualActivitiesResponse> {
  const payload: BatchManualActivitiesRequest = { items };
  return apiFetch<BatchManualActivitiesResponse>('/activities/manual/batch', {
    method: 'POST',
    body: JSON.stringify(payload),
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
