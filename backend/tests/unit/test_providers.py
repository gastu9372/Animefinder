import fakeredis.aioredis as fake_aioredis
import httpx
import pytest
import respx
from src.core.config import Settings
from src.core.exceptions import (
    ExternalServiceUnavailableError,
    InvalidImageError,
    QuotaDepletedError,
    RateLimitExceededError,
)
from src.providers.anilist import AniListProvider, sanitize_synopsis
from src.providers.trace_moe import TraceMoeProvider


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        REDIS_URL="redis://localhost:6379/0",
        TRACE_MOE_API_URL="https://api.trace.moe",
        ANILIST_API_URL="https://graphql.anilist.co",
        _env_file=None,
    )


def test_sanitize_synopsis_html_and_spoilers() -> None:
    raw = "Este anime trata de un viaje.<br><i>Muy emocionante.</i> ~!El protagonista muere al final!~ Fin."
    clean = sanitize_synopsis(raw)
    assert "<br>" not in clean
    assert "<i>" not in clean
    assert "El protagonista muere al final" not in clean
    assert "[Contenido con spoiler omitido]" in clean
    assert "Este anime trata de un viaje." in clean


@pytest.mark.asyncio
async def test_trace_moe_search_and_deduplication(test_settings: Settings) -> None:
    mock_response = {
        "frameCount": 5000,
        "error": "",
        "result": [
            {"anilist": 1, "similarity": 0.95, "episode": 2, "from": 120.0, "to": 125.0},
            {"anilist": 1, "similarity": 0.82, "episode": 2, "from": 118.0, "to": 122.0},  # Duplicado menor
            {"anilist": 2, "similarity": 0.77, "episode": 5, "from": 45.0, "to": 48.0},
        ],
    }

    async with httpx.AsyncClient() as client:
        with respx.mock(assert_all_called=True) as respx_mock:
            respx_mock.post("https://api.trace.moe/search").respond(200, json=mock_response)
            provider = TraceMoeProvider(settings=test_settings, http_client=client)
            results = await provider.search_by_image(b"fake_image_bytes")

            assert len(results) == 2
            assert results[0].anilist_id == 1
            assert results[0].similarity == 0.95
            assert results[1].anilist_id == 2
            assert results[1].similarity == 0.77


@pytest.mark.asyncio
async def test_trace_moe_quota_depleted_402(test_settings: Settings) -> None:
    async with httpx.AsyncClient() as client:
        with respx.mock(assert_all_called=True) as respx_mock:
            respx_mock.post("https://api.trace.moe/search").respond(
                402, json={"error": "Search quota depleted"}
            )
            provider = TraceMoeProvider(settings=test_settings, http_client=client)

            with pytest.raises(QuotaDepletedError):
                await provider.search_by_image(b"fake_bytes")


@pytest.mark.asyncio
async def test_trace_moe_invalid_image_400(test_settings: Settings) -> None:
    async with httpx.AsyncClient() as client:
        with respx.mock(assert_all_called=True) as respx_mock:
            respx_mock.post("https://api.trace.moe/search").respond(
                400, json={"error": "Failed to process image"}
            )
            provider = TraceMoeProvider(settings=test_settings, http_client=client)

            with pytest.raises(InvalidImageError):
                await provider.search_by_image(b"broken")


@pytest.mark.asyncio
async def test_anilist_batch_query_and_caching(test_settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.providers.anilist.get_redis_client", get_fake_redis)

    mock_graphql_resp = {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 1,
                        "title": {"romaji": "Cowboy Bebop", "english": "Cowboy Bebop", "native": "カウボーイビバップ"},
                        "coverImage": {"extraLarge": "https://img.anilist.co/1.jpg"},
                        "description": "Un cazarrecompensas espacial.<br>",
                        "seasonYear": 1998,
                        "format": "TV",
                        "isAdult": False,
                    }
                ]
            }
        }
    }

    async with httpx.AsyncClient() as client:
        with respx.mock() as respx_mock:
            route = respx_mock.post("https://graphql.anilist.co").respond(200, json=mock_graphql_resp)
            provider = AniListProvider(settings=test_settings, http_client=client)

            # Primera llamada: debe consultar la API de AniList
            batch_result = await provider.get_anime_batch([1])
            assert 1 in batch_result
            assert batch_result[1].title.romaji == "Cowboy Bebop"
            assert route.call_count == 1

            # Segunda llamada con el mismo ID: debe responder desde Redis sin volver a llamar a la API
            cached_result = await provider.get_anime_batch([1])
            assert 1 in cached_result
            assert cached_result[1].title.romaji == "Cowboy Bebop"
            assert route.call_count == 1  # No incrementó, se leyó de caché


@pytest.mark.asyncio
async def test_anilist_rate_limit_429(test_settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("src.providers.anilist.get_redis_client", lambda: fake_redis)

    async with httpx.AsyncClient() as client:
        with respx.mock(assert_all_called=True) as respx_mock:
            respx_mock.post("https://graphql.anilist.co").respond(
                429, headers={"Retry-After": "45"}
            )
            provider = AniListProvider(settings=test_settings, http_client=client)

            with pytest.raises(RateLimitExceededError) as exc_info:
                await provider.get_anime_batch([999])
            assert exc_info.value.retry_after_seconds == 45
