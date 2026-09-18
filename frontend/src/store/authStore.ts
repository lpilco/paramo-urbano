/**
 * @fileoverview Lightweight reactive session and auth state manager.
 * @module store/authStore
 */

import { useState, useEffect } from 'react';
import type { UserProfile } from '../types';
import { getStoredToken, clearStoredToken } from '../api/apiClient';

const PROFILE_KEY = 'paramo_user_profile';

const DEFAULT_PROFILE: UserProfile = {
  id: 'usr_default_athlete',
  email: 'atleta.cumbre@paramourbano.app',
  full_name: 'Mateo Chimborazo',
  athlete_profile_id: 'prof_default_001',
  experience_level: 'INTERMEDIATE',
  age: 32,
  weight_kg: 68.5,
};

let currentProfile: UserProfile = (() => {
  const saved = localStorage.getItem(PROFILE_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch {
      // ignore
    }
  }
  return DEFAULT_PROFILE;
})();

const listeners = new Set<(profile: UserProfile) => void>();

export function getProfile(): UserProfile {
  return currentProfile;
}

export function setProfile(profile: UserProfile): void {
  currentProfile = profile;
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  listeners.forEach((fn) => fn(profile));
}

export function resetProfile(): void {
  currentProfile = DEFAULT_PROFILE;
  localStorage.removeItem(PROFILE_KEY);
  clearStoredToken();
  listeners.forEach((fn) => fn(currentProfile));
}

export function useAuth(): { profile: UserProfile; isAuthenticated: boolean; updateProfile: (p: UserProfile) => void; logout: () => void } {
  const [profile, setLocalProfile] = useState<UserProfile>(currentProfile);

  useEffect(() => {
    listeners.add(setLocalProfile);
    return () => {
      listeners.delete(setLocalProfile);
    };
  }, []);

  return {
    profile,
    isAuthenticated: Boolean(getStoredToken() || profile),
    updateProfile: setProfile,
    logout: resetProfile,
  };
}
