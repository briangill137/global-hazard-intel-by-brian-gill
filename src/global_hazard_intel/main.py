from fastapi import FastAPI

from global_hazard_intel.api.routes.hazards import router as hazards_router
from global_hazard_intel.api.routes.health import router as health_router
from global_hazard_intel.config import settings
from global_hazard_intel.utils.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Environmental hazard intelligence API for multi-source global monitoring.",
)

app.include_router(health_router)
app.include_router(hazards_router)


if __name__ == "__main__":
    from global_hazard_intel.desktop_app import launch_app

    launch_app()
