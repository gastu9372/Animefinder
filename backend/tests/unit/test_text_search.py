import json
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis.aioredis as fake_aioredis
from httpx import ASGITransport, AsyncClient
import pytest
from src.core.config import Settings
from src.core.exceptions import RateLimitExceededError
from src.domain.models import CanonicalAnime, TitleInfo
from src.main import create_app
from src.providers.gemini_ai import (
    GeminiLLMProvider,
    LLMCandidate,
    LLMDailyCapReachedError,
    LLMNotConfiguredError,
)
from src.services.text_search_service import TextSearchService, compute_title_similarity


def test_compute_title_similarity() -> None:
    anime = CanonicalAnime(
        id=1535,
        title=TitleInfo(romaji="Death Note", english="Death Note", native="デスノート"),
        cover_image="https://example.com/dn.jpg",
        synopsis="A high school student discovers a supernatural notebook.",
        year=2006,
        format="TV",
        is_adult=False,
    )
    # Exact romaji match
    assert compute_title_similarity("Death Note", anime) == 1.0

    # Case-insensitive
    assert compute_title_similarity("death note", anime) == 1.0

    # Minor variation
    score = compute_title_similarity("Deathnote", anime)
    assert score > 0.85

    # Completely different anime
    score_diff = compute_title_similarity("Sailor Moon", anime)
    assert score_diff < 0.40


@pytest.mark.asyncio
async def test_gemini_provider_unconfigured() -> None:
    settings = Settings(GEMINI_API_KEY="", REDIS_URL="redis://localhost:6379/1")
    provider = GeminiLLMProvider(settings=settings)
    with pytest.raises(LLMNotConfiguredError):
        await provider.infer_animes_from_description("Un chico con un cuaderno de la muerte")


@pytest.mark.asyncio
async def test_gemini_provider_daily_cap_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)
    await fake_redis.set("quota:gemini:daily", "200")

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.providers.gemini_ai.get_redis_client", get_fake_redis)

    settings = Settings(GEMINI_API_KEY="dummy-key", LLM_DAILY_CALL_CAP=200, REDIS_URL="redis://localhost:6379/1")
    provider = GeminiLLMProvider(settings=settings)
    with pytest.raises(LLMDailyCapReachedError):
        await provider.infer_animes_from_description("Un chico con un cuaderno")



@pytest.mark.asyncio
async def test_text_search_llm_success_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.services.text_search_service.get_redis_client", get_fake_redis)

    mock_llm = MagicMock(spec=GeminiLLMProvider)
    mock_llm.infer_animes_from_description = AsyncMock(return_value=[
        LLMCandidate(
            anime_title="Death Note",
            confidence_level="high",
            match_reason="<b>Cuaderno negro</b> que mata personas.",
        )
    ])

    mock_anilist = MagicMock()
    mock_anilist.search_anime_by_title = AsyncMock(return_value=[
        CanonicalAnime(
            id=1535,
            title=TitleInfo(romaji="Death Note", english="Death Note", native="デスノート"),
            cover_image="https://example.com/dn.jpg",
            synopsis="Light Yagami finds a notebook.",
            year=2006,
            format="TV",
            is_adult=False,
        )
    ])

    service = TextSearchService(llm_provider=mock_llm, anilist_provider=mock_anilist)
    result = await service.search_by_description(
        raw_description="Un estudiante de secundaria encuentra un cuaderno y mata criminales",
        client_ip="192.168.1.10",
        limit=5,
    )

    assert result["query_type"] == "text"
    assert result["search_mode"] == "llm"
    assert result["cached"] is False
    assert len(result["results"]) == 1
    item = result["results"][0]
    assert item["id"] == 1535
    assert item["confidence_level"] == "high"
    # HTML tag <b> must be stripped by nh3
    assert item["match_reason"] == "Cuaderno negro que mata personas."


@pytest.mark.asyncio
async def test_text_search_anti_hallucination_discard(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.services.text_search_service.get_redis_client", get_fake_redis)

    mock_llm = MagicMock(spec=GeminiLLMProvider)
    # LLM hallucinated an anime title that doesn't match AniList's result
    mock_llm.infer_animes_from_description = AsyncMock(return_value=[
        LLMCandidate(
            anime_title="Completely Invented Title 999",
            confidence_level="low",
            match_reason="Invented reason",
        )
    ])

    mock_anilist = MagicMock()
    mock_anilist.search_anime_by_title = AsyncMock(return_value=[
        CanonicalAnime(
            id=1,
            title=TitleInfo(romaji="Cowboy Bebop", english="Cowboy Bebop", native="カウボーイビバップ"),
            cover_image="https://example.com/cb.jpg",
            synopsis="Space bounty hunters.",
            year=1998,
            format="TV",
            is_adult=False,
        )
    ])

    service = TextSearchService(llm_provider=mock_llm, anilist_provider=mock_anilist)
    result = await service.search_by_description(
        raw_description="Bounty hunters in space with jazz music",
        client_ip="192.168.1.11",
        limit=5,
    )

    assert result["search_mode"] == "llm"
    assert result["filtered_count"] == 1
    assert len(result["results"]) == 0


@pytest.mark.asyncio
async def test_text_search_fallback_on_unconfigured_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.services.text_search_service.get_redis_client", get_fake_redis)

    mock_llm = MagicMock(spec=GeminiLLMProvider)
    mock_llm.infer_animes_from_description = AsyncMock(side_effect=LLMNotConfiguredError("No key"))

    mock_anilist = MagicMock()
    mock_anilist.search_anime_by_title = AsyncMock(return_value=[
        CanonicalAnime(
            id=1535,
            title=TitleInfo(romaji="Death Note", english="Death Note", native=None),
            cover_image="https://example.com/dn.jpg",
            synopsis="Light finds a notebook.",
            year=2006,
            format="TV",
            is_adult=False,
        )
    ])

    service = TextSearchService(llm_provider=mock_llm, anilist_provider=mock_anilist)
    result = await service.search_by_description(
        raw_description="Death Note",
        client_ip="192.168.1.12",
        limit=5,
    )

    assert result["search_mode"] == "fallback"
    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == 1535
    assert result["results"][0]["confidence_level"] == "medium"


@pytest.mark.asyncio
async def test_text_search_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fake_aioredis.FakeRedis(decode_responses=True)

    async def get_fake_redis():
        return fake_redis

    monkeypatch.setattr("src.services.text_search_service.get_redis_client", get_fake_redis)

    mock_llm = MagicMock(spec=GeminiLLMProvider)
    mock_llm.infer_animes_from_description = AsyncMock(return_value=[
        LLMCandidate(anime_title="Frieren", confidence_level="high", match_reason="Elfa maga")
    ])

    mock_anilist = MagicMock()
    mock_anilist.search_anime_by_title = AsyncMock(return_value=[
        CanonicalAnime(
            id=154587,
            title=TitleInfo(romaji="Sousou no Frieren", english="Frieren: Beyond Journey's End", native=None),
            cover_image="https://example.com/frieren.jpg",
            synopsis="An elf mage after the hero's death.",
            year=2023,
            format="TV",
            is_adult=False,
        )
    ])

    service = TextSearchService(llm_provider=mock_llm, anilist_provider=mock_anilist)

    # First search -> Miss
    res1 = await service.search_by_description("elfa maga que vive muchos anios", "192.168.1.13")
    assert res1["cached"] is False
    assert mock_llm.infer_animes_from_description.call_count == 1

    # Second search with identical text -> Hit
    res2 = await service.search_by_description("elfa maga que vive muchos anios", "192.168.1.13")
    assert res2["cached"] is True
    # The LLM should NOT have been called a second time
    assert mock_llm.infer_animes_from_description.call_count == 1


@pytest.mark.asyncio
async def test_text_search_endpoint_validation(async_client: AsyncClient) -> None:
    # 1. Description too short (< 3 chars)
    resp_short = await async_client.post("/api/v1/search/text", json={"description": "ab"})
    assert resp_short.status_code == 422

    # 2. Limit out of range (> 10)
    resp_limit = await async_client.post("/api/v1/search/text", json={"description": "Valid description", "limit": 20})
    assert resp_limit.status_code == 422


@pytest.mark.asyncio
async def test_text_search_endpoint_success(monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient) -> None:
    mock_service = MagicMock()
    mock_service.search_by_description = AsyncMock(return_value={
        "query_type": "text",
        "search_mode": "fallback",
        "cached": False,
        "filtered_count": 0,
        "processing_time_ms": 42,
        "results": [
            {
                "id": 1535,
                "title": {"romaji": "Death Note", "english": "Death Note", "native": "デスノート"},
                "cover_image": "https://example.com/dn.jpg",
                "synopsis": "Light finds a notebook.",
                "year": 2006,
                "format": "TV",
                "is_adult": False,
                "confidence_percentage": None,
                "confidence_level": "medium",
                "match_reason": "Coincidencia en AniList",
                "scene_info": None,
            }
        ],
    })

    monkeypatch.setattr("src.api.v1.endpoints.search_text.get_text_service", lambda: mock_service)

    response = await async_client.post(
        "/api/v1/search/text",
        json={"description": "anime sobre un cuaderno de la muerte", "limit": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query_type"] == "text"
    assert data["search_mode"] == "fallback"
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == 1535

