from urllib.parse import quote_plus

import httpx

from global_hazard_intel.domain.location import ResolvedLocation

CONTINENT_PRESETS: dict[str, ResolvedLocation] = {
    "global": ResolvedLocation(
        query="global",
        display_name="Global",
        latitude=20.0000,
        longitude=0.0000,
        bbox=(-179.0000, -60.0000, 179.0000, 75.0000),
        source="preset",
    ),
    "europe": ResolvedLocation(
        query="Europe",
        display_name="Europe",
        latitude=54.5260,
        longitude=15.2551,
        bbox=(-31.2660, 34.5000, 39.8690, 71.1850),
        source="preset",
    ),
    "asia": ResolvedLocation(
        query="Asia",
        display_name="Asia",
        latitude=34.0479,
        longitude=100.6197,
        bbox=(25.9740, -10.3590, 179.6870, 81.8510),
        source="preset",
    ),
    "north america": ResolvedLocation(
        query="North America",
        display_name="North America",
        latitude=54.5260,
        longitude=-105.2551,
        bbox=(-168.0000, 5.5000, -52.0000, 83.5000),
        source="preset",
    ),
    "south america": ResolvedLocation(
        query="South America",
        display_name="South America",
        latitude=-8.7832,
        longitude=-55.4915,
        bbox=(-92.0000, -56.0000, -34.0000, 13.0000),
        source="preset",
    ),
    "africa": ResolvedLocation(
        query="Africa",
        display_name="Africa",
        latitude=1.6508,
        longitude=17.6791,
        bbox=(-25.5000, -35.0000, 63.0000, 37.5000),
        source="preset",
    ),
    "australia": ResolvedLocation(
        query="Australia",
        display_name="Australia",
        latitude=-25.2744,
        longitude=133.7751,
        bbox=(112.0000, -44.0000, 154.0000, -10.0000),
        source="preset",
    ),
}


class GeocodingError(RuntimeError):
    pass


class GeocodingConnector:
    def __init__(self) -> None:
        self.client = httpx.Client(
            timeout=20.0,
            headers={"User-Agent": "GlobalHazardIntel/0.1 (geocoding client)"},
        )

    def resolve(self, query: str, mode: str = "auto") -> ResolvedLocation:
        normalized = query.strip()
        if not normalized:
            raise GeocodingError("Location query is required.")

        preset = CONTINENT_PRESETS.get(normalized.lower())
        if preset:
            return preset.model_copy(update={"query": normalized})

        if mode == "coords":
            return self._resolve_coordinates(normalized)

        if mode == "address" or any(char.isdigit() for char in normalized):
            return self._resolve_with_nominatim(normalized)

        try:
            return self._resolve_with_open_meteo(normalized)
        except GeocodingError:
            return self._resolve_with_nominatim(normalized)

    def _resolve_with_open_meteo(self, query: str) -> ResolvedLocation:
        encoded = quote_plus(query)
        response = self.client.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=en&format=json"
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            raise GeocodingError(f"No geocoding match found for '{query}'.")

        result = results[0]
        bbox = (
            float(result.get("longitude", 0.0)) - 2.5,
            float(result.get("latitude", 0.0)) - 2.5,
            float(result.get("longitude", 0.0)) + 2.5,
            float(result.get("latitude", 0.0)) + 2.5,
        )
        return ResolvedLocation(
            query=query,
            display_name=self._compose_name(
                result.get("name"),
                result.get("admin1"),
                result.get("country"),
            ),
            latitude=float(result["latitude"]),
            longitude=float(result["longitude"]),
            bbox=bbox,
            country=result.get("country"),
            admin1=result.get("admin1"),
            source="open-meteo-geocoding",
        )

    def _resolve_with_nominatim(self, query: str) -> ResolvedLocation:
        encoded = quote_plus(query)
        response = self.client.get(
            f"https://nominatim.openstreetmap.org/search?q={encoded}&format=jsonv2&limit=1"
        )
        response.raise_for_status()
        payload = response.json()
        if not payload:
            raise GeocodingError(f"No address match found for '{query}'.")

        result = payload[0]
        bbox_values = [float(value) for value in result["boundingbox"]]
        bbox = (bbox_values[2], bbox_values[0], bbox_values[3], bbox_values[1])
        address = result.get("address", {})
        return ResolvedLocation(
            query=query,
            display_name=result["display_name"],
            latitude=float(result["lat"]),
            longitude=float(result["lon"]),
            bbox=bbox,
            country=address.get("country"),
            admin1=address.get("state"),
            source="nominatim",
        )

    @staticmethod
    def _compose_name(name: str | None, admin1: str | None, country: str | None) -> str:
        parts = [part for part in [name, admin1, country] if part]
        return ", ".join(parts)

    @staticmethod
    def _resolve_coordinates(query: str) -> ResolvedLocation:
        try:
            latitude_text, longitude_text = [part.strip() for part in query.split(",", maxsplit=1)]
            latitude = float(latitude_text)
            longitude = float(longitude_text)
        except (TypeError, ValueError) as error:
            raise GeocodingError("Coordinates must be in 'latitude,longitude' format.") from error

        return ResolvedLocation(
            query=query,
            display_name=f"Custom Coordinates ({latitude}, {longitude})",
            latitude=latitude,
            longitude=longitude,
            bbox=(longitude - 2.5, latitude - 2.5, longitude + 2.5, latitude + 2.5),
            source="coordinates",
        )
