from global_hazard_intel.domain.models import DataSignal


class WeatherConnector:
    def fetch(self, region: str) -> list[DataSignal]:
        return [
            DataSignal(
                source="weather",
                metric="wind_transport_risk",
                value=0.71,
                confidence=0.80,
            ),
            DataSignal(
                source="weather",
                metric="stagnation_index",
                value=0.68,
                confidence=0.79,
            ),
        ]
