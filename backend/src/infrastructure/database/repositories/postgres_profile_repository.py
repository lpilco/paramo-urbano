"""PostgreSQL concrete repository implementation for Athlete Profiles and Goals."""

from datetime import date, timedelta
from typing import List, Optional
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.domain.models.athlete import AthleteProfile
from backend.src.domain.models.enums import Discipline, ExperienceLevel, SubgoalType
from backend.src.domain.models.goal import Goal
from backend.src.domain.models.value_objects import HeartRate
from backend.src.infrastructure.database.models.goal import GoalModel
from backend.src.infrastructure.database.models.plan import TrainingPlanModel
from backend.src.infrastructure.database.models.profile import AthleteProfileModel


class PostgresProfileRepository(AthleteProfileRepository):
    """Concrete repository managing persistence of AthleteProfile and Goal entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session (AsyncSession): Active SQLAlchemy async session.
        """
        self._session: AsyncSession = session

    def _map_experience_to_domain(self, raw_tier: str) -> ExperienceLevel:
        """Map raw or localized experience strings to canonical ExperienceLevel enum."""
        mapping = {
            "INICIAL": ExperienceLevel.BEGINNER,
            "MEDIO": ExperienceLevel.INTERMEDIATE,
            "AVANZADO": ExperienceLevel.ADVANCED,
            "BEGINNER": ExperienceLevel.BEGINNER,
            "INTERMEDIATE": ExperienceLevel.INTERMEDIATE,
            "ADVANCED": ExperienceLevel.ADVANCED,
        }
        return mapping.get(raw_tier.upper(), ExperienceLevel.BEGINNER)

    def _to_domain_profile(self, model: AthleteProfileModel) -> AthleteProfile:
        """Convert AthleteProfileModel ORM instance to domain AthleteProfile entity."""
        return AthleteProfile(
            profile_id=model.id,
            user_id=model.user_id,
            experience_level=self._map_experience_to_domain(model.experience_level),
            age=model.age,
            weight_kg=float(model.weight_kg),
            rest_hr=HeartRate(model.rest_hr) if model.rest_hr is not None else None,
            max_hr=HeartRate(model.max_hr) if model.max_hr is not None else None,
            created_at=model.created_at,
            current_ctl=float(model.current_ctl or 0.0),
            current_atl=float(model.current_atl or 0.0),
        )

    def _to_domain_goal(self, model: GoalModel) -> Goal:
        """Convert GoalModel ORM instance to domain Goal entity."""
        return Goal(
            goal_id=model.id,
            athlete_profile_id=model.athlete_profile_id,
            discipline=Discipline(model.discipline),
            subgoal_type=SubgoalType(model.subgoal_type),
            target_distance_km=float(model.custom_distance_km),
            target_elevation_gain_m=float(model.target_elevation_gain_m),
            target_date=model.target_date,
            available_days_per_week=model.available_days_per_week,
            reference_date=model.target_date - timedelta(days=Goal.MIN_DAYS_IN_ADVANCE),
            created_at=model.created_at,
        )

    async def save_profile(self, profile: AthleteProfile) -> AthleteProfile:
        """Persist or update an athlete profile entity."""
        stmt = select(AthleteProfileModel).where(AthleteProfileModel.id == profile.profile_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        rest_val = profile.rest_hr.bpm if profile.rest_hr is not None else None
        max_val = profile.max_hr.bpm if profile.max_hr is not None else None

        if model is None:
            model = AthleteProfileModel(
                id=profile.profile_id,
                user_id=profile.user_id,
                experience_level=profile.experience_level.value,
                age=profile.age,
                weight_kg=profile.weight_kg,
                rest_hr=rest_val,
                max_hr=max_val,
                created_at=profile.created_at,
            )
            self._session.add(model)
        else:
            model.user_id = profile.user_id
            model.experience_level = profile.experience_level.value
            model.age = profile.age
            model.weight_kg = profile.weight_kg
            model.rest_hr = rest_val
            model.max_hr = max_val

        await self._session.flush()
        return profile

    async def get_profile_by_id(self, profile_id: str) -> Optional[AthleteProfile]:
        """Retrieve an athlete profile by its primary identifier."""
        stmt = select(AthleteProfileModel).where(AthleteProfileModel.id == profile_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain_profile(model)

    async def get_profile_by_user_id(self, user_id: str) -> Optional[AthleteProfile]:
        """Retrieve an athlete profile associated with a user account."""
        stmt = select(AthleteProfileModel).where(AthleteProfileModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain_profile(model)

    async def update_workload_baselines(self, profile_id: str, ctl: float, atl: float) -> None:
        """Update Chronic Training Load (CTL) and Acute Training Load (ATL) baselines."""
        stmt = (
            update(AthleteProfileModel)
            .where(AthleteProfileModel.id == profile_id)
            .values(current_ctl=round(ctl, 2), current_atl=round(atl, 2))
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def save_goal(self, goal: Goal) -> Goal:
        """Persist or update an athlete's target goal."""
        stmt = select(GoalModel).where(GoalModel.id == goal.goal_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = GoalModel(
                id=goal.goal_id,
                athlete_profile_id=goal.athlete_profile_id,
                discipline=goal.discipline.value,
                subgoal_type=goal.subgoal_type.value,
                custom_distance_km=goal.target_distance_km,
                target_elevation_gain_m=goal.target_elevation_gain_m,
                target_date=goal.target_date,
                available_days_per_week=goal.available_days_per_week,
                is_active=True,
                created_at=goal.created_at,
            )
            self._session.add(model)
        else:
            model.discipline = goal.discipline.value
            model.subgoal_type = goal.subgoal_type.value
            model.custom_distance_km = goal.target_distance_km
            model.target_elevation_gain_m = goal.target_elevation_gain_m
        await self._session.flush()

        # Initialize or update active mesocycle training plan for this goal
        plan_stmt = select(TrainingPlanModel).where(
            TrainingPlanModel.athlete_profile_id == goal.athlete_profile_id,
            TrainingPlanModel.status == "ACTIVE",
        )
        plan_res = await self._session.execute(plan_stmt)
        plan_model = plan_res.scalar_one_or_none()

        start_d = date.today()
        end_d = goal.target_date
        plan_name = f"Plan {goal.discipline.value} ({goal.subgoal_type.value})"

        if plan_model is None:
            plan_model = TrainingPlanModel(
                id=str(uuid.uuid4()),
                athlete_profile_id=goal.athlete_profile_id,
                goal_id=goal.goal_id,
                name=plan_name,
                start_date=start_d,
                end_date=end_d,
                status="ACTIVE",
            )
            self._session.add(plan_model)
        else:
            plan_model.goal_id = goal.goal_id
            plan_model.name = plan_name
            plan_model.end_date = end_d

        await self._session.flush()
        return goal

    async def get_active_goal(self, athlete_profile_id: str) -> Optional[Goal]:
        """Retrieve the currently active goal for an athlete profile."""
        stmt = (
            select(GoalModel)
            .where(
                GoalModel.athlete_profile_id == athlete_profile_id,
                GoalModel.is_active.is_(True),
            )
            .order_by(GoalModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain_goal(model)

    async def list_goals(self, athlete_profile_id: str) -> List[Goal]:
        """Retrieve all goals configured for an athlete profile."""
        stmt = (
            select(GoalModel)
            .where(GoalModel.athlete_profile_id == athlete_profile_id)
            .order_by(GoalModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain_goal(m) for m in models]
