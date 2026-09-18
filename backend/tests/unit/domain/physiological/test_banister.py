"""Unit tests for the Banister Impulse-Response EWMA Model and WorkloadMetrics."""

import pytest

from backend.src.domain.exceptions import InvalidLoadError
from backend.src.domain.physiological.banister import BanisterModel, WorkloadMetrics


class TestWorkloadMetrics:
    """Test suite for WorkloadMetrics Value Object."""

    def test_valid_instantiation_computed_tsb_and_fatigue(self) -> None:
        """Test default computation of TSB and is_critical_fatigue."""
        metrics = WorkloadMetrics(
            day_index=1,
            load=100.0,
            ctl=50.0,
            atl=70.0,
        )
        assert metrics.day_index == 1
        assert metrics.load == 100.0
        assert metrics.ctl == 50.0
        assert metrics.atl == 70.0
        assert metrics.tsb == -20.0
        assert metrics.is_critical_fatigue is False

    def test_critical_fatigue_trigger(self) -> None:
        """Test critical fatigue flag when TSB is below -25.0."""
        metrics = WorkloadMetrics(
            day_index=5,
            load=150.0,
            ctl=40.0,
            atl=70.0,
        )
        assert metrics.tsb == -30.0
        assert metrics.is_critical_fatigue is True
        assert "CRITICAL FATIGUE" in str(metrics)

    def test_explicit_tsb_and_fatigue_override(self) -> None:
        """Test instantiation with explicit TSB and explicit flag."""
        metrics = WorkloadMetrics(
            day_index=0,
            load=50.0,
            ctl=30.0,
            atl=30.0,
            tsb=0.0,
            is_critical_fatigue=False,
        )
        assert metrics.tsb == 0.0
        assert metrics.is_critical_fatigue is False
        assert "NORMAL" in str(metrics)

    def test_equality_and_hash(self) -> None:
        """Test value-based equality and hashing."""
        m1 = WorkloadMetrics(day_index=1, load=80.0, ctl=40.0, atl=50.0)
        m2 = WorkloadMetrics(day_index=1, load=80.0, ctl=40.0, atl=50.0)
        m3 = WorkloadMetrics(day_index=2, load=80.0, ctl=40.0, atl=50.0)

        assert m1 == m2
        assert m1 != m3
        assert m1 != "not_a_metric"
        assert hash(m1) == hash(m2)
        assert hash(m1) != hash(m3)
        assert repr(m1) == (
            "WorkloadMetrics(day_index=1, load=80.0, ctl=40.0, atl=50.0, "
            "tsb=-10.0, is_critical_fatigue=False)"
        )

    def test_invalid_day_index_raises_type_error(self) -> None:
        """Test non-integer day_index raises TypeError."""
        with pytest.raises(TypeError, match="day_index must be an integer"):
            WorkloadMetrics(day_index="first", load=50.0, ctl=20.0, atl=20.0)  # type: ignore

        with pytest.raises(TypeError, match="day_index must be an integer"):
            WorkloadMetrics(day_index=True, load=50.0, ctl=20.0, atl=20.0)  # type: ignore

    @pytest.mark.parametrize(
        "load,ctl,atl",
        [
            (-10.0, 50.0, 50.0),
            (50.0, -5.0, 50.0),
            (50.0, 50.0, -1.0),
            ("invalid", 50.0, 50.0),
            (50.0, None, 50.0),
        ],
    )
    def test_invalid_workload_bounds(self, load, ctl, atl) -> None:
        """Test negative or non-numeric values raise InvalidLoadError."""
        with pytest.raises(InvalidLoadError):
            WorkloadMetrics(day_index=0, load=load, ctl=ctl, atl=atl)

    def test_invalid_tsb_type_raises_error(self) -> None:
        """Test non-numeric explicit tsb raises InvalidLoadError."""
        with pytest.raises(InvalidLoadError, match="tsb must be numeric"):
            WorkloadMetrics(day_index=0, load=10.0, ctl=10.0, atl=10.0, tsb="invalid")  # type: ignore


class TestBanisterModel:
    """Test suite for BanisterModel EWMA calculations."""

    @pytest.fixture
    def model(self) -> BanisterModel:
        """Provide a clean BanisterModel instance."""
        return BanisterModel()

    def test_single_step_from_zero_baseline(self, model: BanisterModel) -> None:
        """Test single step calculation starting from zero baseline."""
        # Day 1: 100 load
        # CTL = 0 + (100 - 0) / 42 = 2.38095 -> 2.38
        # ATL = 0 + (100 - 0) / 7 = 14.2857 -> 14.29
        # TSB = 2.38 - 14.29 = -11.91
        result = model.step(current_ctl=0.0, current_atl=0.0, daily_load=100.0, day_index=1)
        assert result.day_index == 1
        assert result.load == 100.0
        assert result.ctl == pytest.approx(2.38, abs=0.01)
        assert result.atl == pytest.approx(14.29, abs=0.01)
        assert result.tsb == pytest.approx(-11.91, abs=0.02)
        assert result.is_critical_fatigue is False

    def test_decay_step_with_zero_load(self, model: BanisterModel) -> None:
        """Test exponential decay on rest days (load = 0)."""
        # Starting CTL = 50.0, ATL = 40.0, Load = 0.0
        # CTL = 50 + (0 - 50)/42 = 50 - 1.19 = 48.81
        # ATL = 40 + (0 - 40)/7 = 40 - 5.71 = 34.29
        # TSB = 48.81 - 34.29 = +14.52 (Form improves as fatigue decays faster)
        result = model.step(current_ctl=50.0, current_atl=40.0, daily_load=0.0, day_index=2)
        assert result.ctl == pytest.approx(48.81, abs=0.01)
        assert result.atl == pytest.approx(34.29, abs=0.01)
        assert result.tsb == pytest.approx(14.52, abs=0.02)
        assert result.tsb > 0.0

    def test_critical_fatigue_detection(self, model: BanisterModel) -> None:
        """Test critical fatigue detection when TSB falls below -25.0."""
        # Athlete with CTL=30 and ATL=40 experiences massive spike of 200 load
        # CTL = 30 + (200 - 30)/42 = 34.05
        # ATL = 40 + (200 - 40)/7 = 62.86
        # TSB = 34.05 - 62.86 = -28.81 (< -25.0)
        result = model.step(current_ctl=30.0, current_atl=40.0, daily_load=200.0, day_index=3)
        assert result.tsb < -25.0
        assert result.is_critical_fatigue is True

    @pytest.mark.parametrize(
        "ctl,atl,load",
        [
            (-1.0, 20.0, 50.0),
            (20.0, -1.0, 50.0),
            (20.0, 20.0, -1.0),
        ],
    )
    def test_step_invalid_negative_arguments_raise_error(
        self, model: BanisterModel, ctl: float, atl: float, load: float
    ) -> None:
        """Test negative step inputs raise InvalidLoadError."""
        with pytest.raises(InvalidLoadError):
            model.step(current_ctl=ctl, current_atl=atl, daily_load=load)

    def test_calculate_series_consecutive_days(self, model: BanisterModel) -> None:
        """Test multi-day sequence calculation over consecutive days."""
        daily_loads = [70.0, 80.0, 0.0, 90.0, 110.0, 60.0, 0.0]
        history = model.calculate_series(
            daily_loads=daily_loads,
            initial_ctl=40.0,
            initial_atl=35.0,
            start_day_index=1,
        )

        assert len(history) == 7
        assert history[0].day_index == 1
        assert history[-1].day_index == 7

        # Ensure state carries over sequentially
        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            expected_ctl = prev.ctl + (curr.load - prev.ctl) / 42.0
            expected_atl = prev.atl + (curr.load - prev.atl) / 7.0
            assert curr.ctl == pytest.approx(expected_ctl, abs=0.01)
            assert curr.atl == pytest.approx(expected_atl, abs=0.01)

    def test_project_future_prospective_simulation(self, model: BanisterModel) -> None:
        """Test prospective future simulation given planned loads."""
        current_ctl = 55.0
        current_atl = 45.0
        planned_loads = [100.0, 120.0, 150.0, 160.0]

        projections = model.project_future(
            current_ctl=current_ctl,
            current_atl=current_atl,
            planned_loads=planned_loads,
            start_day_index=10,
        )

        assert len(projections) == 4
        assert projections[0].day_index == 10
        assert projections[-1].day_index == 13

        # Severe acute loading should progressively drive TSB downwards
        assert projections[-1].tsb < projections[0].tsb
