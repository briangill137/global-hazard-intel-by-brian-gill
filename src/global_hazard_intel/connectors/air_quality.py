from global_hazard_intel.domain.models import DataSignal


class AirQualityConnector:
    def fetch(self, region: str) -> list[DataSignal]:
        return [
            DataSignal(
                source="air_quality",
                metric="pm25_spike",
                value=0.91,
                confidence=0.88,
            ),
            DataSignal(
                source="air_quality",
                metric="so2_anomaly",
                value=0.73,
                confidence=0.77,
            ),
        ]
