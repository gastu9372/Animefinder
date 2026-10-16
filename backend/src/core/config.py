from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Servidor ---
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    PORT: int = Field(default=8000, ge=1024, le=65535)
    DEBUG: bool = False
    TRUSTED_PROXIES: str = "127.0.0.1,172.16.0.0/12,10.0.0.0/8"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost"

    # --- Redis & Rate Limiting ---
    REDIS_URL: str = Field(..., description="URL de conexión a Redis obligatoria")
    RATE_LIMIT_PER_IP_PER_MIN: int = Field(default=10, gt=0)


    IMAGE_SEARCH_PER_IP_PER_DAY: int = Field(default=10, gt=0)

    # --- Procesamiento de Imágenes ---
    MAX_IMAGE_SIZE_BYTES: int = Field(default=8388608, gt=0)  # 8 MB
    IMAGE_PROCESSING_CONCURRENCY: int = Field(default=4, gt=0)

    # --- trace.moe ---
    TRACE_MOE_API_URL: str = "https://api.trace.moe"
    TRACE_MOE_API_KEY: str = ""
    TRACEMOE_MAX_CONCURRENCY: int = Field(default=1, gt=0)
    SIMILARITY_THRESHOLD_HIGH: float = Field(default=0.85, ge=0.0, le=1.0)
    SIMILARITY_THRESHOLD_LOW: float = Field(default=0.70, ge=0.0, le=1.0)
    ENABLE_VIDEO_PREVIEW: bool = True

    # --- AniList ---
    ANILIST_API_URL: str = "https://graphql.anilist.co"
    ANILIST_RATE_LIMIT_PER_MIN: int = Field(default=30, gt=0)
    ADULT_CONTENT_POLICY: Literal["filter", "blur", "allow"] = "filter"

    # --- Google Gemini ---
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    LLM_DAILY_CALL_CAP: int = Field(default=200, gt=0)
    TITLE_MATCH_MIN_SCORE: float = Field(default=0.70, ge=0.0, le=1.0)

    # --- Flags Experimentales ---
    ENABLE_VISION_FALLBACK: bool = False

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS debe contener al menos un origen válido")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def trusted_proxies_list(self) -> list[str]:
        return [proxy.strip() for proxy in self.TRUSTED_PROXIES.split(",") if proxy.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
