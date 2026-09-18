/**
 * @fileoverview Typed HTTP client with Bearer JWT injection and RFC 7807 error parsing.
 * @module api/apiClient
 */

import type { ProblemDetails } from '../types';

/**
 * Standardized API Error class encapsulating RFC 7807 problem details.
 */
export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly title: string;
  public readonly detail: string;
  public readonly problem: ProblemDetails | null;

  constructor(status: number, message: string, problem: ProblemDetails | null = null) {
    super(problem?.detail || message);
    this.name = 'ApiError';
    this.status = status;
    this.code = problem?.code || 'HTTP_ERROR';
    this.title = problem?.title || 'Error de Comunicación';
    this.detail = problem?.detail || message;
    this.problem = problem;
  }
}

const API_BASE_URL = '/api/v1';
const TOKEN_STORAGE_KEY = 'paramo_access_token';

/**
 * Get the stored JWT access token.
 * @returns {string | null}
 */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

/**
 * Persist JWT access token in browser storage.
 * @param {string} token
 */
export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

/**
 * Clear persisted JWT access token.
 */
export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

/**
 * Performs an authenticated HTTP request with JSON error parsing.
 *
 * @async
 * @template T
 * @param {string} endpoint - API endpoint relative to base (e.g. '/diagnostics')
 * @param {RequestInit} [options={}] - Fetch configuration options
 * @returns {Promise<T>} Parsed JSON response payload
 * @throws {ApiError} If HTTP response status is not ok (4xx, 5xx)
 */
export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const token = getStoredToken();

  const headers = new Headers(options.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Set Accept header by default
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // Only set Content-Type to JSON if body is not FormData
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let problem: ProblemDetails | null = null;
    let fallbackText = `Error HTTP ${response.status}: ${response.statusText}`;

    try {
      const errorJson = await response.json();
      problem = errorJson as ProblemDetails;
      if (problem.detail) {
        fallbackText = problem.detail;
      }
    } catch {
      // Body wasn't JSON
    }

    throw new ApiError(response.status, fallbackText, problem);
  }

  // Return empty object for 204 or empty response
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
