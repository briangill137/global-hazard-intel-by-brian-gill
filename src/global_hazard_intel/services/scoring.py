from global_hazard_intel.domain.models import DataSignal, HazardType


class ScoringService:
    def score(self, hazard_type: HazardType, signals: list[DataSignal]) -> tuple[float, float]:
        if not signals:
            return 0.0, 0.0

        average_signal = sum(signal.value for signal in signals) / len(signals)
        average_confidence = sum(signal.confidence for signal in signals) / len(signals)

        type_weight = {
            HazardType.DUST_STORM: 0.92,
            HazardType.WILDFIRE_SMOKE: 0.95,
            HazardType.CHEMICAL_LEAK: 0.90,
            HazardType.POLLUTION_SPIKE: 0.88,
        }[hazard_type]

        severity = min(1.0, average_signal * type_weight)
        confidence = min(1.0, average_confidence)
        return severity, confidence
