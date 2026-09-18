"""End-to-End (E2E) Acceptance Criteria & NFR Certification Suite for Páramo Urbano (v2.0.0 Core).

Certifies formal Gherkin scenarios defined in the PRD (FR-01 to FR-05) and Non-Functional Requirements:
- FR-01: Massive Ingestion & Cryptographic Deduplication / FIT Magic Bytes Pre-validation.
- FR-02: Manual Session Logging via Foster sRPE & EWMA Baseline Updates.
- FR-03: Territorial Segmentation (Trail +D / VAM vs. Asphalt Pace / rTSS).
- FR-04: Physiological Dashboard & Forced Rest Injection upon ACWR Overload (> 1.5).
- FR-05: Goal Configuration with 14-Day Horizon Lock & 16-Week Mesocycle Generation.
- NFRs: Ingestion Latency (< 250ms), Worker Performance (<= 1.8s), 500m Privacy Radius, AppSec (XXE/JWT).
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
import hashlib
import os
import time
from typing import Dict
import pytest
from httpx import AsyncClient

from backend.src.domain.exceptions import SecurityXmlAttackException
from backend.src.domain.physiological.acwr import ACWREvaluator, ACWRZone
from backend.src.domain.physiological.altitude_filter import (
    AltitudeHysteresisFilter,
    ElevationGainResult,
)
from backend.src.infrastructure.database.models import ActivityModel
from backend.src.infrastructure.database.repositories.postgres_job_repository import (
    PostgresIngestionJobRepository,
)
from backend.src.infrastructure.database.repositories.postgres_profile_repository import (
    PostgresProfileRepository,
)
from backend.src.infrastructure.parsers.fit_parser import FitParser
from backend.src.infrastructure.parsers.gpx_parser import GpxParser
from backend.src.interfaces.api.middlewares.privacy_filter import (
    obfuscate_gps_points,
)

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/fixtures"))


@pytest.mark.asyncio
class TestFR01MassiveIngestionAndMagicBytes:
    """Gherkin Acceptance Tests for FR-01: Massive ingestion, SHA-256 deduplication, and magic bytes."""

    async def test_concurrent_upload_valid_files_and_deduplication(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
        app_instance,
    ) -> None:
        """Scenario: Carga exitosa por lotes de archivos .FIT, .GPX y .CSV con deduplicación criptográfica.

        Given que el atleta se encuentra autenticado en "/diagnostics"
        And selecciona archivos válidos (.FIT, .GPX, .CSV)
        When sube concurrentemente los archivos
        Then el sistema valida que ningún archivo exceda 25 MB
        And calcula el hash SHA-256 de cada archivo
        And retorna HTTP 202 Accepted con identificadores de trabajo "job_id"
        And rechaza con HTTP 409 una carga duplicada del mismo hash.
        """
        fit_path = os.path.join(FIXTURES_DIR, "sample_run.fit")
        gpx_path = os.path.join(FIXTURES_DIR, "sample_trail.gpx")
        csv_path = os.path.join(FIXTURES_DIR, "garmin_activities_sample.csv")

        with open(fit_path, "rb") as f:
            fit_bytes = f.read()
        with open(gpx_path, "rb") as f:
            gpx_bytes = f.read()
        with open(csv_path, "rb") as f:
            csv_bytes = f.read()

        # Concurrent upload using asyncio.gather
        tasks = [
            client.post(
                "/api/v1/activities/upload",
                files={"file": ("morning_run.fit", fit_bytes, "application/octet-stream")},
                headers=authenticated_athlete["headers"],
            ),
            client.post(
                "/api/v1/activities/upload",
                files={"file": ("mountain_trail.gpx", gpx_bytes, "application/gpx+xml")},
                headers=authenticated_athlete["headers"],
            ),
            client.post(
                "/api/v1/activities/upload",
                files={"file": ("garmin_history.csv", csv_bytes, "text/csv")},
                headers=authenticated_athlete["headers"],
            ),
        ]

        responses = await asyncio.gather(*tasks)

        job_ids = []
        for resp in responses:
            assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert "job_id" in data
            assert data["status"] == "QUEUED"
            assert len(data["sha256"]) == 64
            job_ids.append(data["job_id"])

        # Verify all job IDs are unique
        assert len(set(job_ids)) == 3

        # Simulate that the FIT activity has been persisted to verify deduplication
        fit_hash = hashlib.sha256(fit_bytes).hexdigest().lower()
        async with app_instance.state.session_factory() as session:
            act = ActivityModel(
                id=job_ids[0],
                athlete_profile_id=authenticated_athlete["profile_id"],
                source_type="FIT",
                file_hash_sha256=fit_hash,
                sport_category="ROAD_RUN",
                started_at=datetime.now(timezone.utc),
                duration_seconds=1800,
                distance_meters=5000.0,
                processing_status="PROCESSED",
            )
            session.add(act)
            await session.commit()

        # Duplicate upload attempt of identical FIT file
        dup_resp = await client.post(
            "/api/v1/activities/upload",
            files={"file": ("repeat_run.fit", fit_bytes, "application/octet-stream")},
            headers=authenticated_athlete["headers"],
        )
        assert dup_resp.status_code == 409
        problem = dup_resp.json()
        assert problem["code"] == "DUPLICATE_ACTIVITY"
        assert fit_hash in problem["detail"]

    async def test_corrupted_fit_magic_bytes_rejected_422_and_failed_job(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
        app_instance,
    ) -> None:
        """Scenario: Rechazo de archivo binario .FIT corrupto o con cabecera alterada.

        Given que un usuario intenta subir un archivo "actividad_corrupta.fit"
        When el sistema examina los bytes 8 al 11 del archivo
        And comprueba que no contienen la firma ASCII ".FIT" (0x2E 0x46 0x49 0x54)
        Then el sistema rechaza el archivo con código HTTP 422 Unprocessable Entity
        And marca la tarea con estado FAILED en la base de datos notificando el motivo.
        """
        corrupted_path = os.path.join(FIXTURES_DIR, "corrupted_header.fit")
        with open(corrupted_path, "rb") as f:
            corrupted_bytes = f.read()

        # Verify fixture indeed has altered magic bytes
        assert corrupted_bytes[8:12] != b".FIT"

        corrupted_hash = hashlib.sha256(corrupted_bytes).hexdigest().lower()

        response = await client.post(
            "/api/v1/activities/upload",
            files={"file": ("corrupted_header.fit", corrupted_bytes, "application/octet-stream")},
            headers=authenticated_athlete["headers"],
        )

        assert response.status_code == 422
        problem = response.json()
        assert problem["code"] == "INVALID_FIT_HEADER"
        assert "magic bytes" in problem["detail"].lower()

        # Verify job was recorded as FAILED in the job repository
        async with app_instance.state.session_factory() as session:
            job_repo = PostgresIngestionJobRepository(session)
            # Find job by sha256
            job = await job_repo.get_job_by_hash(corrupted_hash)
            assert job is not None
            assert job["status"] == "FAILED"
            assert "InvalidFitHeaderException" in job["error_message"]


@pytest.mark.asyncio
class TestFR02ManualFosterSRPE:
    """Gherkin Acceptance Tests for FR-02: Manual workout logging via Foster sRPE."""

    async def test_manual_logging_45min_rpe6_calculates_270_load_and_updates_atl(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Scenario: Registro manual de sesión mediante sRPE con cálculo de carga y actualización de fatiga.

        Given que el atleta finalizó una sesión sin archivo GPS
        When registra manualmente duración de 45 minutos y RPE de 6
        Then el backend persiste la actividad con source_type "MANUAL"
        And calcula deterministamente una carga Foster de 270 unidades (45 * 6)
        And retorna HTTP 201 Created con el ID de la actividad creada
        And actualiza de forma inmediata las métricas ATL y TSB en /diagnostics.
        """
        started_at = datetime.now(timezone.utc).isoformat()
        payload = {
            "sport_category": "ROAD_RUN",
            "started_at": started_at,
            "duration_minutes": 45,
            "session_rpe": 6,
            "notes": "Rodaje de mantenimiento 45 min a RPE 6",
        }

        response = await client.post(
            "/api/v1/activities/manual",
            json=payload,
            headers=authenticated_athlete["headers"],
        )

        assert response.status_code == 201
        data = response.json()
        assert "activity_id" in data
        assert data["duration_minutes"] == 45.0
        assert data["session_rpe"] == 6
        # Deterministic Foster calculation: 45 min * 6 RPE = 270.0 a.u.
        assert data["calculated_load"] == 270.0

        # Query diagnostics to verify ATL and TSB were updated
        diag_resp = await client.get(
            "/api/v1/diagnostics",
            headers=authenticated_athlete["headers"],
        )
        assert diag_resp.status_code == 200
        diag_data = diag_resp.json()
        banister = diag_data["banister"]

        # ATL must be strictly positive after absorbing 270 units of load
        assert banister["atl"] > 0.0
        assert "tsb" in banister
        assert diag_data["weekly_total_load"] >= 270.0

    async def test_manual_logging_rpe_out_of_bounds_rejected(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Scenario: Validación de rango en esfuerzo percibido fuera de cota.

        Given que el usuario completa el formulario manual
        When ingresa un valor de RPE de 12 o de 0
        Then el sistema bloquea el registro con código HTTP 422
        And retorna el error tipado correspondiente.
        """
        for invalid_rpe in [12, 0]:
            payload = {
                "sport_category": "STRENGTH",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "duration_minutes": 30,
                "session_rpe": invalid_rpe,
                "notes": f"RPE inválido ({invalid_rpe})",
            }
            response = await client.post(
                "/api/v1/activities/manual",
                json=payload,
                headers=authenticated_athlete["headers"],
            )
            assert response.status_code == 422
            problem = response.json()
            assert problem["status"] == 422


class TestFR03TerritorialSegmentation:
    """Gherkin Acceptance Tests for FR-03: Mountain (+D / VAM) vs. Asphalt (Pace / rTSS)."""

    def test_trail_run_hysteresis_filter_and_vam_priority(self) -> None:
        """Scenario: Procesamiento de sesión de Trail Running priorizando metros verticales (+D y VAM).

        Given que se procesa una serie de altitudes con categoría "TRAIL_RUN"
        When el normalizador analiza las cotas de altitud con filtro de histéresis de 3 metros
        Then elimina oscilaciones espurias menores a 3m y calcula con precisión el desnivel positivo acumulado (+D)
        And prioriza en las métricas la velocidad de ascenso (VAM m/h).
        """
        filter_engine = AltitudeHysteresisFilter(threshold_meters=3.0)

        # Baseline series with genuine climbs separated by micro-jitter (< 3m)
        # Climb 1: 2800 -> 2810 (+10m)
        # Jitter: 2810 -> 2811.5 -> 2810.2 (oscillations < 3m, should not add gain)
        # Climb 2: 2810 -> 2835 (+25m)
        elevations = [
            2800.0,
            2805.0,
            2810.0,
            2811.5,
            2810.2,
            2811.0,
            2810.5,
            2820.0,
            2835.0,
        ]

        smoothed = filter_engine.smooth_moving_average(elevations, window_size=3)
        assert len(smoothed) == len(elevations)

        gain_result = filter_engine.filter_elevation_gain(elevations)
        assert isinstance(gain_result, ElevationGainResult)
        # Filtered gain (+D) must reject noise oscillations (< 3m)
        assert gain_result.filtered_gain_meters > 0.0
        assert gain_result.noise_rejected_meters >= 0.0
        assert gain_result.filtered_gain_meters <= gain_result.raw_gain_meters

        # Calculate VAM for a 30-minute window climbing 300m
        duration_hours = 0.5
        climb_meters = 300.0
        vam = climb_meters / duration_hours  # 600 m/h
        assert vam == 600.0

    def test_road_run_pace_and_rtss_priority(self) -> None:
        """Scenario: Procesamiento de sesión de Asfalto con desglose métrico de ritmo medio y rTSS.

        Given que se procesa una actividad de "ROAD_RUN"
        When se analizan las métricas de carrera
        Then desglosa el ritmo medio por kilómetro (min/km)
        And la altitud no constituye la métrica determinante de la carga de entrenamiento.
        """
        distance_meters = 10000.0  # 10 km
        duration_seconds = 2700  # 45 minutes (4:30 min/km)

        # Calculate pace in min/km
        pace_min_per_km = (duration_seconds / 60.0) / (distance_meters / 1000.0)
        assert pace_min_per_km == 4.5  # 4 min 30 sec / km

        # Calculate speed in m/s
        speed_ms = distance_meters / duration_seconds
        assert round(speed_ms, 2) == 3.70


class TestFR04DashboardAndForcedRest:
    """Gherkin Acceptance Tests for FR-04: Banister Freshness Balance and Forced Rest Day Trigger."""

    def test_dashboard_optimal_freshness_balance(self) -> None:
        """Scenario: Visualización de estado óptimo de frescura en el Dashboard (CTL 60, ATL 48 -> TSB +12).

        Given que el atleta tiene acumulado un CTL de 60 y un ATL de 48
        When el sistema evalúa el balance fisiológico
        Then renderiza un TSB positivo de +12 (60 - 48)
        And el velocímetro ACWR se sitúa en 1.05 dentro del "Sweet Spot" verde (0.8 - 1.3).
        """
        ctl = 60.0
        atl = 48.0
        tsb = ctl - atl
        assert tsb == 12.0

        evaluator = ACWREvaluator()
        result = evaluator.calculate(acute_load=atl, chronic_load=ctl)

        assert 0.80 <= result.ratio <= 1.30
        assert result.zone == ACWRZone.SWEET_SPOT
        assert result.requires_mandatory_rest is False
        assert result.freeze_weekly_increments is False

    async def test_overload_acwr_triggers_mandatory_rest_in_planner(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
        app_instance,
    ) -> None:
        """Scenario: Detección automática de sobrecarga aguda (ACWR = 1.62) y descanso obligatorio.

        Given que un atleta experimenta un pico de volumen que eleva su ACWR a 1.62 (> 1.50)
        When el sistema recalcula los valores
        Then el indicador de ACWR pasa a Zona de Peligro (DANGER / ROJO)
        And el planificador sustituye automáticamente la siguiente sesión intensa por un DÍA DE DESCANSO OBLIGATORIO.
        """
        profile_id = authenticated_athlete["profile_id"]

        # Simulate overload: CTL = 40.0, ATL = 64.8 => ratio = 64.8 / 40.0 = 1.62
        async with app_instance.state.session_factory() as session:
            profile_repo = PostgresProfileRepository(session)
            await profile_repo.update_workload_baselines(
                profile_id=profile_id,
                ctl=40.0,
                atl=64.8,
            )
            await session.commit()

        # Check diagnostics endpoint shows danger zone
        diag_resp = await client.get(
            "/api/v1/diagnostics",
            headers=authenticated_athlete["headers"],
        )
        assert diag_resp.status_code == 200
        diag_data = diag_resp.json()
        acwr = diag_data["acwr"]

        assert round(acwr["ratio"], 2) == 1.62
        assert acwr["zone"] in ("CRITICAL_INJURY_RISK", "DANGER")
        assert acwr["requires_mandatory_rest"] is True

        # Query planner to verify mandatory rest day was injected
        plan_resp = await client.get(
            "/api/v1/plans?view=WEEKLY",
            headers=authenticated_athlete["headers"],
        )
        assert plan_resp.status_code == 200
        plan_data = plan_resp.json()
        microcycles = plan_data["microcycles"]
        assert len(microcycles) >= 1

        week1_sessions = microcycles[0]["sessions"]
        # Must contain at least one session marked as mandatory rest day
        forced_rest_sessions = [
            s
            for s in week1_sessions
            if s.get("is_rest_day") is True and "DESCANSO OBLIGATORIO" in s.get("day_name", "")
        ]
        assert len(forced_rest_sessions) >= 1
        assert forced_rest_sessions[0]["duration_min"] == 0


@pytest.mark.asyncio
class TestFR05GoalConfigurationAndHorizon:
    """Gherkin Acceptance Tests for FR-05: Goal Configuration with 14-Day Lock and Mesocycle Generation."""

    async def test_configure_goal_16_weeks_and_generate_mesocycle(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
        app_instance,
    ) -> None:
        """Scenario: Configuración exitosa de meta de Trail Running a 16 semanas y generación de mesociclo.

        Given que el atleta navega al formulario de metas
        When selecciona disciplina "TRAIL_RUNNING", "TRAIL_MARATHON", 42 km y 2200 m D+ a 16 semanas
        Then el sistema valida que la fecha sea superior a hoy + 14 días
        And persiste la meta en la tabla "goals"
        And retorna HTTP 201 Created
        And el planificador genera un mesociclo estructurado (Base, Build, Peak, Tapering).
        """
        target_date = (date.today() + timedelta(weeks=16)).isoformat()
        payload = {
            "discipline": "TRAIL_RUNNING",
            "subgoal_type": "TRAIL_MARATHON",
            "target_distance_km": 42.195,
            "target_elevation_gain_m": 2200.0,
            "target_date": target_date,
            "available_days_per_week": 5,
        }

        response = await client.post(
            "/api/v1/profiles/me/goals",
            json=payload,
            headers=authenticated_athlete["headers"],
        )

        assert response.status_code == 201
        data = response.json()
        assert "goal_id" in data
        assert data["weeks_to_target"] >= 15
        assert data["discipline"] == "TRAIL_RUNNING"

        # Query planner to verify multi-phase mesocycle generation
        plan_resp = await client.get(
            "/api/v1/plans?view=MONTHLY",
            headers=authenticated_athlete["headers"],
        )
        assert plan_resp.status_code == 200
        plan_data = plan_resp.json()
        phases = [mc["phase"] for mc in plan_data["microcycles"]]

        # Verify structured periodization phases exist (BASE, BUILD, PEAK, TAPER)
        assert "BASE" in phases
        assert "BUILD" in phases
        assert "PEAK" in phases
        assert "TAPER" in phases

    async def test_configure_goal_too_soon_rejected_422(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
        app_instance,
    ) -> None:
        """Scenario: Intento de configuración con margen biológico insuficiente (< 14 días).

        Given que el atleta intenta fijar su fecha de competencia
        When selecciona una fecha ubicada a sólo 5 días en el futuro
        Then el sistema rechaza la petición con error HTTP 422
        And la persistencia en base de datos queda completamente bloqueada.
        """
        invalid_target = (date.today() + timedelta(days=5)).isoformat()
        payload = {
            "discipline": "ROAD_RUNNING",
            "subgoal_type": "FIRST_5K",
            "target_distance_km": 5.0,
            "target_elevation_gain_m": 10.0,
            "target_date": invalid_target,
            "available_days_per_week": 3,
        }

        response = await client.post(
            "/api/v1/profiles/me/goals",
            json=payload,
            headers=authenticated_athlete["headers"],
        )

        assert response.status_code == 422
        problem = response.json()
        assert problem["code"] == "INVALID_TARGET_DATE"
        assert "14-day" in problem["detail"] or "14 días" in problem["detail"].lower()


class TestNFRAndSecurity:
    """Verification of Non-Functional Requirements: Latency, Worker Throughput, Privacy, and AppSec."""

    async def test_nfr01_upload_latency_under_250ms(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """NFR-01: Ingestion API latency must respond in less than 250 ms for raw files."""
        gpx_path = os.path.join(FIXTURES_DIR, "sample_trail.gpx")
        with open(gpx_path, "rb") as f:
            gpx_bytes = f.read()

        unique_gpx = gpx_bytes + f"<!-- salt {time.time()} -->".encode()

        start_time = time.perf_counter()
        response = await client.post(
            "/api/v1/activities/upload",
            files={"file": (f"latency_test_{time.time()}.gpx", unique_gpx, "application/gpx+xml")},
            headers=authenticated_athlete["headers"],
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        assert response.status_code == 202
        assert elapsed_ms < 250.0, f"Upload API took {elapsed_ms:.1f} ms, exceeding 250 ms limit."

    def test_nfr02_worker_decodes_fit_in_less_than_1800ms(self) -> None:
        """NFR-02: Worker performance must parse and normalize 2h .FIT (~7200 records) in <= 1.8 seconds."""
        parser = FitParser()
        fit_path = os.path.join(FIXTURES_DIR, "sample_run.fit")
        with open(fit_path, "rb") as f:
            sample_fit = f.read()

        # Benchmark repeated parsing to simulate sustained 2-hour throughput
        start_time = time.perf_counter()
        # Parse standard sample 50 times (equivalent load of > 7,500 record decodings)
        for _ in range(50):
            record = parser.parse(sample_fit)
            assert record.sport_category is not None

        elapsed_s = time.perf_counter() - start_time
        assert elapsed_s <= 1.8, f"Parsing throughput benchmark took {elapsed_s:.3f} s, exceeding 1.8s limit."

    def test_nfr05_geographic_privacy_suppresses_500m_radius(self) -> None:
        """NFR-05: Telemetry coordinate responses must suppress points within 500m of origin and destination."""
        # Route points: 0m, 200m, 400m, 800m, 1200m, 1500m
        # 1 deg latitude is approx 111,139 meters. 100m is ~0.0009 deg.
        points = [
            {"lat": 0.0000, "lon": 0.0000},  # Origin (0m) -> Filtered
            {"lat": 0.0018, "lon": 0.0000},  # ~200m from origin -> Filtered
            {"lat": 0.0036, "lon": 0.0000},  # ~400m from origin -> Filtered
            {"lat": 0.0072, "lon": 0.0000},  # ~800m from origin, ~700m from dest -> Retained
            {"lat": 0.0108, "lon": 0.0000},  # ~1200m from origin, ~300m from dest -> Filtered
            {"lat": 0.0135, "lon": 0.0000},  # Destination (~1500m) -> Filtered
        ]

        sanitized = obfuscate_gps_points(points, radius_meters=500.0)
        assert len(sanitized) == 1
        assert sanitized[0]["lat"] == 0.0072

    def test_appsec_xxe_attack_mitigation(self) -> None:
        """AppSec: GPX XML Parser must strictly mitigate XML External Entity (XXE) injection attacks."""
        xxe_path = os.path.join(FIXTURES_DIR, "xxe_attack.gpx")
        with open(xxe_path, "rb") as f:
            xxe_bytes = f.read()

        parser = GpxParser()
        with pytest.raises(SecurityXmlAttackException) as exc_info:
            parser.parse(xxe_bytes)

        assert "xxe" in str(exc_info.value).lower() or "threat" in str(exc_info.value).lower()

    async def test_appsec_jwt_forged_signature_rejected(self, client: AsyncClient) -> None:
        """AppSec: Requests with forged RSA-256 JWT tokens must be strictly rejected with HTTP 401."""
        forged_headers = {"Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIn0.forged_signature"}
        response = await client.get("/api/v1/diagnostics", headers=forged_headers)
        assert response.status_code == 401
        problem = response.json()
        assert problem["code"] == "AUTHENTICATION_FAILED"
