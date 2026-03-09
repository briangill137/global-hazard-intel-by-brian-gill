import httpx

from global_hazard_intel.domain.location import ResolvedLocation


class LiveDataConnector:
    def __init__(self) -> None:
        self.client = httpx.Client(
            timeout=30.0,
            headers={"User-Agent": "GlobalHazardIntel/0.1 (live data client)"},
        )

    def fetch_weather(self, location: ResolvedLocation) -> dict[str, float | None]:
        params = (
            "latitude={lat}&longitude={lon}&current="
            "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,"
            "wind_speed_10m,wind_gusts_10m,wind_direction_10m"
        ).format(lat=location.latitude, lon=location.longitude)
        response = self.client.get(f"https://api.open-meteo.com/v1/forecast?{params}")
        response.raise_for_status()
        return response.json().get("current", {})

    def fetch_air_quality(self, location: ResolvedLocation) -> dict[str, float | None]:
        params = (
            "latitude={lat}&longitude={lon}&current="
            "european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
            "sulphur_dioxide,ozone,dust"
        ).format(lat=location.latitude, lon=location.longitude)
        response = self.client.get(f"https://air-quality-api.open-meteo.com/v1/air-quality?{params}")
        response.raise_for_status()
        return response.json().get("current", {})

    def fetch_nasa_events(self, location: ResolvedLocation) -> list[dict]:
        west, south, east, north = location.bbox
        url = (
            "https://eonet.gsfc.nasa.gov/api/v3/events"
            f"?status=open&days=30&bbox={west},{south},{east},{north}"
        )
        response = self.client.get(url)
        response.raise_for_status()
        return response.json().get("events", [])

    def fetch_satellite_image(self, location: ResolvedLocation) -> bytes | None:
        west, south, east, north = location.bbox
        width = max(0.8, abs(east - west))
        height = max(0.8, abs(north - south))
        scale = 1.5 if max(width, height) < 8 else 1.0
        bbox = (
            location.longitude - width * scale / 2,
            location.latitude - height * scale / 2,
            location.longitude + width * scale / 2,
            location.latitude + height * scale / 2,
        )
        url = (
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            f"?bbox={bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            "&bboxSR=4326&imageSR=4326&size=900,450&format=png32&transparent=false&f=image"
        )
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return response.content
        except Exception:
            return None
