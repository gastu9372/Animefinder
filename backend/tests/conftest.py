import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.core.config import Settings, get_settings
from src.main import create_app


@pytest.fixture(autouse=True)
def test_env() -> None:
    """Configura variables de entorno mínimas para la suite de pruebas."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://testserver"
    os.environ["DEBUG"] = "true"
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Cliente HTTP asíncrono configurado para invocar la app FastAPI."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
