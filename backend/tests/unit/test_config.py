import os

import pytest
from pydantic import ValidationError
from src.core.config import Settings


def test_settings_fail_fast_missing_redis_url() -> None:
    """Verifica que el inicio de la app falle de inmediato si falta REDIS_URL."""
    # Guardar valor original si existía
    original_val = os.environ.get("REDIS_URL")
    if "REDIS_URL" in os.environ:
        del os.environ["REDIS_URL"]

    try:
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)  # Ignorar archivo .env para evaluar variables puras
        errors = exc_info.value.errors()
        assert any(err["loc"] == ("REDIS_URL",) for err in errors)
    finally:
        if original_val is not None:
            os.environ["REDIS_URL"] = original_val


def test_settings_cors_origins_parsing() -> None:
    """Verifica que CORS_ORIGINS se parsee correctamente a lista de cadenas."""
    settings = Settings(
        REDIS_URL="redis://localhost:6379/0",
        CORS_ORIGINS="http://localhost:5173, http://example.com ,https://app.animefinder.com",
        _env_file=None,
    )
    assert settings.cors_origins_list == [
        "http://localhost:5173",
        "http://example.com",
        "https://app.animefinder.com",
    ]


def test_settings_production_flag() -> None:
    """Verifica que el flag is_production responda al valor del entorno."""
    prod_settings = Settings(
        REDIS_URL="redis://localhost:6379/0",
        ENVIRONMENT="production",
        _env_file=None,
    )
    assert prod_settings.is_production is True

    dev_settings = Settings(
        REDIS_URL="redis://localhost:6379/0",
        ENVIRONMENT="development",
        _env_file=None,
    )
    assert dev_settings.is_production is False
