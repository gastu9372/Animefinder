import io
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis as fake_aioredis
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from PIL import Image
import pytest
from src.api.v1.endpoints.search_image import extract_client_ip
from src.core.config import get_settings
from src.domain.models import CanonicalAnime, RawImageMatch, TitleInfo
from src.main import create_app
from src.services.image_search_service import format_timestamp


def create_test_image_bytes() -> bytes:
    """Genera una imagen JPEG válida mínima en memoria."""
    img = Image.new("RGB", (200, 200), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_format_timestamp() -> None:
    assert format_timestamp(0.0) == "00:00"
    assert format_timestamp(65.0) == "01:05"
    assert format_timestamp(845.5) == "14:05"
    assert format_timestamp(None) is None


def test_extract_client_ip_security() -> None:
    # 1. Socket directo NO confiable intenta inyectar X-Forwarded-For falso
    untrusted_scope = {
        "type": "http",
        "client": ("203.0.113.195", 54321),
        "headers": [(b"x-forwarded-for", b"1.1.1.1")],
    }
    req_untrusted = Request(untrusted_scope)
    assert extract_client_ip(req_untrusted) == "203.0.113.195"  # Ignora el header falsificado

    # 2. Socket directo proviene de localhost/proxy confiable
    trusted_scope = {
        "type": "http",
        "client": ("127.0.0.1", 54321),
        "headers": [(b"x-forwarded-for", b"203.0.113.50, 10.0.0.1")],
    }
    req_trusted = Request(trusted_scope)
    assert extract_client_ip(req_trusted) == "203.0.113.50"  # Acepta la IP real


@pytest.mark.asyncio
async def test_search_image_success_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.services.image_search_service.get_redis_client", get_fake_redis)

    app = create_app()

    # Mock de proveedores
    mock_raw_matches = [
        RawImageMatch(
            anilist_id=100,
            similarity=0.92,
            episode=3,
            from_seconds=300.0,
            to_seconds=305.0,
            video_url="https://media.trace.moe/video/100/...",
        )
    ]
    mock_anime_meta = {
        100: CanonicalAnime(
            id=100,
            title=TitleInfo(romaji="Steins;Gate", english="Steins;Gate", native="シュタインズ・ゲート"),
            cover_image="https://img.anilist.co/sg.jpg",
            synopsis="Científicos locos y viajes en el tiempo.",
            year=2011,
            format="TV",
            is_adult=False,
        )
    }

    with patch("src.api.v1.endpoints.search_image.get_image_service") as mock_get_svc:
        mock_svc = AsyncMock()
        mock_svc.search_by_image.return_value = {
            "query_type": "image",
            "search_mode": "trace.moe",
            "cached": False,
            "filtered_count": 0,
            "processing_time_ms": 120,
            "results": [
                {
                    "id": 100,
                    "title": mock_anime_meta[100].title.model_dump(),
                    "cover_image": mock_anime_meta[100].cover_image,
                    "synopsis": mock_anime_meta[100].synopsis,
                    "year": 2011,
                    "format": "TV",
                    "is_adult": False,
                    "confidence_percentage": 92.0,
                    "confidence_level": "high",
                    "match_reason": None,
                    "scene_info": {
                        "episode": 3,
                        "timestamp_seconds": 300.0,
                        "timestamp_formatted": "05:00",
                        "preview_video_url": "https://media.trace.moe/video/100/...",
                    },
                }
            ],
        }
        mock_get_svc.return_value = mock_svc

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            img_bytes = create_test_image_bytes()
            files = {"file": ("scene.jpg", img_bytes, "image/jpeg")}
            response = await client.post("/api/v1/search/image", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["query_type"] == "image"
            assert len(data["results"]) == 1
            assert data["results"][0]["id"] == 100
            assert data["results"][0]["confidence_percentage"] == 92.0
            assert data["results"][0]["scene_info"]["timestamp_formatted"] == "05:00"


@pytest.mark.asyncio
async def test_search_image_reject_fake_binary() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Archivo con extensión .jpg pero contenido ejecutable falso
        fake_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00"
        files = {"file": ("malicious.jpg", fake_bytes, "image/jpeg")}
        response = await client.post("/api/v1/search/image", files=files)

        assert response.status_code == 415
        problem = response.json()
        assert problem["code"] == "UNSUPPORTED_MEDIA_TYPE"


@pytest.mark.asyncio
async def test_search_image_reject_too_large() -> None:
    app = create_app()
    settings = get_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Generar buffer que excede el límite configurado
        large_bytes = b"\xff\xd8\xff" + b"0" * (settings.MAX_IMAGE_SIZE_BYTES + 10)
        files = {"file": ("huge.jpg", large_bytes, "image/jpeg")}
        response = await client.post("/api/v1/search/image", files=files)

        assert response.status_code == 400
        problem = response.json()
        assert problem["code"] == "INVALID_IMAGE"


@pytest.mark.asyncio
async def test_rate_limit_isolation_by_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.services.image_search_service.get_redis_client", get_fake_redis)

    from src.services.image_search_service import ImageSearchService

    svc = ImageSearchService()

    ip_a = "192.168.1.10"
    ip_b = "192.168.1.20"

    # Consumir 10 peticiones para IP A
    for _ in range(10):
        await svc.check_rate_limits(ip_a)

    # La petición 11 de IP A debe fallar por rate limit
    with pytest.raises(Exception) as exc_info:
        await svc.check_rate_limits(ip_a)
    assert "límite" in str(exc_info.value).lower()

    # IP B debe poder realizar consultas sin verse afectada por el bucket de IP A
    await svc.check_rate_limits(ip_b)  # No levanta excepción
