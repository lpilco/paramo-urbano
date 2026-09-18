"""Abstract repository interface for Athlete Profile and Goal persistence."""

from abc import ABC, abstractmethod
from typing import List, Optional

from backend.src.domain.models.athlete import AthleteProfile
from backend.src.domain.models.goal import Goal


class AthleteProfileRepository(ABC):
    """Abstract interface defining the contract for Athlete Profiles and Goals."""

    @abstractmethod
    async def save_profile(self, profile: AthleteProfile) -> AthleteProfile:
        """Persist or update an athlete profile entity.

        Args:
            profile (AthleteProfile): The profile entity to persist.

        Returns:
            AthleteProfile: The persisted profile entity.
        """
        pass

    @abstractmethod
    async def get_profile_by_id(self, profile_id: str) -> Optional[AthleteProfile]:
        """Retrieve an athlete profile by its primary identifier.

        Args:
            profile_id (str): Unique profile UUID.

        Returns:
            Optional[AthleteProfile]: The profile if found, or None.
        """
        pass

    @abstractmethod
    async def get_profile_by_user_id(self, user_id: str) -> Optional[AthleteProfile]:
        """Retrieve an athlete profile associated with a user account.

        Args:
            user_id (str): Associated user UUID.

        Returns:
            Optional[AthleteProfile]: The profile if found, or None.
        """
        pass

    @abstractmethod
    async def update_workload_baselines(
        self, profile_id: str, ctl: float, atl: float
    ) -> None:
        """Update Chronic Training Load (CTL) and Acute Training Load (ATL) baselines.

        Args:
            profile_id (str): Target profile UUID.
            ctl (float): New Chronic Training Load magnitude.
            atl (float): New Acute Training Load magnitude.
        """
        pass

    @abstractmethod
    async def save_goal(self, goal: Goal) -> Goal:
        """Persist or update an athlete's target goal.

        Args:
            goal (Goal): The goal entity to persist.

        Returns:
            Goal: The persisted goal entity.
        """
        pass

    @abstractmethod
    async def get_active_goal(self, athlete_profile_id: str) -> Optional[Goal]:
        """Retrieve the currently active goal for an athlete profile.

        Args:
            athlete_profile_id (str): Target athlete profile UUID.

        Returns:
            Optional[Goal]: The active goal if exists, or None.
        """
        pass

    @abstractmethod
    async def list_goals(self, athlete_profile_id: str) -> List[Goal]:
        """Retrieve all goals configured for an athlete profile.

        Args:
            athlete_profile_id (str): Target athlete profile UUID.

        Returns:
            List[Goal]: All historical and active goals.
        """
        pass
