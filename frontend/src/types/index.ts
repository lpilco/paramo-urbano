/**
 * @fileoverview Canonical TypeScript interfaces and domain models for Páramo Urbano.
 * Aligned with docs/DATA_SCHEMA.md and Backend DTOs.
 * @module types
 */

export type SportCategory = 'ROAD_RUN' | 'TRAIL_RUN' | 'HIKE' | 'STRENGTH';

export type ActivitySource = 'FIT' | 'GPX' | 'CSV' | 'MANUAL';

export type Discipline = 'ROAD_RUNNING' | 'TRAIL_RUNNING' | 'TREKKING';

export type ACWRZone = 'SWEET_SPOT' | 'WARNING' | 'DANGER' | string;

export type PlanViewGranularity = 'DAILY' | 'WEEKLY' | 'MONTHLY';

/** Activity upload response (HTTP 202 Accepted) */
export interface UploadActivityResponse {
  job_id: string;
  file_name: string;
  sha256: string;
  status: 'QUEUED' | 'PROCESSED' | 'FAILED' | string;
}

/** Request payload for manual non-GPS activity */
export interface ManualActivityRequest {
  sport_category: SportCategory | string;
  started_at: string;
  duration_minutes: number;
  session_rpe: number;
  notes?: string;
  distance_km?: number;
  elevation_gain_m?: number;
}

/** Response returned after persisting manual activity (HTTP 201 Created) */
export interface ManualActivityResponse {
  activity_id: string;
  sport_category: string;
  started_at: string;
  duration_minutes: number;
  session_rpe: number;
  calculated_load: number;
  notes: string;
}

/** Summary item in paginated activities list */
export interface ActivitySummary {
  id: string;
  sport_category: string;
  source_type: string;
  started_at: string;
  duration_minutes: number;
  distance_km: number;
  elevation_gain_m: number;
  session_rpe?: number | null;
  calculated_load?: number | null;
  tss_score?: number | null;
  processing_status: string;
  notes: string;
}

/** Paginated response wrapper for activities */
export interface PaginatedActivitiesResponse {
  items: ActivitySummary[];
  total: number;
  page: number;
  limit: number;
}

/** Banister Impulse-Response EWMA metrics */
export interface BanisterMetrics {
  ctl: number;
  atl: number;
  tsb: number;
  is_critical_fatigue: boolean;
}

/** Tim Gabbett Acute:Chronic Workload Ratio metrics */
export interface ACWRMetrics {
  ratio: number;
  zone: ACWRZone;
  requires_mandatory_rest: boolean;
  freeze_weekly_increments: boolean;
  recommendation: string;
}

/** Consolidated physiological diagnostics for athlete */
export interface AthleteDiagnostics {
  athlete_profile_id: string;
  banister: BanisterMetrics;
  acwr: ACWRMetrics;
  weekly_total_load: number;
  weekly_duration_minutes: number;
  days_evaluated: number;
}

/** Request payload for configuring an athletic goal */
export interface CreateGoalRequest {
  discipline: Discipline | string;
  subgoal_type: string;
  target_distance_km: number;
  target_elevation_gain_m?: number;
  target_date: string;
  available_days_per_week?: number;
  mountain_altitude_category?: string | null;
}

/** Persisted athletic goal response */
export interface GoalResponse {
  goal_id: string;
  athlete_profile_id: string;
  discipline: string;
  subgoal_type: string;
  target_distance_km: number;
  target_elevation_gain_m: number;
  target_date: string;
  available_days_per_week: number;
  days_to_target: number;
  weeks_to_target: number;
  created_at: string;
}

/** Session contextual nutrition prescription */
export interface NutritionPrescription {
  strategy: string;
  protein_g_kg: string;
  carbs_g_kg: string;
  hydration_guidelines: string;
}

/** Physical discharge and recovery prescription */
export interface RecoveryTherapy {
  therapy_name: string;
  protocol: string;
}

/** Individual scheduled workout session */
export interface WorkoutSession {
  day_of_week: number;
  day_name: string;
  is_rest_day: boolean;
  session_category: string;
  duration_min: number;
  target_distance_km: number;
  target_elevation_gain_m: number;
  nutrition: NutritionPrescription;
  recovery: RecoveryTherapy;
}

/** 7-day microcycle within periodized plan */
export interface Microcycle {
  week_number: number;
  phase: 'BASE' | 'BUILD' | 'PEAK' | 'TAPER' | string;
  target_volume_hours: number;
  target_load: number;
  weekly_progression_pct: number;
  sessions: WorkoutSession[];
}

/** Periodized training plan response */
export interface PeriodizedPlan {
  plan_id: string;
  athlete_profile_id: string;
  view: PlanViewGranularity;
  active_goal_discipline?: string | null;
  target_date?: string | null;
  microcycles: Microcycle[];
}

/** RFC 7807 Problem Details for HTTP errors */
export interface ProblemDetails {
  type?: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  code?: string;
  extra?: Record<string, unknown>;
}

/** Authenticated user profile */
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  athlete_profile_id: string;
  experience_level: string;
  age?: number;
  weight_kg?: number;
}
