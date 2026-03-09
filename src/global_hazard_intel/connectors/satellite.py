from global_hazard_intel.domain.models import DataSignal


class SatelliteConnector:
    def fetch(self, region: str) -> list[DataSignal]:
        return [
            DataSignal(
                source="satellite",
                metric="aerosol_density",
                value=0.82,
                confidence=0.87,
            ),
            DataSignal(
                source="satellite",
                metric="thermal_anomaly",
                value=0.76,
                confidence=0.84,
            ),
        ]
