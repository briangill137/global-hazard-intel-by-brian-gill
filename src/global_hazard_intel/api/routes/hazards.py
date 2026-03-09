from fastapi import APIRouter

from global_hazard_intel.domain.models import DetectionRequest, DetectionResponse, HazardEvent
from global_hazard_intel.pipelines.orchestrator import HazardOrchestrator

router = APIRouter(prefix="/api/v1/hazards", tags=["hazards"])
orchestrator = HazardOrchestrator()


@router.get("", response_model=list[HazardEvent])
def list_hazards() -> list[HazardEvent]:
    existing = orchestrator.list_hazards()
    if existing:
        return existing
    return orchestrator.run_detection("global").hazards


@router.post("/detect", response_model=DetectionResponse)
def detect_hazards(request: DetectionRequest) -> DetectionResponse:
    return orchestrator.run_detection(request.region)
