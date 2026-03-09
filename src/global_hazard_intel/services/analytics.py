from __future__ import annotations

from dataclasses import dataclass

from global_hazard_intel.domain.models import DataSignal, HazardEvent


@dataclass(slots=True)
class ExposureBand:
    name: str
    share: float
    guidance: str


@dataclass(slots=True)
class HealthAnalytics:
    exposure_score: float
    advisory_level: str
    vulnerable_groups: list[str]
    estimated_population_exposure_millions: float
    exposure_bands: list[ExposureBand]
    advisory_text: str


@dataclass(slots=True)
class ForecastPoint:
    horizon_hours: int
    hazard_spread_score: float
    air_quality_risk: float
    confidence: float


@dataclass(slots=True)
class WeatherAnalytics:
    operations_score: float
    plume_transport_risk: float
    station_readiness: str
    forecast: list[ForecastPoint]
    weather_brief: str


@dataclass(slots=True)
class ScientificAnalytics:
    observation_utility_score: float
    data_provenance: list[str]
    trigger_explanations: list[str]
    confidence_notes: list[str]
    research_summary: str


@dataclass(slots=True)
class ExecutiveAnalytics:
    enterprise_priority_score: float
    investment_readiness: str
    decision_summary: list[str]
    unique_value_points: list[str]


@dataclass(slots=True)
class AnalyticsBundle:
    health: HealthAnalytics
    weather: WeatherAnalytics
    scientific: ScientificAnalytics
    executive: ExecutiveAnalytics


class AnalyticsService:
    def build(
        self,
        hazards: list[HazardEvent],
        signals: list[DataSignal],
        weather: dict[str, float | None],
        air_quality: dict[str, float | None],
        nasa_events: list[dict],
    ) -> AnalyticsBundle:
        return AnalyticsBundle(
            health=self._build_health(hazards, air_quality),
            weather=self._build_weather(hazards, weather, air_quality),
            scientific=self._build_scientific(hazards, signals, nasa_events),
            executive=self._build_executive(hazards, weather, air_quality, nasa_events),
        )

    def _build_health(
        self,
        hazards: list[HazardEvent],
        air_quality: dict[str, float | None],
    ) -> HealthAnalytics:
        aqi = float(air_quality.get("us_aqi") or 0.0)
        pm25 = float(air_quality.get("pm2_5") or 0.0)
        ozone = float(air_quality.get("ozone") or 0.0)
        exposure_score = min(1.0, 0.45 * (aqi / 300.0) + 0.35 * (pm25 / 150.0) + 0.20 * (ozone / 180.0))
        advisory_level = (
            "Severe" if exposure_score >= 0.75 else "High" if exposure_score >= 0.55 else "Elevated" if exposure_score >= 0.30 else "Moderate"
        )
        estimated_population = round(2.5 + exposure_score * 18.0 + len(hazards) * 1.4, 1)
        exposure_bands = [
            ExposureBand("Minimal", max(0.0, 1.0 - exposure_score * 1.6), "Routine monitoring"),
            ExposureBand("Sensitive Groups", min(1.0, exposure_score * 0.9), "Issue targeted advisories"),
            ExposureBand("General Population", min(1.0, max(0.0, exposure_score - 0.25)), "Consider broad public messaging"),
        ]
        vulnerable_groups = ["Children", "Older adults", "Asthma and COPD patients", "Outdoor workers"]
        advisory_text = (
            f"{advisory_level} exposure conditions. Prioritize respiratory messaging, school guidance, and mask/indoor-air recommendations."
        )
        return HealthAnalytics(
            exposure_score=exposure_score,
            advisory_level=advisory_level,
            vulnerable_groups=vulnerable_groups,
            estimated_population_exposure_millions=estimated_population,
            exposure_bands=exposure_bands,
            advisory_text=advisory_text,
        )

    def _build_weather(
        self,
        hazards: list[HazardEvent],
        weather: dict[str, float | None],
        air_quality: dict[str, float | None],
    ) -> WeatherAnalytics:
        wind = float(weather.get("wind_speed_10m") or 0.0)
        gust = float(weather.get("wind_gusts_10m") or 0.0)
        cloud = float(weather.get("cloud_cover") or 0.0)
        dust = float(air_quality.get("dust") or 0.0)
        plume_transport = min(1.0, 0.4 * (wind / 80.0) + 0.35 * (gust / 100.0) + 0.25 * (dust / 300.0))
        operations_score = min(1.0, 0.5 * plume_transport + 0.2 * (cloud / 100.0) + 0.3 * min(1.0, len(hazards) / 4.0))
        station_readiness = (
            "Escalated monitoring" if operations_score >= 0.7 else "Enhanced watch" if operations_score >= 0.45 else "Routine watch"
        )
        forecast = self._forecast_points(plume_transport, float(air_quality.get("us_aqi") or 0.0) / 300.0)
        weather_brief = (
            "Transport conditions support regional hazard spread. Review plume direction, station calibration, and next-shift readiness."
        )
        return WeatherAnalytics(
            operations_score=operations_score,
            plume_transport_risk=plume_transport,
            station_readiness=station_readiness,
            forecast=forecast,
            weather_brief=weather_brief,
        )

    def _build_scientific(
        self,
        hazards: list[HazardEvent],
        signals: list[DataSignal],
        nasa_events: list[dict],
    ) -> ScientificAnalytics:
        hazard_conf = sum(h.confidence for h in hazards) / len(hazards) if hazards else 0.0
        provenance = [
            "Open-Meteo Geocoding",
            "Open-Meteo Weather",
            "Open-Meteo Air Quality",
            "NASA EONET",
            "Esri World Imagery",
        ]
        top_signals = sorted(signals, key=lambda item: item.value * item.confidence, reverse=True)[:5]
        trigger_explanations = [
            f"{signal.metric} from {signal.source} contributed {signal.value:.2f} signal with {signal.confidence:.2f} confidence."
            for signal in top_signals
        ]
        confidence_notes = [
            f"{len(nasa_events)} NASA event(s) in the region increased scientific context strength.",
            f"Mean hazard confidence is {hazard_conf:.2f}.",
        ]
        observation_score = min(1.0, 0.55 * min(1.0, len(nasa_events) / 10.0) + 0.45 * hazard_conf)
        summary = "Designed for earth-observation review, cross-sensor interpretation, and research traceability."
        return ScientificAnalytics(
            observation_utility_score=observation_score,
            data_provenance=provenance,
            trigger_explanations=trigger_explanations,
            confidence_notes=confidence_notes,
            research_summary=summary,
        )

    def _build_executive(
        self,
        hazards: list[HazardEvent],
        weather: dict[str, float | None],
        air_quality: dict[str, float | None],
        nasa_events: list[dict],
    ) -> ExecutiveAnalytics:
        severity = max((hazard.severity for hazard in hazards), default=0.0)
        aqi = float(air_quality.get("us_aqi") or 0.0) / 300.0
        wind = float(weather.get("wind_speed_10m") or 0.0) / 80.0
        science = min(1.0, len(nasa_events) / 8.0)
        score = min(1.0, 0.35 * severity + 0.25 * aqi + 0.20 * wind + 0.20 * science)
        readiness = "Strong showcase candidate" if score >= 0.65 else "High-potential prototype" if score >= 0.40 else "Emerging concept"
        summary = [
            "Multi-stakeholder value across health, meteorology, and EO teams.",
            "Live public-data fusion supports rapid pilots and agency demonstrations.",
            "Report outputs are suitable for briefing packs and stakeholder handoff.",
        ]
        unique_points = [
            "One interface for health advisories, weather operations, and scientific interpretation.",
            "Timestamped PDF/CSV reporting with live satellite context.",
            "Explainable signal trace for each detection run.",
            "Built to evolve toward population exposure and forecast propagation workflows.",
        ]
        return ExecutiveAnalytics(
            enterprise_priority_score=score,
            investment_readiness=readiness,
            decision_summary=summary,
            unique_value_points=unique_points,
        )

    @staticmethod
    def _forecast_points(plume_transport: float, air_quality_risk: float) -> list[ForecastPoint]:
        points: list[ForecastPoint] = []
        for hours, multiplier in [(6, 0.95), (24, 1.0), (48, 0.92), (72, 0.85)]:
            spread = min(1.0, plume_transport * multiplier + (0.08 if hours >= 24 else 0.0))
            aq = min(1.0, air_quality_risk * multiplier + (0.05 if hours >= 48 else 0.0))
            confidence = max(0.35, 0.92 - (hours / 120.0))
            points.append(
                ForecastPoint(
                    horizon_hours=hours,
                    hazard_spread_score=spread,
                    air_quality_risk=aq,
                    confidence=confidence,
                )
            )
        return points
