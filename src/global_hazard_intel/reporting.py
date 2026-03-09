from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from global_hazard_intel.domain.monitoring import MonitoringSnapshot


class ReportExporter:
    def __init__(self, base_dir: str = "reports") -> None:
        self.base_dir = Path(base_dir)

    def export(self, snapshot: MonitoringSnapshot, figure: Figure) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_name = self._slugify(snapshot.location.display_name)
        report_dir = self.base_dir / f"{timestamp}_{safe_name}"
        report_dir.mkdir(parents=True, exist_ok=True)

        files = {
            "hazard_csv": report_dir / f"hazard_report_{timestamp}.csv",
            "signal_csv": report_dir / f"signal_report_{timestamp}.csv",
            "nasa_csv": report_dir / f"nasa_events_{timestamp}.csv",
            "history_csv": report_dir / f"history_report_{timestamp}.csv",
            "forecast_csv": report_dir / f"forecast_report_{timestamp}.csv",
            "summary_json": report_dir / f"summary_{timestamp}.json",
            "pdf": report_dir / f"hazard_report_{timestamp}.pdf",
        }

        self._write_hazard_csv(files["hazard_csv"], snapshot)
        self._write_signals_csv(files["signal_csv"], snapshot)
        self._write_nasa_csv(files["nasa_csv"], snapshot)
        self._write_history_csv(files["history_csv"], snapshot)
        self._write_forecast_csv(files["forecast_csv"], snapshot)
        self._write_summary_json(files["summary_json"], snapshot)
        self._write_pdf(files["pdf"], snapshot, figure)
        return report_dir

    def _write_hazard_csv(self, path: Path, snapshot: MonitoringSnapshot) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "query",
                    "resolved_location",
                    "latitude",
                    "longitude",
                    "hazard_type",
                    "title",
                    "severity",
                    "confidence",
                    "recommended_action",
                ]
            )
            for hazard in snapshot.hazards:
                writer.writerow(
                    [
                        snapshot.query,
                        snapshot.location.display_name,
                        snapshot.location.latitude,
                        snapshot.location.longitude,
                        hazard.hazard_type.value,
                        hazard.title,
                        f"{hazard.severity:.3f}",
                        f"{hazard.confidence:.3f}",
                        hazard.recommended_action,
                    ]
                )

    def _write_signals_csv(self, path: Path, snapshot: MonitoringSnapshot) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["signal_metric", "signal_value", "signal_confidence", "source"])
            for signal in snapshot.signals:
                writer.writerow([signal.metric, f"{signal.value:.3f}", f"{signal.confidence:.3f}", signal.source])

    def _write_nasa_csv(self, path: Path, snapshot: MonitoringSnapshot) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["title", "categories", "closed", "geometry_count"])
            for event in snapshot.nasa_events:
                categories = ", ".join(category.get("title", "") for category in event.get("categories", []))
                writer.writerow(
                    [event.get("title", ""), categories, event.get("closed", ""), len(event.get("geometry", []))]
                )

    def _write_history_csv(self, path: Path, snapshot: MonitoringSnapshot) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "captured_at",
                    "location_name",
                    "top_hazard",
                    "top_severity",
                    "health_exposure_score",
                    "weather_operations_score",
                    "observation_utility_score",
                ]
            )
            for record in snapshot.history:
                writer.writerow(
                    [
                        record.captured_at,
                        record.location_name,
                        record.top_hazard,
                        f"{record.top_severity:.3f}",
                        f"{record.health_exposure_score:.3f}",
                        f"{record.weather_operations_score:.3f}",
                        f"{record.observation_utility_score:.3f}",
                    ]
                )

    def _write_forecast_csv(self, path: Path, snapshot: MonitoringSnapshot) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["horizon_hours", "hazard_spread_score", "air_quality_risk", "confidence"])
            for point in snapshot.analytics.weather.forecast:
                writer.writerow(
                    [
                        point.horizon_hours,
                        f"{point.hazard_spread_score:.3f}",
                        f"{point.air_quality_risk:.3f}",
                        f"{point.confidence:.3f}",
                    ]
                )

    def _write_summary_json(self, path: Path, snapshot: MonitoringSnapshot) -> None:
        payload = {
            "query": snapshot.query,
            "location": snapshot.location.display_name,
            "coordinates": [snapshot.location.latitude, snapshot.location.longitude],
            "hazards": [
                {
                    "type": hazard.hazard_type.value,
                    "title": hazard.title,
                    "severity": hazard.severity,
                    "confidence": hazard.confidence,
                }
                for hazard in snapshot.hazards
            ],
            "analytics": {
                "health": {
                    "exposure_score": snapshot.analytics.health.exposure_score,
                    "advisory_level": snapshot.analytics.health.advisory_level,
                    "estimated_population_exposure_millions": snapshot.analytics.health.estimated_population_exposure_millions,
                },
                "weather": {
                    "operations_score": snapshot.analytics.weather.operations_score,
                    "plume_transport_risk": snapshot.analytics.weather.plume_transport_risk,
                    "station_readiness": snapshot.analytics.weather.station_readiness,
                },
                "scientific": {
                    "observation_utility_score": snapshot.analytics.scientific.observation_utility_score,
                    "data_provenance": snapshot.analytics.scientific.data_provenance,
                },
                "executive": {
                    "enterprise_priority_score": snapshot.analytics.executive.enterprise_priority_score,
                    "investment_readiness": snapshot.analytics.executive.investment_readiness,
                },
            },
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_pdf(self, path: Path, snapshot: MonitoringSnapshot, figure: Figure) -> None:
        with PdfPages(path) as pdf:
            pdf.savefig(figure)
            pdf.savefig(self._build_cover_page(snapshot))
            pdf.savefig(self._build_sector_page(snapshot))
            pdf.savefig(self._build_forecast_page(snapshot))
            pdf.savefig(self._build_science_page(snapshot))
            pdf.savefig(self._build_history_page(snapshot))

    def _build_cover_page(self, snapshot: MonitoringSnapshot) -> Figure:
        figure = Figure(figsize=(11.69, 8.27))
        axis = figure.add_subplot(111)
        axis.axis("off")
        hazard_lines = [
            f"- {hazard.title} | {hazard.hazard_type.value} | severity {hazard.severity:.2f} | confidence {hazard.confidence:.2f}"
            for hazard in snapshot.hazards
        ] or ["- No strong hazards detected in this snapshot"]
        text = "\n".join(
            [
                "GLOBAL HAZARD INTEL By Brian Gill",
                "Integrated Stakeholder Hazard Report",
                "",
                f"Query: {snapshot.query}",
                f"Resolved location: {snapshot.location.display_name}",
                f"Coordinates: {snapshot.location.latitude}, {snapshot.location.longitude}",
                f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
                "",
                f"Enterprise Priority Score: {snapshot.analytics.executive.enterprise_priority_score:.2f}",
                f"Investment Readiness: {snapshot.analytics.executive.investment_readiness}",
                "",
                "Hazard Summary:",
                *hazard_lines,
                "",
                "Executive Summary:",
                *[f"- {line}" for line in snapshot.analytics.executive.decision_summary],
            ]
        )
        axis.text(0.03, 0.97, text, va="top", ha="left", fontsize=12, family="monospace")
        return figure

    def _build_sector_page(self, snapshot: MonitoringSnapshot) -> Figure:
        figure = Figure(figsize=(11.69, 8.27))
        axis = figure.add_subplot(111)
        axis.axis("off")
        health = snapshot.analytics.health
        weather = snapshot.analytics.weather
        text = "\n".join(
            [
                "Stakeholder Analytics",
                "",
                f"Public Health Exposure Score: {health.exposure_score:.2f}",
                f"Advisory Level: {health.advisory_level}",
                f"Estimated Population Exposure: {health.estimated_population_exposure_millions:.1f} million",
                f"Health Advisory: {health.advisory_text}",
                "",
                f"Weather Operations Score: {weather.operations_score:.2f}",
                f"Plume Transport Risk: {weather.plume_transport_risk:.2f}",
                f"Station Readiness: {weather.station_readiness}",
                f"Weather Brief: {weather.weather_brief}",
                "",
                "Unique Value:",
                *[f"- {line}" for line in snapshot.analytics.executive.unique_value_points],
            ]
        )
        axis.text(0.03, 0.97, text, va="top", ha="left", fontsize=11, family="monospace")
        return figure

    def _build_forecast_page(self, snapshot: MonitoringSnapshot) -> Figure:
        figure = Figure(figsize=(11.69, 8.27))
        axis = figure.add_subplot(111)
        axis.axis("off")
        lines = [
            f"- {point.horizon_hours}h | spread={point.hazard_spread_score:.2f} | aq-risk={point.air_quality_risk:.2f} | confidence={point.confidence:.2f}"
            for point in snapshot.analytics.weather.forecast
        ]
        axis.text(
            0.03,
            0.97,
            "\n".join(
                [
                    "Forecast and Propagation Outlook",
                    "",
                    "Projected hazard windows:",
                    *lines,
                    "",
                    "Recommended operational use:",
                    "- Use 6h and 24h windows for alerting.",
                    "- Use 48h and 72h windows for staffing, briefing, and logistics planning.",
                ]
            ),
            va="top",
            ha="left",
            fontsize=11,
            family="monospace",
        )
        return figure

    def _build_science_page(self, snapshot: MonitoringSnapshot) -> Figure:
        figure = Figure(figsize=(11.69, 8.27))
        axis = figure.add_subplot(111)
        axis.axis("off")
        science = snapshot.analytics.scientific
        text = "\n".join(
            [
                "Scientific and Explainability Notes",
                "",
                f"Observation Utility Score: {science.observation_utility_score:.2f}",
                "",
                "Provenance:",
                *[f"- {item}" for item in science.data_provenance],
                "",
                "Trigger Explanations:",
                *[f"- {item}" for item in science.trigger_explanations],
                "",
                "Confidence Notes:",
                *[f"- {item}" for item in science.confidence_notes],
            ]
        )
        axis.text(0.03, 0.97, text, va="top", ha="left", fontsize=11, family="monospace")
        return figure

    def _build_history_page(self, snapshot: MonitoringSnapshot) -> Figure:
        figure = Figure(figsize=(11.69, 8.27))
        axis = figure.add_subplot(111)
        axis.axis("off")
        lines = [
            f"- {record.captured_at} | {record.location_name} | {record.top_hazard} | sev={record.top_severity:.2f} | health={record.health_exposure_score:.2f} | wx={record.weather_operations_score:.2f}"
            for record in snapshot.history[-12:]
        ] or ["- No prior history"]
        axis.text(
            0.03,
            0.97,
            "\n".join(["Operational History", "", *lines]),
            va="top",
            ha="left",
            fontsize=10,
            family="monospace",
        )
        return figure

    @staticmethod
    def _slugify(value: str) -> str:
        allowed = "".join(char if char.isalnum() else "_" for char in value.lower())
        return "_".join(part for part in allowed.split("_") if part)[:80] or "location"
