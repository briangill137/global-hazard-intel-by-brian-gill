from global_hazard_intel.connectors.geocoding import GeocodingConnector
from global_hazard_intel.connectors.live_data import LiveDataConnector
from global_hazard_intel.domain.models import DataSignal
from global_hazard_intel.domain.location import ResolvedLocation


class IngestionBundle:
    def __init__(
        self,
        location: ResolvedLocation,
        signals: list[DataSignal],
        events: list[dict],
        weather: dict[str, float | None],
        air_quality: dict[str, float | None],
        satellite_image_bytes: bytes | None,
    ) -> None:
        self.location = location
        self.signals = signals
        self.events = events
        self.weather = weather
        self.air_quality = air_quality
        self.satellite_image_bytes = satellite_image_bytes


class IngestionService:
    def __init__(self) -> None:
        self.geocoding = GeocodingConnector()
        self.live = LiveDataConnector()

    def collect(self, region: str, mode: str = "auto") -> IngestionBundle:
        location = self.geocoding.resolve(region, mode=mode)
        weather = self.live.fetch_weather(location)
        air_quality = self.live.fetch_air_quality(location)
        events = self.live.fetch_nasa_events(location)
        satellite_image_bytes = self.live.fetch_satellite_image(location)

        signals = [
            DataSignal(
                source="weather",
                metric="wind_speed_10m",
                value=min(1.0, float(weather.get("wind_speed_10m", 0.0)) / 80.0),
                confidence=0.86,
            ),
            DataSignal(
                source="weather",
                metric="wind_gusts_10m",
                value=min(1.0, float(weather.get("wind_gusts_10m", 0.0)) / 100.0),
                confidence=0.83,
            ),
            DataSignal(
                source="air_quality",
                metric="pm2_5",
                value=min(1.0, float(air_quality.get("pm2_5", 0.0)) / 150.0),
                confidence=0.90,
            ),
            DataSignal(
                source="air_quality",
                metric="pm10",
                value=min(1.0, float(air_quality.get("pm10", 0.0)) / 220.0),
                confidence=0.88,
            ),
            DataSignal(
                source="air_quality",
                metric="sulphur_dioxide",
                value=min(1.0, float(air_quality.get("sulphur_dioxide", 0.0)) / 350.0),
                confidence=0.82,
            ),
            DataSignal(
                source="air_quality",
                metric="carbon_monoxide",
                value=min(1.0, float(air_quality.get("carbon_monoxide", 0.0)) / 1500.0),
                confidence=0.80,
            ),
            DataSignal(
                source="air_quality",
                metric="nitrogen_dioxide",
                value=min(1.0, float(air_quality.get("nitrogen_dioxide", 0.0)) / 200.0),
                confidence=0.84,
            ),
            DataSignal(
                source="air_quality",
                metric="dust",
                value=min(1.0, float(air_quality.get("dust", 0.0)) / 300.0),
                confidence=0.87,
            ),
            DataSignal(
                source="air_quality",
                metric="us_aqi",
                value=min(1.0, float(air_quality.get("us_aqi", 0.0)) / 300.0),
                confidence=0.91,
            ),
            DataSignal(
                source="satellite_events",
                metric="wildfire_event_count",
                value=min(1.0, self._count_wildfire_events(events) / 5.0),
                confidence=0.85 if events else 0.55,
            ),
        ]
        return IngestionBundle(
            location=location,
            signals=signals,
            events=events,
            weather=weather,
            air_quality=air_quality,
            satellite_image_bytes=satellite_image_bytes,
        )

    @staticmethod
    def _count_wildfire_events(events: list[dict]) -> int:
        count = 0
        for event in events:
            haystack = " ".join(
                [
                    str(event.get("title", "")),
                    " ".join(category.get("title", "") for category in event.get("categories", [])),
                ]
            ).lower()
            if any(keyword in haystack for keyword in ("wildfire", "fire", "smoke")):
                count += 1
        return count
