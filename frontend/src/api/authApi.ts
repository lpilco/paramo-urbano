/**
 * @fileoverview Authentication and Athlete registration API services.
 * @module api/authApi
 */

import { apiFetch, setStoredToken, clearStoredToken } from './apiClient';
import type { UserProfile } from '../types';

export interface AuthResponse {
  access_token: string;
  token_type: string;
  refresh_token?: string;
  user: {
    id: string;
    email: string;
  };
  profile: {
    id: string;
    full_name: string;
    experience_level: string;
    age?: number;
    weight_kg?: number;
  };
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  age: number;
  weight_kg: number;
  experience_level?: string;
  rest_hr?: number;
  max_hr?: number;
}

export interface LoginPayload {
  email: string;
  password: string;
}

/**
 * Register a new athlete and initialize biometric profile.
 *
 * @async
 * @param {RegisterPayload} payload
 * @returns {Promise<AuthResponse>}
 */
export async function registerAthlete(payload: RegisterPayload): Promise<AuthResponse> {
  const response = await apiFetch<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  setStoredToken(response.access_token);
  return response;
}

/**
 * Authenticate existing athlete and receive JWT.
 *
 * @async
 * @param {LoginPayload} payload
 * @returns {Promise<AuthResponse>}
 */
export async function loginAthlete(payload: LoginPayload): Promise<AuthResponse> {
  const response = await apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  setStoredToken(response.access_token);
  return response;
}

/**
 * Sign out and clear stored session.
 */
export function logoutAthlete(): void {
  clearStoredToken();
}

/**
 * Build UserProfile model from auth response.
 * @param {AuthResponse} res
 * @returns {UserProfile}
 */
export function mapAuthToProfile(res: AuthResponse): UserProfile {
  return {
    id: res.user.id,
    email: res.user.email,
    full_name: res.profile.full_name,
    athlete_profile_id: res.profile.id,
    experience_level: res.profile.experience_level,
    age: res.profile.age,
    weight_kg: res.profile.weight_kg,
  };
}
