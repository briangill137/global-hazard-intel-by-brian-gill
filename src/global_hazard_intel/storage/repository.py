from global_hazard_intel.domain.models import HazardEvent


class HazardRepository:
    def __init__(self) -> None:
        self._events: list[HazardEvent] = []

    def save_all(self, events: list[HazardEvent]) -> list[HazardEvent]:
        self._events = events
        return self._events

    def list_all(self) -> list[HazardEvent]:
        return self._events
