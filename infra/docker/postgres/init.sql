-- ==============================================================================
-- PÁRAMO URBANO (v2.0.0 Core) — DDL de Inicialización PostgreSQL 16
-- ==============================================================================

-- 1. Extensiones del Sistema
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Función genérica para actualización de timestamps (updated_at)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Tabla: USERS
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 4. Tabla: ATHLETE_PROFILES
CREATE TABLE IF NOT EXISTS athlete_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    experience_level VARCHAR(32) NOT NULL CHECK (
        experience_level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'INICIAL', 'MEDIO', 'AVANZADO')
    ),
    age INT NOT NULL CHECK (age >= 10 AND age <= 100),
    weight_kg NUMERIC(5, 2) NOT NULL CHECK (weight_kg >= 30.0 AND weight_kg <= 250.0),
    rest_hr INT CHECK (rest_hr IS NULL OR (rest_hr >= 30 AND rest_hr <= 240)),
    max_hr INT CHECK (max_hr IS NULL OR (max_hr >= 30 AND max_hr <= 240)),
    vdot_score NUMERIC(4, 1) CHECK (vdot_score IS NULL OR (vdot_score >= 15.0 AND vdot_score <= 85.0)),
    current_ctl NUMERIC(6, 2) NOT NULL DEFAULT 0.0 CHECK (current_ctl >= 0.0),
    current_atl NUMERIC(6, 2) NOT NULL DEFAULT 0.0 CHECK (current_atl >= 0.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_hr_profile_validity CHECK (rest_hr IS NULL OR max_hr IS NULL OR rest_hr < max_hr)
);

CREATE TRIGGER trg_athlete_profiles_updated_at
BEFORE UPDATE ON athlete_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 5. Tabla: GOALS
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_profile_id UUID NOT NULL REFERENCES athlete_profiles(id) ON DELETE CASCADE,
    discipline VARCHAR(32) NOT NULL CHECK (discipline IN ('ROAD_RUNNING', 'TRAIL_RUNNING', 'TREKKING')),
    subgoal_type VARCHAR(64) NOT NULL,
    custom_distance_km NUMERIC(7, 3) NOT NULL CHECK (custom_distance_km > 0),
    target_elevation_gain_m NUMERIC(7, 1) NOT NULL DEFAULT 0.0 CHECK (target_elevation_gain_m >= 0.0),
    mountain_altitude_category VARCHAR(64),
    target_date DATE NOT NULL,
    available_days_per_week INT NOT NULL DEFAULT 5 CHECK (available_days_per_week >= 1 AND available_days_per_week <= 7),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_goals_athlete_active ON goals (athlete_profile_id, is_active);

CREATE TRIGGER trg_goals_updated_at
BEFORE UPDATE ON goals
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 6. Tabla: ACTIVITIES
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_profile_id UUID NOT NULL REFERENCES athlete_profiles(id) ON DELETE CASCADE,
    source_type VARCHAR(32) NOT NULL CHECK (
        source_type IN ('FIT', 'CSV', 'GPX', 'JSON', 'MANUAL', 'FILE_FIT', 'FILE_CSV', 'FILE_GPX', 'FILE_JSON')
    ),
    file_storage_key VARCHAR(512),
    file_hash_sha256 VARCHAR(64),
    sport_category VARCHAR(32) NOT NULL CHECK (
        sport_category IN ('ROAD_RUN', 'TRAIL_RUN', 'HIKE', 'STRENGTH')
    ),
    started_at TIMESTAMPTZ NOT NULL,
    duration_seconds INT NOT NULL CHECK (duration_seconds > 0),
    distance_meters NUMERIC(10, 2) NOT NULL DEFAULT 0.0 CHECK (distance_meters >= 0.0),
    elevation_gain_meters NUMERIC(8, 2) NOT NULL DEFAULT 0.0 CHECK (elevation_gain_meters >= 0.0),
    tss_score NUMERIC(6, 2) CHECK (tss_score IS NULL OR tss_score >= 0.0),
    session_rpe INT CHECK (session_rpe IS NULL OR (session_rpe >= 1 AND session_rpe <= 10)),
    foster_load NUMERIC(8, 2) CHECK (foster_load IS NULL OR foster_load >= 0.0),
    processing_status VARCHAR(32) NOT NULL DEFAULT 'PROCESSED' CHECK (
        processing_status IN ('QUEUED', 'PROCESSING', 'PROCESSED', 'COMPLETED', 'FAILED', 'PENDING')
    ),
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Deduplicación criptográfica estricta: sólo hashes no nulos son únicos
CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_file_hash_sha256 
ON activities (file_hash_sha256) 
WHERE file_hash_sha256 IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_activities_athlete_started 
ON activities (athlete_profile_id, started_at DESC);

CREATE TRIGGER trg_activities_updated_at
BEFORE UPDATE ON activities
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 7. Tabla: ACTIVITY_TELEMETRY_SUMMARY
CREATE TABLE IF NOT EXISTS activity_telemetry_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID NOT NULL UNIQUE REFERENCES activities(id) ON DELETE CASCADE,
    avg_hr INT CHECK (avg_hr IS NULL OR (avg_hr >= 30 AND avg_hr <= 240)),
    max_hr INT CHECK (max_hr IS NULL OR (max_hr >= 30 AND max_hr <= 240)),
    avg_speed_ms NUMERIC(5, 2) CHECK (avg_speed_ms IS NULL OR (avg_speed_ms >= 0.0 AND avg_speed_ms <= 15.0)),
    max_speed_ms NUMERIC(5, 2) CHECK (max_speed_ms IS NULL OR (max_speed_ms >= 0.0 AND max_speed_ms <= 25.0)),
    avg_vam_vertical_speed_mh NUMERIC(7, 1) CHECK (avg_vam_vertical_speed_mh IS NULL OR avg_vam_vertical_speed_mh >= 0.0),
    telemetry_points_count INT NOT NULL DEFAULT 0 CHECK (telemetry_points_count >= 0),
    hr_zones_distribution JSONB,
    pace_zones_distribution JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_hr_summary_validity CHECK (avg_hr IS NULL OR max_hr IS NULL OR avg_hr <= max_hr),
    CONSTRAINT chk_speed_summary_validity CHECK (avg_speed_ms IS NULL OR max_speed_ms IS NULL OR avg_speed_ms <= max_speed_ms)
);

-- 8. Tabla: INGESTION_JOBS
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id VARCHAR(64) PRIMARY KEY,
    athlete_profile_id UUID NOT NULL REFERENCES athlete_profiles(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL,
    file_storage_key VARCHAR(512) NOT NULL,
    detected_format VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'QUEUED' CHECK (
        status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED')
    ),
    progress_percent INT NOT NULL DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_hash ON ingestion_jobs (file_hash_sha256);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_athlete_status ON ingestion_jobs (athlete_profile_id, status);

CREATE TRIGGER trg_ingestion_jobs_updated_at
BEFORE UPDATE ON ingestion_jobs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 9. Tablas del Planificador de Entrenamiento
CREATE TABLE IF NOT EXISTS training_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    athlete_profile_id UUID NOT NULL REFERENCES athlete_profiles(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE' CHECK (
        status IN ('DRAFT', 'ACTIVE', 'COMPLETED', 'ARCHIVED')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_plan_dates CHECK (start_date <= end_date)
);

CREATE INDEX IF NOT EXISTS idx_training_plans_athlete_status ON training_plans (athlete_profile_id, status);

CREATE TRIGGER trg_training_plans_updated_at
BEFORE UPDATE ON training_plans
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS microcycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
    week_number INT NOT NULL CHECK (week_number >= 1),
    phase VARCHAR(32) NOT NULL CHECK (phase IN ('BASE', 'BUILD', 'PEAK', 'TAPER', 'RECOVERY')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_volume_hours NUMERIC(5, 2) NOT NULL DEFAULT 0.0 CHECK (target_volume_hours >= 0.0),
    target_tss NUMERIC(6, 2) NOT NULL DEFAULT 0.0 CHECK (target_tss >= 0.0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_microcycle_dates CHECK (start_date <= end_date)
);

CREATE INDEX IF NOT EXISTS idx_microcycles_plan_week ON microcycles (plan_id, week_number);

CREATE TABLE IF NOT EXISTS workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    microcycle_id UUID NOT NULL REFERENCES microcycles(id) ON DELETE CASCADE,
    day_of_week INT NOT NULL CHECK (day_of_week >= 1 AND day_of_week <= 7),
    is_rest_day BOOLEAN NOT NULL DEFAULT FALSE,
    session_category VARCHAR(32) NOT NULL CHECK (
        session_category IN ('ROAD_RUN', 'TRAIL_RUN', 'LONG_RUN', 'TEMPO', 'INTERVALS', 'RECOVERY', 'STRENGTH', 'REST')
    ),
    duration_min INT NOT NULL DEFAULT 0 CHECK (duration_min >= 0),
    target_distance_km NUMERIC(6, 3) DEFAULT 0.0 CHECK (target_distance_km >= 0.0),
    target_elevation_gain_m NUMERIC(6, 1) DEFAULT 0.0 CHECK (target_elevation_gain_m >= 0.0),
    exercise_list JSONB NOT NULL DEFAULT '[]'::jsonb,
    nutrition_guidelines JSONB NOT NULL DEFAULT '{}'::jsonb,
    recovery_prescriptions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workout_sessions_microcycle_day ON workout_sessions (microcycle_id, day_of_week);
