"""Database clean reset script for Páramo Urbano (v2.0.0 Core).

Executes a cascading truncation / purge across all tables:
- users
- athlete_profiles
- goals
- activities
- ingestion_jobs
- activity_telemetry_summaries
- training_plans
- microcycles
- workout_sessions

Re-creates all clean schemas from scratch using SQLAlchemy metadata.
Leaves database in 100% clean state with ZERO mock or seed records.
"""

import asyncio
import logging
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.src.infrastructure.database.models.base import Base
import backend.src.infrastructure.database.models  # Ensure all models are registered
from backend.src.infrastructure.database.session import (
    create_engine_and_session,
    init_db_schema,
    resolve_database_url,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ResetDB] %(message)s",
)
logger = logging.getLogger("ResetDB")


async def purge_and_recreate_database(engine: AsyncEngine) -> None:
    """Cascade purge all tables and recreate schema cleanly.

    Args:
        engine (AsyncEngine): SQLAlchemy asynchronous database engine.
    """
    logger.info("Connecting to database for clean reset...")

    # Determine database dialect
    dialect_name = engine.dialect.name
    logger.info(f"Detected database dialect: '{dialect_name}'")

    async with engine.begin() as conn:
        if dialect_name == "postgresql":
            logger.info("Executing TRUNCATE CASCADE on PostgreSQL tables...")
            truncate_stmt = text(
                """
                TRUNCATE TABLE 
                    workout_sessions,
                    microcycles,
                    training_plans,
                    activity_telemetry_summaries,
                    activities,
                    ingestion_jobs,
                    goals,
                    athlete_profiles,
                    users
                CASCADE;
                """
            )
            try:
                await conn.execute(truncate_stmt)
                logger.info("All tables truncated with CASCADE.")
            except Exception as tr_err:
                logger.warning(f"Could not truncate directly ({tr_err}), dropping tables...")
                await conn.run_sync(Base.metadata.drop_all)
        else:
            # SQLite or other
            logger.info("Dropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("Re-creating all schema tables from Base.metadata...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Schema re-creation complete.")


async def main() -> None:
    """CLI orchestrator for database purge."""
    target_urls = []

    # Check CLI arguments first
    if len(sys.argv) > 1 and sys.argv[1].startswith(("--url=", "postgresql://", "sqlite://")):
        arg_url = sys.argv[1].replace("--url=", "")
        target_urls.append(resolve_database_url(arg_url))
    else:
        env_url = resolve_database_url()
        target_urls.append(env_url)

        # If env points to container name 'postgres', also prepare localhost alternative
        if "@postgres:" in env_url:
            target_urls.append(env_url.replace("@postgres:", "@127.0.0.1:"))

        # Also reset local sqlite development database if present
        local_sqlite = f"sqlite+aiosqlite:///{os.path.join(ROOT_DIR, 'paramo_urbano_dev.db')}"
        if os.path.exists(os.path.join(ROOT_DIR, "paramo_urbano_dev.db")):
            target_urls.append(local_sqlite)

    success = False
    for db_url in target_urls:
        logger.info(f"Attempting clean reset on target: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        try:
            engine, _ = create_engine_and_session(db_url)
            await purge_and_recreate_database(engine)
            await engine.dispose()
            logger.info("Clean state successfully achieved on database. Zero mock data present.")
            success = True
            break
        except Exception as conn_err:
            logger.warning(f"Could not reset {db_url.split('@')[-1] if '@' in db_url else db_url}: {conn_err}")

    if not success:
        logger.error("Failed to connect to any target database. Ensure PostgreSQL or SQLite is available.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
