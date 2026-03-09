from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from global_hazard_intel.domain.location import ResolvedLocation


class HazardType(str, Enum):
    DUST_STORM = "dust_storm"
    WILDFIRE_SMOKE = "wildfire_smoke"
    CHEMICAL_LEAK = "chemical_leak"
    POLLUTION_SPIKE = "pollution_spike"


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class DataSignal(BaseModel):
    source: str
    metric: str
    value: float
    confidence: float = Field(ge=0.0, le=1.0)


class HazardEvent(BaseModel):
    id: str
    hazard_type: HazardType
    title: str
    location: Coordinates
    severity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str
    recommended_action: str
    signals: list[DataSignal]


class DetectionRequest(BaseModel):
    region: str = "global"


class DetectionResponse(BaseModel):
    region: str
    resolved_location: ResolvedLocation
    hazards: list[HazardEvent]
