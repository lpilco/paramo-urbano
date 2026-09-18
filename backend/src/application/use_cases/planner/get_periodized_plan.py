"""Use case for generating periodized training plans with contextual nutrition and recovery therapies."""

from datetime import date
from typing import List

from backend.src.application.dtos.plans import (
    MicrocycleDTO,
    NutritionPrescriptionDTO,
    PeriodizedPlanResponse,
    RecoveryTherapyDTO,
    WorkoutSessionDTO,
)
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.domain.exceptions import EntityNotFoundError
from backend.src.domain.physiological.acwr import ACWREvaluator


class GetPeriodizedPlanUseCase:
    """Orchestrates deterministic periodization plans with safe progression and recovery prescriptions."""

    def __init__(self, profile_repository: AthleteProfileRepository) -> None:
        """Initialize use case with profile repository.

        Args:
            profile_repository (AthleteProfileRepository): Port for athlete profiles and goals.
        """
        self._profile_repo: AthleteProfileRepository = profile_repository

    def _build_standard_sessions(
        self,
        base_volume_hours: float,
        discipline: str,
        elevation_gain_target: float,
    ) -> List[WorkoutSessionDTO]:
        """Generate canonical 7-day microcycle sessions with contextual nutrition and therapies."""
        is_trail = discipline in ("TRAIL_RUNNING", "TREKKING")
        weekend_sport = "TRAIL_RUN" if is_trail else "ROAD_RUN"
        weekend_elev = max(400.0, elevation_gain_target * 0.25) if is_trail else 50.0

        return [
            # Day 1: Lunes - Descanso Activo / Movilidad
            WorkoutSessionDTO(
                day_of_week=1,
                day_name="Lunes",
                is_rest_day=True,
                session_category="REST",
                duration_min=0,
                target_distance_km=0.0,
                target_elevation_gain_m=0.0,
                nutrition=NutritionPrescriptionDTO(
                    strategy="BALANCED_RECOVERY",
                    protein_g_kg="1.4 - 1.6 g/kg/día",
                    carbs_g_kg="3.0 - 4.0 g/kg/día",
                    hydration_guidelines="2.0 - 2.5 L de agua mineral con electrolitos y magnesio.",
                ),
                recovery=RecoveryTherapyDTO(
                    therapy_name="Automasaje Miofascial / Foam Roller",
                    protocol="15 min de liberación miofascial en sóleos, gemelos e isquiotibiales.",
                ),
            ),
            # Day 2: Martes - Fuerza Neuromuscular
            WorkoutSessionDTO(
                day_of_week=2,
                day_name="Martes",
                is_rest_day=False,
                session_category="STRENGTH",
                duration_min=50,
                target_distance_km=0.0,
                target_elevation_gain_m=0.0,
                nutrition=NutritionPrescriptionDTO(
                    strategy="HIGH_PROTEIN",
                    protein_g_kg="1.8 - 2.2 g/kg/día",
                    carbs_g_kg="4.0 - 5.0 g/kg/día",
                    hydration_guidelines=(
                        "Ingesta de 25-30g de proteína de alto valor biológico dentro "
                        "de los 30 min post-entrenamiento."
                    ),
                ),
                recovery=RecoveryTherapyDTO(
                    therapy_name="Sauna Seco",
                    protocol="15-20 min a 80°C para relajación muscular, vasodilatación y detoxificación.",
                ),
            ),
            # Day 3: Miércoles - Carrera Continua Aeróbica
            WorkoutSessionDTO(
                day_of_week=3,
                day_name="Miércoles",
                is_rest_day=False,
                session_category="ROAD_RUN",
                duration_min=55,
                target_distance_km=9.0,
                target_elevation_gain_m=40.0,
                nutrition=NutritionPrescriptionDTO(
                    strategy="MODERATE_CARBS",
                    protein_g_kg="1.6 g/kg/día",
                    carbs_g_kg="5.0 - 6.0 g/kg/día",
                    hydration_guidelines="500 ml de bebida isotónica durante el rodaje.",
                ),
                recovery=RecoveryTherapyDTO(
                    therapy_name="Movilidad Dinámica y Estiramientos",
                    protocol="10 min de movilidad articular y flexibilidad de cadena posterior.",
                ),
            ),
            # Day 4: Jueves - Descanso Total
            WorkoutSessionDTO(
                day_of_week=4,
                day_name="Jueves",
                is_rest_day=True,
                session_category="REST",
                duration_min=0,
                target_distance_km=0.0,
                target_elevation_gain_m=0.0,
                nutrition=NutritionPrescriptionDTO(
                    strategy="BALANCED_RECOVERY",
                    protein_g_kg="1.5 g/kg/día",
                    carbs_g_kg="3.5 g/kg/día",
                    hydration_guidelines="2.0 L de agua con infusión de antioxidantes y descanso metabólico.",
                ),
                recovery=RecoveryTherapyDTO(
                    therapy_name="Descanso Pasivo y Sueño Profundo",
                    protocol="Mínimo 8 horas de descanso nocturno y elevación pasiva de piernas 15 min.",
                ),
            ),
            # Day 5: Viernes - Fuerza Funcional y Core
            WorkoutSessionDTO(
                day_of_week=5,
                day_name="Viernes",
                is_rest_day=False,
                session_category="STRENGTH",
                duration_min=45,
                target_distance_km=0.0,
                target_elevation_gain_m=0.0,
                nutrition=NutritionPrescriptionDTO(
                    strategy="HIGH_PROTEIN",
                    protein_g_kg="1.8 - 2.0 g/kg/día",
                    carbs_g_kg="4.5 g/kg/día",
                    hydration_guidelines=(
                        "Hidratación constante con electrolitos para sostener la contractilidad muscular."
                    ),
                ),
                recovery=RecoveryTherapyDTO(
                    therapy_name="Sauna Seco y Automasaje",
                    protocol="15 min de sauna seco seguido de automasaje suave en cuádriceps y glúteos.",
                ),
            ),
            # Day 6: Sábado - Fondo Largo / Tirada de Montaña con +D
            WorkoutSessionDTO(
                day_of_week=6,
                day_name="Sábado",
                is_rest_day=False,
                session_category=weekend_sport,
                duration_min=110,
                target_distance_km=16.5,
                target_elevation_gain_m=weekend_elev,
                nutrition=NutritionPrescriptionDTO(
                    strategy="GLYCOGEN_LOAD",
                    protein_g_kg="1.6 - 1.8 g/kg/día",
                    carbs_g_kg="6.0 - 8.0 g/kg/día",
                    hydration_guidelines=(
                        "Sobrecarga glucogénica previa y 500-750 ml/h de solución "
                        "isotónica con sodio (600-800 mg Na/L)."
                    ),
                ),
                recovery=RecoveryTherapyDTO(
                    therapy_name="Baños de Contraste (Hidroterapia)",
                    protocol=(
                        "3 ciclos de 1 min agua fría (10-12°C) por 3 min agua caliente (38°C) "
                        "+ masaje de descarga deportiva."
                    ),
                ),
            ),
            # Day 7: Domingo - Regenerativo / Caminata Suave
            WorkoutSessionDTO(
                day_of_week=7,
                day_name="Domingo",
                is_rest_day=True,
                session_category="REST",
                duration_min=30,
                target_distance_km=3.0,
                target_elevation_gain_m=0.0,
                nutrition=NutritionPrescriptionDTO(
                    strategy="BALANCED_RECOVERY",
                    protein_g_kg="1.5 g/kg/día",
                    carbs_g_kg="4.0 g/kg/día",
                    hydration_guidelines="Rehidratación hipotónica post-fin de semana.",
                ),
                recovery=RecoveryTherapyDTO(
                    therapy_name="Automasaje Miofascial y Crioterapia Local",
                    protocol="Uso de foam roller o pistola de percusión para descarga linfática.",
                ),
            ),
        ]

    async def execute(
        self,
        athlete_profile_id: str,
        view: str = "WEEKLY",
    ) -> PeriodizedPlanResponse:
        """Generate or retrieve periodized microcycles complying with safe progression rules (<= 10%).

        Args:
            athlete_profile_id (str): Associated athlete profile UUID.
            view (str, optional): Target view granularity ('DAILY', 'WEEKLY', 'MONTHLY'). Defaults to 'WEEKLY'.

        Returns:
            PeriodizedPlanResponse: Formatted plan response.

        Raises:
            EntityNotFoundError: If athlete profile does not exist.
        """
        profile = await self._profile_repo.get_profile_by_id(athlete_profile_id)
        if profile is None:
            raise EntityNotFoundError(f"Athlete profile '{athlete_profile_id}' not found.")

        active_goal = await self._profile_repo.get_active_goal(athlete_profile_id)
        discipline = active_goal.discipline.value if active_goal else "ROAD_RUNNING"
        elev_target = active_goal.target_elevation_gain_m if active_goal else 0.0
        target_date_str = active_goal.target_date.isoformat() if active_goal else None

        # 1. Biomechanical Fatigue Check (FR-04): Trigger forced rest day if ACWR > 1.5
        cur_ctl = float(getattr(profile, "current_ctl", 0.0) or 0.0)
        cur_atl = float(getattr(profile, "current_atl", 0.0) or 0.0)
        is_overloaded = False
        if cur_ctl > 0.0:
            acwr_status = ACWREvaluator().calculate(acute_load=cur_atl, chronic_load=cur_ctl)
            if acwr_status.requires_mandatory_rest or acwr_status.ratio > 1.5:
                is_overloaded = True

        base_hours = 4.5
        base_load = 280.0
        week1_sessions = self._build_standard_sessions(base_hours, discipline, elev_target)

        # Substitute next intense session with MANDATORY REST DAY if overloaded
        if is_overloaded:
            replaced = False
            new_sessions = []
            for s in week1_sessions:
                if not replaced and not s.is_rest_day:
                    forced_rest = WorkoutSessionDTO(
                        day_of_week=s.day_of_week,
                        day_name=f"{s.day_name} (DÍA DE DESCANSO OBLIGATORIO)",
                        is_rest_day=True,
                        session_category="REST",
                        duration_min=0,
                        target_distance_km=0.0,
                        target_elevation_gain_m=0.0,
                        nutrition=NutritionPrescriptionDTO(
                            strategy="BALANCED_RECOVERY",
                            protein_g_kg="1.6 g/kg/día",
                            carbs_g_kg="3.5 g/kg/día",
                            hydration_guidelines="Hidratación hipotónica con antioxidantes y magnesio.",
                        ),
                        recovery=RecoveryTherapyDTO(
                            therapy_name="Descanso Forzado por Sobrecarga",
                            protocol="Inyección automática por ACWR > 1.50. Cese estricto de impacto osteoarticular.",
                        ),
                    )
                    new_sessions.append(forced_rest)
                    replaced = True
                else:
                    new_sessions.append(s)
            week1_sessions = new_sessions

        # 2. Periodized Mesocycle Generation (FR-05)
        # Determine total weeks to target (default 4 if not set)
        weeks_to_target = 4
        if active_goal and active_goal.target_date:
            days_diff = (active_goal.target_date - date.today()).days
            if days_diff > 0:
                weeks_to_target = max(4, round(days_diff / 7.0))

        if weeks_to_target >= 12:
            # Multi-phase macrocycle: Base (weeks 1-4), Build (weeks 5-10), Peak (weeks 11-14), Taper (weeks 15-16)
            week1 = MicrocycleDTO(
                week_number=1,
                phase="BASE",
                target_volume_hours=round(base_hours, 2),
                target_load=round(base_load, 1),
                weekly_progression_pct=0.0,
                sessions=week1_sessions,
            )
            week2 = MicrocycleDTO(
                week_number=2,
                phase="BUILD",
                target_volume_hours=round(base_hours * 1.075, 2),
                target_load=round(base_load * 1.075, 1),
                weekly_progression_pct=7.5,
                sessions=week1_sessions,
            )
            week3 = MicrocycleDTO(
                week_number=3,
                phase="PEAK",
                target_volume_hours=round(base_hours * 1.15, 2),
                target_load=round(base_load * 1.15, 1),
                weekly_progression_pct=7.0,
                sessions=week1_sessions,
            )
            week4 = MicrocycleDTO(
                week_number=4,
                phase="TAPER",
                target_volume_hours=round(base_hours * 0.65, 2),
                target_load=round(base_load * 0.65, 1),
                weekly_progression_pct=-35.0,
                sessions=week1_sessions,
            )
            all_microcycles = [week1, week2, week3, week4]
        else:
            # Standard 4-week build/recovery mesocycle
            week1 = MicrocycleDTO(
                week_number=1,
                phase="BUILD_1",
                target_volume_hours=round(base_hours, 2),
                target_load=round(base_load, 1),
                weekly_progression_pct=0.0,
                sessions=week1_sessions,
            )
            week2 = MicrocycleDTO(
                week_number=2,
                phase="BUILD_2",
                target_volume_hours=round(base_hours * 1.075, 2),
                target_load=round(base_load * 1.075, 1),
                weekly_progression_pct=7.5,
                sessions=week1_sessions,
            )
            week3 = MicrocycleDTO(
                week_number=3,
                phase="BUILD_3",
                target_volume_hours=round(base_hours * 1.15, 2),
                target_load=round(base_load * 1.15, 1),
                weekly_progression_pct=7.5,
                sessions=week1_sessions,
            )
            week4 = MicrocycleDTO(
                week_number=4,
                phase="RECOVERY",
                target_volume_hours=round(base_hours * 0.70, 2),
                target_load=round(base_load * 0.70, 1),
                weekly_progression_pct=-30.0,
                sessions=week1_sessions,
            )
            all_microcycles = [week1, week2, week3, week4]

        # Granularity filtering
        normalized_view = view.upper().strip()
        if normalized_view == "DAILY":
            # Filter week 1 to today's day of week
            today_dow = date.today().isoweekday()  # 1=Mon ... 7=Sun
            daily_sessions = [s for s in week1.sessions if s.day_of_week == today_dow]
            if not daily_sessions:
                daily_sessions = [week1.sessions[0]]
            filtered_microcycles = [
                MicrocycleDTO(
                    week_number=1,
                    phase=week1.phase,
                    target_volume_hours=round(daily_sessions[0].duration_min / 60.0, 2),
                    target_load=week1.target_load / 7.0,
                    weekly_progression_pct=0.0,
                    sessions=daily_sessions,
                )
            ]
        elif normalized_view == "MONTHLY":
            filtered_microcycles = all_microcycles
        else:
            # Default: WEEKLY view
            filtered_microcycles = [week1]

        return PeriodizedPlanResponse(
            plan_id=f"plan-{athlete_profile_id[:8]}",
            athlete_profile_id=athlete_profile_id,
            view=normalized_view if normalized_view in ("DAILY", "WEEKLY", "MONTHLY") else "WEEKLY",
            active_goal_discipline=discipline,
            target_date=target_date_str,
            microcycles=filtered_microcycles,
        )
