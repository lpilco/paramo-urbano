"""Automated data seeding module for Páramo Urbano (v2.0.0 Core).

Seeds canonical profiles, goals, activities, and telemetry summaries idempotently
from JSON fixtures in data/seeds/.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import logging
import os
import sys
from typing import Any, Dict, Optional, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.src.infrastructure.database.models import (
    ActivityModel,
    ActivityTelemetrySummaryModel,
    AthleteProfileModel,
    GoalModel,
    UserModel,
)
from backend.src.infrastructure.database.session import (
    create_engine_and_session,
    init_db_schema,
)
from backend.src.infrastructure.security.jwt_service import RSAJwtSecurityService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Seeder] %(message)s",
)
logger = logging.getLogger("DataSeeder")

ROOT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../")
)
SEEDS_DIR = os.path.join(ROOT_DIR, "data", "seeds")


async def seed_athlete_from_dict(
    session: AsyncSession,
    data: Dict[str, Any],
    security_service: RSAJwtSecurityService,
) -> Tuple[str, str]:
    """Seed an athlete user, profile, goal, and activities idempotently.

    Args:
        session (AsyncSession): Active transactional database session.
        data (Dict[str, Any]): Structured profile data loaded from JSON.
        security_service (RSAJwtSecurityService): Service for hashing passwords.

    Returns:
        Tuple[str, str]: (user_id, profile_id)
    """
    user_data = data["user"]
    profile_data = data["profile"]
    goal_data = data.get("goal")
    activities_data = data.get("activities", [])

    email = user_data["email"].strip().lower()

    # 1. Check if user already exists
    user_stmt = select(UserModel).where(UserModel.email == email)
    user_result = await session.execute(user_stmt)
    existing_user = user_result.scalar_one_or_none()

    if existing_user is not None:
        user_id = str(existing_user.id)
        logger.info(f"User '{email}' already exists (id={user_id}).")

        # Retrieve profile
        profile_stmt = select(AthleteProfileModel).where(
            AthleteProfileModel.user_id == user_id
        )
        profile_res = await session.execute(profile_stmt)
        existing_profile = profile_res.scalar_one_or_none()
        profile_id = str(existing_profile.id) if existing_profile else str(uuid.uuid4())
    else:
        user_id = str(uuid.uuid4())
        hashed_pw = security_service.hash_password(user_data["password"])
        new_user = UserModel(
            id=user_id,
            email=email,
            password_hash=hashed_pw,
            full_name=user_data["full_name"],
        )
        session.add(new_user)
        await session.flush()

        profile_id = str(uuid.uuid4())
        new_profile = AthleteProfileModel(
            id=profile_id,
            user_id=user_id,
            experience_level=profile_data["experience_level"],
            age=profile_data["age"],
            weight_kg=profile_data["weight_kg"],
            rest_hr=profile_data.get("rest_hr"),
            max_hr=profile_data.get("max_hr"),
            vdot_score=profile_data.get("vdot_score"),
            current_ctl=profile_data.get("current_ctl", 0.0),
            current_atl=profile_data.get("current_atl", 0.0),
        )
        session.add(new_profile)
        await session.flush()
        logger.info(f"Created user '{email}' and profile '{profile_id}'.")

    # 2. Seed active goal if present
    if goal_data:
        goal_stmt = select(GoalModel).where(
            GoalModel.athlete_profile_id == profile_id,
            GoalModel.is_active == True,  # noqa: E712
        )
        goal_res = await session.execute(goal_stmt)
        if goal_res.scalar_one_or_none() is None:
            weeks_ahead = goal_data.get("weeks_ahead", 16)
            target_dt = date.today() + timedelta(weeks=weeks_ahead)

            new_goal = GoalModel(
                id=str(uuid.uuid4()),
                athlete_profile_id=profile_id,
                discipline=goal_data["discipline"],
                subgoal_type=goal_data["subgoal_type"],
                custom_distance_km=goal_data["custom_distance_km"],
                target_elevation_gain_m=goal_data.get("target_elevation_gain_m", 0.0),
                mountain_altitude_category=goal_data.get("mountain_altitude_category"),
                target_date=target_dt,
                available_days_per_week=goal_data.get("available_days_per_week", 5),
                is_active=True,
            )
            session.add(new_goal)
            logger.info(f"Seeded active goal for profile '{profile_id}' (target: {target_dt}).")

    # 3. Seed activities idempotently
    now = datetime.now(timezone.utc)
    for act in activities_data:
        days_ago = act.get("days_ago", 1)
        started_at = now - timedelta(days=days_ago)

        # Generate deterministic cryptographic SHA-256 for synthetic session
        raw_seed_str = (
            f"{profile_id}_{started_at.strftime('%Y%m%d%H%M')}_"
            f"{act['sport_category']}_{act['duration_seconds']}"
        )
        file_hash = hashlib.sha256(raw_seed_str.encode("utf-8")).hexdigest()

        # Check deduplication
        act_stmt = select(ActivityModel).where(
            ActivityModel.file_hash_sha256 == file_hash
        )
        act_res = await session.execute(act_stmt)
        if act_res.scalar_one_or_none() is not None:
            continue

        activity_id = str(uuid.uuid4())
        new_activity = ActivityModel(
            id=activity_id,
            athlete_profile_id=profile_id,
            source_type=act["source_type"],
            file_storage_key=f"{profile_id}/{file_hash}.{act['source_type'].lower()}",
            file_hash_sha256=file_hash,
            sport_category=act["sport_category"],
            started_at=started_at,
            duration_seconds=act["duration_seconds"],
            distance_meters=act.get("distance_meters", 0.0),
            elevation_gain_meters=act.get("elevation_gain_meters", 0.0),
            tss_score=act.get("tss_score"),
            session_rpe=act.get("session_rpe"),
            foster_load=act.get("foster_load"),
            processing_status="PROCESSED",
            notes=act.get("notes", ""),
        )
        session.add(new_activity)

        # Telemetry summary if present
        telem = act.get("telemetry_summary")
        if telem:
            summary = ActivityTelemetrySummaryModel(
                id=str(uuid.uuid4()),
                activity_id=activity_id,
                avg_hr=telem.get("avg_hr"),
                max_hr=telem.get("max_hr"),
                avg_speed_ms=telem.get("avg_speed_ms"),
                max_speed_ms=telem.get("max_speed_ms"),
                avg_vam_vertical_speed_mh=telem.get("avg_vam_vertical_speed_mh"),
                telemetry_points_count=telem.get("telemetry_points_count", 0),
                hr_zones_distribution=telem.get("hr_zones_distribution"),
                pace_zones_distribution=telem.get("pace_zones_distribution"),
            )
            session.add(summary)

    await session.commit()
    logger.info(f"Completed seeding for '{email}'.")
    return user_id, profile_id


async def seed_database(
    session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
    engine: Optional[Any] = None,
    database_url: Optional[str] = None,
) -> None:
    """Execute master database seeding process from configured JSON seed files.

    Args:
        session_factory (Optional[async_sessionmaker[AsyncSession]], optional):
            Database session factory. Defaults to lazy default factory.
        engine (Optional[Any], optional): AsyncEngine to initialize schema if needed.
        database_url (Optional[str], optional): Explicit database URL.
    """
    logger.info("Starting Páramo Urbano data seeding process...")

    if session_factory is None:
        try:
            engine, session_factory = create_engine_and_session(database_url)
            await init_db_schema(engine)
        except Exception as exc:
            if database_url is None:
                logger.warning(
                    f"Configured database unreachable ({exc}). Falling back to local SQLite: paramo_urbano_dev.db"
                )
                engine, session_factory = create_engine_and_session(
                    "sqlite+aiosqlite:///paramo_urbano_dev.db"
                )
                await init_db_schema(engine)
            else:
                raise
    elif engine is not None:
        await init_db_schema(engine)

    security_service = RSAJwtSecurityService()

    # Load Perfil Avanzado
    advanced_path = os.path.join(SEEDS_DIR, "user_profile.json")
    if os.path.exists(advanced_path):
        with open(advanced_path, "r", encoding="utf-8") as f:
            adv_data = json.load(f)
        async with session_factory() as session:
            await seed_athlete_from_dict(session, adv_data, security_service)
    else:
        logger.warning(f"Advanced profile seed file not found: {advanced_path}")

    # Load Perfil Principiante CaCo
    beginner_path = os.path.join(SEEDS_DIR, "user_profiles", "athlete_beginner_caco.json")
    if os.path.exists(beginner_path):
        with open(beginner_path, "r", encoding="utf-8") as f:
            beg_data = json.load(f)
        async with session_factory() as session:
            await seed_athlete_from_dict(session, beg_data, security_service)
    else:
        logger.warning(f"Beginner profile seed file not found: {beginner_path}")

    logger.info("Data seeding process finished successfully.")


def main() -> None:
    """CLI entrypoint for executing database seeds."""
    db_url = None
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--db="):
                db_url = arg.split("=", 1)[1]
            elif not arg.startswith("--"):
                db_url = arg
    asyncio.run(seed_database(database_url=db_url))


if __name__ == "__main__":
    main()
