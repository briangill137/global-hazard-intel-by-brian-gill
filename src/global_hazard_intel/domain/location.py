from pydantic import BaseModel


class ResolvedLocation(BaseModel):
    query: str
    display_name: str
    latitude: float
    longitude: float
    bbox: tuple[float, float, float, float]
    country: str | None = None
    admin1: str | None = None
    source: str
