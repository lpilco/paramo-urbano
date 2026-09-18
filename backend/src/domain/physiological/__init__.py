"""Páramo Urbano Physiological and Deterministic Biomechanical Engine.

Exposes domain models, value objects, and deterministic evaluation engines
for:
- Banister EWMA Impulse Response (CTL, ATL, TSB, prospective simulations)
- Gabbett's ACWR (Sweet Spot, Caution, and Critical Injury Risk zones)
- Session Training Load quantification (Foster sRPE, rTSS, hrTSS)
- Altitude Barometric Hysteresis Filtering (+D cumulative ascent)
- Daniels & Gilbert VDOT and Pace Zones with GPS tolerance
"""

from .acwr import ACWREvaluator, ACWRStatus, ACWRZone
from .altitude_filter import AltitudeHysteresisFilter, ElevationGainResult
from .banister import BanisterModel, WorkloadMetrics
from .session_load import LoadCalculationMethod, SessionLoad, SessionLoadCalculator
from .vdot import PaceZone, VDOTCalculator, VDOTPrescription

__all__ = [
    # Banister
    "BanisterModel",
    "WorkloadMetrics",
    # ACWR
    "ACWREvaluator",
    "ACWRStatus",
    "ACWRZone",
    # Session Load
    "SessionLoadCalculator",
    "SessionLoad",
    "LoadCalculationMethod",
    # Altitude Filter
    "AltitudeHysteresisFilter",
    "ElevationGainResult",
    # VDOT
    "VDOTCalculator",
    "VDOTPrescription",
    "PaceZone",
]
