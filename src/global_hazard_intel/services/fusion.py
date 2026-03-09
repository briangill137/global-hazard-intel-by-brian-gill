from collections import defaultdict

from global_hazard_intel.domain.models import DataSignal


class FusionService:
    def group_by_source(self, signals: list[DataSignal]) -> dict[str, list[DataSignal]]:
        grouped: dict[str, list[DataSignal]] = defaultdict(list)
        for signal in signals:
            grouped[signal.source].append(signal)
        return dict(grouped)
