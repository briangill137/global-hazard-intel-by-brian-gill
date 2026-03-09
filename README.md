# Global Hazard Intel

Global Hazard Intel is a live environmental hazard intelligence platform. It fuses public weather, air-quality, geocoding, satellite-imagery, and NASA event feeds to detect:

- dust storms
- wildfire smoke
- chemical leaks
- pollution spikes

The repository is structured like an investor-facing, company-ready starter project: clear architecture, clean code boundaries, API scaffolding, dashboard prototype, and deployment-ready metadata.

## Vision

Build a global AI monitoring system that ingests multi-source earth observation data and produces a real-time hazard intelligence layer for governments, insurers, logistics companies, and climate-tech platforms.

## Core Pipeline

```text
Satellite Imagery + Weather Data + Air Quality Sensors
                        |
                        v
               AI Hazard Detection Engine
                        |
                        v
             Global Hazard Dashboard + API
```

## Hazards Covered

- Dust storms
- Wildfire smoke
- Chemical leaks
- Pollution spikes

## Repository Layout

```text
.
|-- .github/workflows/ci.yml
|-- dashboard/
|-- docs/
|-- src/global_hazard_intel/
|   |-- api/
|   |-- connectors/
|   |-- domain/
|   |-- pipelines/
|   |-- services/
|   |-- storage/
|   `-- utils/
|-- tests/
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- Makefile
`-- pyproject.toml
```

## Quick Start

1. Create a virtual environment.
2. Install dependencies.
3. Run the desktop monitoring app or start the API.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
uvicorn global_hazard_intel.main:app --reload
```

API docs will be available at `http://127.0.0.1:8000/docs`.

To open the desktop monitoring app:

```bash
python main.py
```

The Tkinter window title is `GLOBAL HAZARD INTEL By Brian Gill` and supports:

- continent selection from a dropdown
- country, city, or address input
- direct coordinates
- lab-style monitoring console layout
- live refresh charts with Matplotlib
- satellite imagery panel
- weather analytics, health analytics, and scientific analytics tabs
- status cards for live state, active region, hazard count, and sync time
- report export to timestamped PDF and CSV folders

## Example Endpoints

- `GET /health`
- `GET /api/v1/hazards`
- `POST /api/v1/hazards/detect`

## Live Data Sources

- Open-Meteo Geocoding API
- Open-Meteo Weather Forecast API
- Open-Meteo Air Quality API
- NASA EONET events API
- OpenStreetMap Nominatim for address resolution
- Esri World Imagery export service for satellite basemap snapshots

## Desktop Analytics

The desktop application is designed for cross-functional review:

- Weather analytics for operations teams and weather stations
- Public-health analytics for air-quality and exposure monitoring
- Scientific analytics for earth observation and atmospheric research
- Forecast propagation windows for 6h, 24h, 48h, and 72h outlooks
- Explainable trigger notes and signal provenance
- Executive partner-value scoring and investment-readiness framing
- Multi-file report export with timestamped output folders

Generated report folders now contain:

- `hazard_report_<timestamp>.pdf`
- `hazard_report_<timestamp>.csv`
- `signal_report_<timestamp>.csv`
- `nasa_events_<timestamp>.csv`
- `history_report_<timestamp>.csv`
- `forecast_report_<timestamp>.csv`
- `summary_<timestamp>.json`

## Research Package

The repository includes an IEEE-style LaTeX paper scaffold in [research/paper.tex](c:/Users/Brian%20Gill/Desktop/Python%20Development/Global%20Hazard%20Intel/research/paper.tex) with author metadata for Brian Gill and `briang.gill@bgcode.tech`.

## Product Direction

- Real-time ingestion from NASA, ESA, Copernicus, NOAA, and public AQ networks
- Event fusion across imagery, meteorology, and sensor anomalies
- Geospatial alerting and severity scoring
- Regional forecasting and risk propagation models
- Enterprise integrations through API and webhook delivery

## Tech Stack

- FastAPI
- Pydantic
- Uvicorn
- Pytest
- Lightweight static dashboard prototype

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)

## Status

This is a polished starter scaffold, not a fully trained operational earth observation system yet. It is designed to help you present the concept professionally on GitHub and continue building quickly.
