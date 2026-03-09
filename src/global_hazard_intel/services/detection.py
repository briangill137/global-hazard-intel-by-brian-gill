from global_hazard_intel.domain.location import ResolvedLocation
from global_hazard_intel.domain.models import Coordinates, DataSignal, HazardEvent, HazardType


class DetectionService:
    def detect(self, region: str, location: ResolvedLocation, signals: list[DataSignal]) -> list[HazardEvent]:
        signal_map = {signal.metric: signal for signal in signals}
        hazards: list[HazardEvent] = []

        location_point = Coordinates(latitude=location.latitude, longitude=location.longitude)

        dust_score = min(
            1.0,
            signal_map.get("dust", self._empty_signal()).value * 0.65
            + signal_map.get("wind_speed_10m", self._empty_signal()).value * 0.35,
        )
        if dust_score >= 0.25:
            hazards.append(
                self._build_event(
                    region=region,
                    hazard_type=HazardType.DUST_STORM,
                    title="Dust Transport Risk",
                    summary="Live dust concentration and wind fields suggest airborne dust transport risk.",
                    action="Monitor airports, logistics corridors, and respiratory advisories.",
                    severity=dust_score,
                    confidence=self._average_confidence(signals, ["dust", "wind_speed_10m"]),
                    location=location_point,
                    signals=self._select_signals(signals, {"dust", "wind_speed_10m", "wind_gusts_10m"}),
                )
            )

        wildfire_score = min(
            1.0,
            signal_map.get("wildfire_event_count", self._empty_signal()).value * 0.55
            + signal_map.get("pm2_5", self._empty_signal()).value * 0.45,
        )
        if wildfire_score >= 0.20:
            hazards.append(
                self._build_event(
                    region=region,
                    hazard_type=HazardType.WILDFIRE_SMOKE,
                    title="Wildfire Smoke Risk",
                    summary="NASA event activity and particulate loading indicate potential wildfire smoke impact.",
                    action="Issue public-health guidance and review plume trajectory.",
                    severity=wildfire_score,
                    confidence=self._average_confidence(signals, ["wildfire_event_count", "pm2_5"]),
                    location=location_point,
                    signals=self._select_signals(signals, {"wildfire_event_count", "pm2_5", "pm10"}),
                )
            )

        chemical_score = min(
            1.0,
            signal_map.get("sulphur_dioxide", self._empty_signal()).value * 0.45
            + signal_map.get("carbon_monoxide", self._empty_signal()).value * 0.25
            + signal_map.get("nitrogen_dioxide", self._empty_signal()).value * 0.30,
        )
        if chemical_score >= 0.20:
            hazards.append(
                self._build_event(
                    region=region,
                    hazard_type=HazardType.CHEMICAL_LEAK,
                    title="Chemical Emissions Anomaly",
                    summary="Gas concentration anomalies suggest industrial emissions or a possible chemical release.",
                    action="Escalate for local environmental investigation and source attribution.",
                    severity=chemical_score,
                    confidence=self._average_confidence(
                        signals, ["sulphur_dioxide", "carbon_monoxide", "nitrogen_dioxide"]
                    ),
                    location=location_point,
                    signals=self._select_signals(
                        signals, {"sulphur_dioxide", "carbon_monoxide", "nitrogen_dioxide"}
                    ),
                )
            )

        pollution_score = min(
            1.0,
            signal_map.get("us_aqi", self._empty_signal()).value * 0.45
            + signal_map.get("pm2_5", self._empty_signal()).value * 0.30
            + signal_map.get("pm10", self._empty_signal()).value * 0.25,
        )
        if pollution_score >= 0.18:
            hazards.append(
                self._build_event(
                    region=region,
                    hazard_type=HazardType.POLLUTION_SPIKE,
                    title="Air Pollution Spike",
                    summary="Live AQI and particulate signals show degraded air quality conditions.",
                    action="Issue exposure guidance and investigate likely pollution sources.",
                    severity=pollution_score,
                    confidence=self._average_confidence(signals, ["us_aqi", "pm2_5", "pm10"]),
                    location=location_point,
                    signals=self._select_signals(signals, {"us_aqi", "pm2_5", "pm10"}),
                )
            )

        return hazards

    @staticmethod
    def _build_event(
        region: str,
        hazard_type: HazardType,
        title: str,
        summary: str,
        action: str,
        severity: float,
        confidence: float,
        location: Coordinates,
        signals: list[DataSignal],
    ) -> HazardEvent:
        return HazardEvent(
            id=f"{region.lower().replace(' ', '-')}-{hazard_type.value}",
            hazard_type=hazard_type,
            title=title,
            location=location,
            severity=severity,
            confidence=confidence,
            summary=summary,
            recommended_action=action,
            signals=signals,
        )

    @staticmethod
    def _average_confidence(signals: list[DataSignal], metrics: list[str]) -> float:
        matching = [signal.confidence for signal in signals if signal.metric in metrics]
        if not matching:
            return 0.0
        return sum(matching) / len(matching)

    @staticmethod
    def _select_signals(signals: list[DataSignal], metrics: set[str]) -> list[DataSignal]:
        return [signal for signal in signals if signal.metric in metrics]

    @staticmethod
    def _empty_signal() -> DataSignal:
        return DataSignal(source="none", metric="none", value=0.0, confidence=0.0)
