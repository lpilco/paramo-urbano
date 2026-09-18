"""Unit tests for domain Entities and Canonical Data Contracts.

Validates Athlete, AthleteProfile (Gellish theoretical HR and Karvonen zones),
Goal (14-day adaptation horizon and Trail +D requirements), Activity (Foster sRPE),
and CanonicalActivityRecord telemetry invariants.
"""

from datetime import date, datetime, timedelta, timezone
import unittest

from backend.src.domain.exceptions import (
    EntityValidationError,
    GoalRuleViolationError,
)
from backend.src.domain.models.activity import Activity, CanonicalActivityRecord
from backend.src.domain.models.athlete import Athlete, AthleteProfile
from backend.src.domain.models.enums import (
    Discipline,
    ExperienceLevel,
    ProcessingStatus,
    SourceType,
    SportCategory,
    SubgoalType,
)
from backend.src.domain.models.goal import Goal
from backend.src.domain.models.value_objects import (
    HeartRate,
    SessionRPE,
    Sha256Hash,
    Speed,
)


class TestAthleteAndProfileEntities(unittest.TestCase):
    """Test suite for Athlete and AthleteProfile domain entities."""

    def test_athlete_profile_gellish_theoretical_hr(self) -> None:
        """Verify deterministic theoretical HRmax via Gellish formula: 208 - (0.7 * age)."""
        # Age 40: 208 - (0.7 * 40) = 208 - 28 = 180 bpm
        hr_40 = AthleteProfile.calculate_theoretical_max_hr(40)
        self.assertEqual(hr_40.bpm, 180)

        # Age 20: 208 - (0.7 * 20) = 208 - 14 = 194 bpm
        hr_20 = AthleteProfile.calculate_theoretical_max_hr(20)
        self.assertEqual(hr_20.bpm, 194)

        # Age 55: 208 - (0.7 * 55) = 208 - 38.5 = 170 bpm (rounded)
        hr_55 = AthleteProfile.calculate_theoretical_max_hr(55)
        self.assertEqual(hr_55.bpm, 170)

    def test_athlete_profile_effective_max_hr_and_zones(self) -> None:
        """Verify effective max HR and Karvonen 5-zone cardiovascular boundaries."""
        rest_hr = HeartRate(50)
        measured_max = HeartRate(190)

        profile = AthleteProfile(
            profile_id="prof_001",
            user_id="usr_001",
            experience_level=ExperienceLevel.ADVANCED,
            age=30,
            weight_kg=68.5,
            rest_hr=rest_hr,
            max_hr=measured_max,
        )

        # Effective max HR is the measured one
        self.assertEqual(profile.effective_max_hr, measured_max)
        # Heart Rate Reserve = 190 - 50 = 140 bpm
        self.assertEqual(profile.heart_rate_reserve, 140)

        # Karvonen zones check
        zones = profile.calculate_hr_zones()
        self.assertIn("Z1_RECOVERY", zones)
        self.assertIn("Z5_ANAEROBIC", zones)
        # Z1: 50 + 140 * 0.50 = 120 bpm to 50 + 140 * 0.60 = 134 bpm
        self.assertEqual(zones["Z1_RECOVERY"], (120, 134))
        # Z5: 50 + 140 * 0.90 = 176 bpm to 50 + 140 * 1.00 = 190 bpm
        self.assertEqual(zones["Z5_ANAEROBIC"], (176, 190))

    def test_athlete_profile_fallback_to_theoretical_hr(self) -> None:
        """Verify fallback to Gellish when max_hr is not provided (Beginner archetype)."""
        profile = AthleteProfile(
            profile_id="prof_002",
            user_id="usr_002",
            experience_level=ExperienceLevel.BEGINNER,
            age=30,
            weight_kg=72.0,
            rest_hr=None,
            max_hr=None,
        )
        # Gellish for age 30: 208 - 21 = 187 bpm
        self.assertEqual(profile.effective_max_hr.bpm, 187)
        self.assertIsNone(profile.heart_rate_reserve)

    def test_athlete_profile_invalid_invariants(self) -> None:
        """Verify that out-of-range demographic and physiological data fail fast."""
        # Age under 10 or over 100
        with self.assertRaises(EntityValidationError):
            AthleteProfile(None, "u1", ExperienceLevel.BEGINNER, 9, 60.0)
        with self.assertRaises(EntityValidationError):
            AthleteProfile(None, "u1", ExperienceLevel.BEGINNER, 101, 60.0)

        # Weight under 30 kg or over 250 kg
        with self.assertRaises(EntityValidationError):
            AthleteProfile(None, "u1", ExperienceLevel.BEGINNER, 25, 29.9)
        with self.assertRaises(EntityValidationError):
            AthleteProfile(None, "u1", ExperienceLevel.BEGINNER, 25, 250.1)

        # Rest HR >= Max HR
        with self.assertRaises(EntityValidationError):
            AthleteProfile(
                None, "u1", ExperienceLevel.ADVANCED, 25, 70.0,
                rest_hr=HeartRate(180), max_hr=HeartRate(170)
            )

    def test_athlete_aggregate_creation_and_profile_attachment(self) -> None:
        """Verify Athlete aggregate root creation, email validation, and profile linking."""
        athlete = Athlete(athlete_id="ath_123", email="runner@paramourbano.ec")
        self.assertEqual(athlete.email, "runner@paramourbano.ec")
        self.assertIsNone(athlete.profile)

        profile = AthleteProfile(
            profile_id="prof_123",
            user_id="ath_123",
            experience_level=ExperienceLevel.INTERMEDIATE,
            age=28,
            weight_kg=65.0,
        )
        athlete.attach_profile(profile)
        self.assertEqual(athlete.profile, profile)

    def test_athlete_invalid_email_raises_exception(self) -> None:
        """Verify that malformed emails fail fast."""
        with self.assertRaises(EntityValidationError):
            Athlete(None, "not-an-email")
        with self.assertRaises(EntityValidationError):
            Athlete(None, "@domain.com")


class TestGoalEntity(unittest.TestCase):
    """Test suite for Goal domain entity and deterministic planning constraints."""

    def setUp(self) -> None:
        """Set deterministic reference date for unit tests."""
        self.ref_date = date(2026, 9, 20)

    def test_valid_road_running_goal(self) -> None:
        """Verify road running goal configuration without mandatory elevation gain."""
        target_date = self.ref_date + timedelta(days=70)  # 10 weeks
        goal = Goal(
            goal_id="goal_road",
            athlete_profile_id="prof_001",
            discipline=Discipline.ROAD_RUNNING,
            subgoal_type=SubgoalType.MARATHON,
            target_distance_km=42.195,
            target_elevation_gain_m=0.0,
            target_date=target_date,
            available_days_per_week=5,
            reference_date=self.ref_date,
        )

        self.assertEqual(goal.target_distance_km, 42.195)
        self.assertEqual(goal.target_elevation_gain_m, 0.0)
        self.assertEqual(goal.days_to_target(self.ref_date), 70)
        self.assertEqual(goal.weeks_to_target(self.ref_date), 10)

    def test_valid_trail_running_goal_with_elevation(self) -> None:
        """Verify trail running goal with mandatory positive elevation gain (+D)."""
        target_date = self.ref_date + timedelta(days=112)  # 16 weeks
        goal = Goal(
            goal_id="goal_trail",
            athlete_profile_id="prof_001",
            discipline=Discipline.TRAIL_RUNNING,
            subgoal_type=SubgoalType.TRAIL_MARATHON,
            target_distance_km=42.0,
            target_elevation_gain_m=2400.0,
            target_date=target_date,
            available_days_per_week=5,
            reference_date=self.ref_date,
        )

        self.assertEqual(goal.target_elevation_gain_m, 2400.0)
        self.assertEqual(goal.weeks_to_target(self.ref_date), 16)

    def test_trail_running_without_elevation_raises_violation(self) -> None:
        """Verify that TRAIL_RUNNING with target_elevation_gain_m <= 0 is strictly rejected."""
        target_date = self.ref_date + timedelta(days=30)
        with self.assertRaises(GoalRuleViolationError):
            Goal(
                goal_id=None,
                athlete_profile_id="prof_001",
                discipline=Discipline.TRAIL_RUNNING,
                subgoal_type=SubgoalType.TRAIL_SHORT,
                target_distance_km=21.0,
                target_elevation_gain_m=0.0,  # Invalid for trail running
                target_date=target_date,
                reference_date=self.ref_date,
            )

    def test_target_date_under_14_days_raises_violation(self) -> None:
        """Verify strict blocking of goals with less than 14 days adaptation window."""
        # 13 days in future -> violation
        with self.assertRaises(GoalRuleViolationError):
            Goal(
                goal_id=None,
                athlete_profile_id="prof_001",
                discipline=Discipline.ROAD_RUNNING,
                subgoal_type=SubgoalType.TEN_K,
                target_distance_km=10.0,
                target_elevation_gain_m=0.0,
                target_date=self.ref_date + timedelta(days=13),
                reference_date=self.ref_date,
            )

        # Past date -> violation
        with self.assertRaises(GoalRuleViolationError):
            Goal(
                goal_id=None,
                athlete_profile_id="prof_001",
                discipline=Discipline.ROAD_RUNNING,
                subgoal_type=SubgoalType.TEN_K,
                target_distance_km=10.0,
                target_elevation_gain_m=0.0,
                target_date=self.ref_date - timedelta(days=1),
                reference_date=self.ref_date,
            )

    def test_target_date_exactly_14_days_is_accepted(self) -> None:
        """Verify that exactly 14 days in advance is accepted as minimum threshold."""
        goal = Goal(
            goal_id=None,
            athlete_profile_id="prof_001",
            discipline=Discipline.ROAD_RUNNING,
            subgoal_type=SubgoalType.FIVE_K,
            target_distance_km=5.0,
            target_elevation_gain_m=0.0,
            target_date=self.ref_date + timedelta(days=14),
            reference_date=self.ref_date,
        )
        self.assertEqual(goal.days_to_target(self.ref_date), 14)
        self.assertEqual(goal.weeks_to_target(self.ref_date), 2)


class TestActivityAndCanonicalRecord(unittest.TestCase):
    """Test suite for Activity entity and CanonicalActivityRecord."""

    def test_canonical_activity_record_valid_telemetry(self) -> None:
        """Verify CanonicalActivityRecord calculations (VAM, paces, durations)."""
        record = CanonicalActivityRecord(
            record_id="rec_001",
            sport_category=SportCategory.TRAIL_RUN,
            started_at=datetime(2026, 9, 17, 6, 0, 0, tzinfo=timezone.utc),
            duration_seconds=7200,  # 2 hours
            distance_meters=18000.0,  # 18 km
            elevation_gain_meters=1200.0,  # 1200 m D+
            avg_speed=Speed(2.5),
            max_speed=Speed(5.0),
            avg_hr=HeartRate(152),
            max_hr=HeartRate(178),
            file_hash=Sha256Hash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            telemetry_points_count=7200,
        )

        self.assertEqual(record.duration_minutes, 120.0)
        self.assertEqual(record.duration_hours, 2.0)
        self.assertEqual(record.distance_km, 18.0)
        # VAM = 1200 m / 2.0 h = 600.0 m/h
        self.assertEqual(record.vam_vertical_speed_mh, 600.0)

    def test_canonical_activity_record_invalid_invariants(self) -> None:
        """Verify telemetry invariant validations fail fast."""
        now = datetime.now(timezone.utc)

        # Duration <= 0
        with self.assertRaises(EntityValidationError):
            CanonicalActivityRecord(None, SportCategory.ROAD_RUN, now, 0, 5000.0, 50.0)

        # Distance < 0
        with self.assertRaises(EntityValidationError):
            CanonicalActivityRecord(None, SportCategory.ROAD_RUN, now, 1800, -10.0, 50.0)

        # Avg HR > Max HR
        with self.assertRaises(EntityValidationError):
            CanonicalActivityRecord(
                None, SportCategory.ROAD_RUN, now, 1800, 5000.0, 50.0,
                avg_hr=HeartRate(180), max_hr=HeartRate(160)
            )

        # Avg Speed > Max Speed
        with self.assertRaises(EntityValidationError):
            CanonicalActivityRecord(
                None, SportCategory.ROAD_RUN, now, 1800, 5000.0, 50.0,
                avg_speed=Speed(6.0), max_speed=Speed(4.0)
            )

    def test_manual_activity_foster_load_computation(self) -> None:
        """Verify FR-02: 50 min session with RPE 8 produces exactly 400.0 Foster load units."""
        started = datetime(2026, 9, 17, 7, 0, 0, tzinfo=timezone.utc)
        rpe = SessionRPE(8)

        act = Activity.create_manual(
            athlete_profile_id="prof_100",
            sport_category=SportCategory.STRENGTH,
            started_at=started,
            duration_minutes=50,
            session_rpe=rpe,
            notes="Goblet squat, bulgarian split squats, core",
        )

        self.assertEqual(act.source_type, SourceType.MANUAL)
        self.assertEqual(act.sport_category, SportCategory.STRENGTH)
        self.assertEqual(act.duration_seconds, 3000)
        self.assertEqual(act.duration_minutes, 50.0)
        self.assertEqual(act.session_rpe, rpe)
        self.assertEqual(act.foster_load, 400.0)
        self.assertEqual(act.processing_status, ProcessingStatus.PROCESSED)

    def test_manual_activity_caco_session(self) -> None:
        """Verify Beginner Walk/Run (CaCo) session: 30 min at RPE 4 -> 120.0 load."""
        started = datetime(2026, 9, 17, 8, 0, 0, tzinfo=timezone.utc)
        act = Activity.create_manual(
            athlete_profile_id="prof_200",
            sport_category=SportCategory.ROAD_RUN,
            started_at=started,
            duration_minutes=30,
            session_rpe=SessionRPE(4),
            distance_meters=3200.0,
        )

        self.assertEqual(act.foster_load, 120.0)
        self.assertEqual(act.distance_km, 3.2)

    def test_pending_upload_and_state_transitions(self) -> None:
        """Verify asynchronous ingestion lifecycle transitions."""
        file_hash = Sha256Hash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

        act = Activity.create_pending_upload(
            athlete_profile_id="prof_300",
            file_hash=file_hash,
            source_type=SourceType.FIT,
        )

        self.assertEqual(act.processing_status, ProcessingStatus.QUEUED)

        act.mark_as_processing()
        self.assertEqual(act.processing_status, ProcessingStatus.PROCESSING)

        act.mark_as_processed()
        self.assertEqual(act.processing_status, ProcessingStatus.PROCESSED)

        act.mark_as_failed("Corrupt CRC-16 checksum")
        self.assertEqual(act.processing_status, ProcessingStatus.FAILED)
        self.assertIn("Corrupt CRC-16 checksum", act.notes)

    def test_update_rpe_recalculates_foster_load(self) -> None:
        """Verify that updating an activity's RPE updates Foster load proportionally."""
        act = Activity(
            activity_id="act_555",
            athlete_profile_id="prof_001",
            source_type=SourceType.MANUAL,
            sport_category=SportCategory.ROAD_RUN,
            started_at=datetime.now(timezone.utc),
            duration_seconds=3600,  # 60 min
        )
        self.assertIsNone(act.foster_load)

        act.set_rpe(SessionRPE(6))
        # 60 min * RPE 6 = 360.0
        self.assertEqual(act.foster_load, 360.0)

        act.set_rpe(SessionRPE(9))
        # 60 min * RPE 9 = 540.0
        self.assertEqual(act.foster_load, 540.0)


if __name__ == "__main__":
    unittest.main()
