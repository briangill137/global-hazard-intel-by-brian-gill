from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Global Hazard Intel"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    satellite_provider: str = "mock_nasa_esa"
    weather_provider: str = "mock_noaa"
    air_quality_provider: str = "mock_openaq"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
