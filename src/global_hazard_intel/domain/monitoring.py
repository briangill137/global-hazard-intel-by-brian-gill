from dataclasses import dataclass

from global_hazard_intel.domain.location import ResolvedLocation
from global_hazard_intel.domain.models import DataSignal, HazardEvent
from global_hazard_intel.services.analytics import AnalyticsBundle


@dataclass(slots=True)
class SnapshotRecord:
    captured_at: str
    location_name: str
    top_hazard: str
    top_severity: float
    health_exposure_score: float
    weather_operations_score: float
    observation_utility_score: float


@dataclass(slots=True)
class MonitoringSnapshot:
    query: str
    mode: str
    location: ResolvedLocation
    hazards: list[HazardEvent]
    signals: list[DataSignal]
    weather: dict[str, float | None]
    air_quality: dict[str, float | None]
    nasa_events: list[dict]
    analytics: AnalyticsBundle
    history: list[SnapshotRecord]
    satellite_image_bytes: bytes | None = None
