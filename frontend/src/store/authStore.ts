/**
 * @fileoverview Lightweight reactive session and auth state manager.
 * Strictly enforces multi-user tenant isolation, zero singleton mocks,
 * and complete session purge on logout.
 * @module store/authStore
 */

import { useState, useEffect } from 'react';
import type { UserProfile } from '../types';
import { getStoredToken, clearStoredToken } from '../api/apiClient';

const PROFILE_KEY = 'paramo_user_profile';

let currentProfile: UserProfile | null = (() => {
  const token = getStoredToken();
  if (!token) {
    localStorage.removeItem(PROFILE_KEY);
    return null;
  }
  const saved = localStorage.getItem(PROFILE_KEY);
  if (saved) {
    try {
      return JSON.parse(saved) as UserProfile;
    } catch {
      localStorage.removeItem(PROFILE_KEY);
    }
  }
  return null;
})();

const listeners = new Set<(profile: UserProfile | null) => void>();

/**
 * Retrieve active in-memory user profile.
 * @returns {UserProfile | null}
 */
export function getProfile(): UserProfile | null {
  return currentProfile;
}

/**
 * Persist and propagate active user profile.
 * @param {UserProfile | null} profile
 */
export function setProfile(profile: UserProfile | null): void {
  currentProfile = profile;
  if (profile) {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } else {
    localStorage.removeItem(PROFILE_KEY);
  }
  listeners.forEach((fn) => fn(profile));
}

/**
 * Completely purge active session, tokens, and profile data from local storage.
 */
export function resetProfile(): void {
  currentProfile = null;
  localStorage.removeItem(PROFILE_KEY);
  localStorage.removeItem('access_token');
  localStorage.removeItem('paramo_access_token');
  clearStoredToken();
  listeners.forEach((fn) => fn(null));
}

/**
 * React hook for consuming reactive auth session state.
 */
export function useAuth(): {
  profile: UserProfile | null;
  isAuthenticated: boolean;
  updateProfile: (p: UserProfile | null) => void;
  logout: () => void;
} {
  const [profile, setLocalProfile] = useState<UserProfile | null>(currentProfile);

  useEffect(() => {
    listeners.add(setLocalProfile);
    return () => {
      listeners.delete(setLocalProfile);
    };
  }, []);

  const hasToken = Boolean(getStoredToken() || localStorage.getItem('access_token'));
  const isAuthenticated = Boolean(hasToken && profile);

  return {
    profile,
    isAuthenticated,
    updateProfile: setProfile,
    logout: resetProfile,
  };
}
