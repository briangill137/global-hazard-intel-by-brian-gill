from datetime import datetime

from global_hazard_intel.domain.monitoring import MonitoringSnapshot, SnapshotRecord
from global_hazard_intel.domain.models import DetectionResponse
from global_hazard_intel.services.analytics import AnalyticsService
from global_hazard_intel.services.detection import DetectionService
from global_hazard_intel.services.ingestion import IngestionService
from global_hazard_intel.storage.repository import HazardRepository


class HazardOrchestrator:
    def __init__(self) -> None:
        self.ingestion = IngestionService()
        self.detection = DetectionService()
        self.analytics = AnalyticsService()
        self.repository = HazardRepository()
        self.snapshot_history: list[SnapshotRecord] = []

    def run_detection(self, region: str, mode: str = "auto") -> DetectionResponse:
        bundle = self.ingestion.collect(region, mode=mode)
        hazards = self.detection.detect(region, bundle.location, bundle.signals)
        persisted = self.repository.save_all(hazards)
        return DetectionResponse(region=region, resolved_location=bundle.location, hazards=persisted)

    def run_snapshot(self, region: str, mode: str = "auto") -> MonitoringSnapshot:
        bundle = self.ingestion.collect(region, mode=mode)
        hazards = self.detection.detect(region, bundle.location, bundle.signals)
        persisted = self.repository.save_all(hazards)
        analytics = self.analytics.build(
            hazards=persisted,
            signals=bundle.signals,
            weather=bundle.weather,
            air_quality=bundle.air_quality,
            nasa_events=bundle.events,
        )
        record = SnapshotRecord(
            captured_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            location_name=bundle.location.display_name,
            top_hazard=persisted[0].hazard_type.value if persisted else "none",
            top_severity=max((hazard.severity for hazard in persisted), default=0.0),
            health_exposure_score=analytics.health.exposure_score,
            weather_operations_score=analytics.weather.operations_score,
            observation_utility_score=analytics.scientific.observation_utility_score,
        )
        self.snapshot_history.append(record)
        self.snapshot_history = self.snapshot_history[-25:]
        return MonitoringSnapshot(
            query=region,
            mode=mode,
            location=bundle.location,
            hazards=persisted,
            signals=bundle.signals,
            weather=bundle.weather,
            air_quality=bundle.air_quality,
            nasa_events=bundle.events,
            analytics=analytics,
            history=list(self.snapshot_history),
            satellite_image_bytes=bundle.satellite_image_bytes,
        )

    def list_hazards(self) -> list:
        return self.repository.list_all()
